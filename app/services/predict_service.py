from datetime import timedelta
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.config import MODELS_DIR
from app.models import CleanFlowDaily, ModelRegistry, PredictionDaily


def _holiday_proxy(day_type: str | None) -> int:
    if not day_type:
        return 0
    value = day_type.strip()
    keywords = ["节", "假", "周末", "休"]
    return 1 if any(k in value for k in keywords) and "工作" not in value else 0


def run_prediction(db: Session, model_version: str, horizon: int, start_date):
    model_rec = db.execute(
        select(ModelRegistry).where(ModelRegistry.model_version == model_version)
    ).scalar_one_or_none()
    if model_rec is None:
        raise ValueError("model_version not found")
    if horizon != model_rec.horizon:
        raise ValueError("horizon mismatch with model")

    model_path = Path(MODELS_DIR) / f"{model_version}.joblib"
    if not model_path.exists():
        raise ValueError("model artifact file missing")
    bundle = joblib.load(model_path)
    model = bundle["model"]
    feature_columns = bundle["feature_columns"]
    residual_q10 = float(bundle["residual_q10"])
    residual_q90 = float(bundle["residual_q90"])

    history_rows = db.execute(
        select(CleanFlowDaily)
        .where(
            CleanFlowDaily.county == model_rec.county,
            CleanFlowDaily.date < start_date,
        )
        .order_by(CleanFlowDaily.date.asc())
    ).scalars().all()
    if len(history_rows) < 1:
        raise ValueError("insufficient history rows before start_date")

    history_df = pd.DataFrame(
        [
            {
                "date": r.date,
                "actual_count": float(r.actual_count),
                "temp_c": r.temp_c,
                "weather_type": r.weather_type or "UNKNOWN",
                "day_type": r.day_type,
            }
            for r in history_rows
        ]
    )
    history_df = history_df.sort_values("date").reset_index(drop=True)
    history_values = history_df["actual_count"].tolist()

    temp_default = (
        float(history_df["temp_c"].dropna().tail(30).mean())
        if not history_df["temp_c"].dropna().empty
        else 20.0
    )
    weather_mode = (
        history_df["weather_type"].dropna().tail(30).mode().iloc[0]
        if not history_df["weather_type"].dropna().empty
        else "UNKNOWN"
    )
    weather_categories = sorted(history_df["weather_type"].fillna("UNKNOWN").unique().tolist() + [weather_mode])
    weather_map = {k: i for i, k in enumerate(weather_categories)}
    weather_code_default = weather_map.get(weather_mode, 0)

    inserted = 0
    for i in range(horizon):
        target_date = start_date + timedelta(days=i)
        day_of_week = target_date.weekday()
        is_weekend = int(day_of_week >= 5)
        month = target_date.month
        is_holiday = 0
        lag_1 = history_values[-1] if len(history_values) >= 1 else None
        lag_7 = history_values[-7] if len(history_values) >= 7 else lag_1
        lag_14 = history_values[-14] if len(history_values) >= 14 else lag_7
        rolling_window = history_values[-7:] if len(history_values) >= 7 else history_values
        rolling_mean_7 = float(np.mean(rolling_window)) if rolling_window else None
        rolling_std_7 = float(np.std(rolling_window)) if rolling_window else None
        if None in [lag_1, lag_7, lag_14, rolling_mean_7, rolling_std_7]:
            raise ValueError("not enough history to build prediction features")

        feature_row = {
            "day_of_week": day_of_week,
            "month": month,
            "is_weekend": is_weekend,
            "is_holiday_proxy": is_holiday,
            "temp_c": temp_default,
            "weather_type_code": weather_code_default,
            "lag_1": float(lag_1),
            "lag_7": float(lag_7),
            "lag_14": float(lag_14),
            "rolling_mean_7": float(rolling_mean_7),
            "rolling_std_7": float(rolling_std_7),
        }
        x = np.array([[feature_row[col] for col in feature_columns]], dtype=float)
        y_pred = float(model.predict(x)[0])
        y_low = float(y_pred + residual_q10)
        y_high = float(y_pred + residual_q90)

        db.execute(
            delete(PredictionDaily).where(
                PredictionDaily.date == target_date,
                PredictionDaily.county == model_rec.county,
                PredictionDaily.horizon == horizon,
                PredictionDaily.model_version == model_version,
            )
        )
        db.add(
            PredictionDaily(
                date=target_date,
                county=model_rec.county,
                horizon=horizon,
                model_version=model_version,
                y_pred=y_pred,
                y_low=y_low,
                y_high=y_high,
            )
        )
        history_values.append(y_pred)
        inserted += 1

    db.commit()
    return inserted
