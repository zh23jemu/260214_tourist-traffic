import json
from datetime import datetime
from pathlib import Path

import joblib
from lightgbm import LGBMRegressor
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import MODELS_DIR
from app.models import FeatureDaily, ModelRegistry

FEATURE_COLUMNS = [
    "day_of_week",
    "month",
    "is_weekend",
    "is_holiday_proxy",
    "temp_c",
    "weather_type_code",
    "lag_1",
    "lag_7",
    "lag_14",
    "rolling_mean_7",
    "rolling_std_7",
]


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.where(y_true == 0, 1.0, y_true)
    return float(np.mean(np.abs((y_true - y_pred) / denom)))


def train_model(db: Session, feature_version: str, horizon: int, county: str):
    rows = db.execute(
        select(FeatureDaily)
        .where(
            FeatureDaily.feature_version == feature_version,
            FeatureDaily.county == county,
        )
        .order_by(FeatureDaily.date.asc())
    ).scalars().all()
    if not rows:
        raise ValueError("no feature rows found for this feature_version/county")

    df = pd.DataFrame(
        [
            {
                "date": r.date,
                "actual_count": r.actual_count,
                "day_of_week": r.day_of_week,
                "month": r.month,
                "is_weekend": r.is_weekend,
                "is_holiday_proxy": r.is_holiday_proxy,
                "temp_c": r.temp_c,
                "weather_type_code": r.weather_type_code,
                "lag_1": r.lag_1,
                "lag_7": r.lag_7,
                "lag_14": r.lag_14,
                "rolling_mean_7": r.rolling_mean_7,
                "rolling_std_7": r.rolling_std_7,
            }
            for r in rows
        ]
    )
    df = df.dropna(subset=["actual_count"]).sort_values("date").reset_index(drop=True)
    if len(df) < 10:
        raise ValueError("insufficient data for training: need at least 10 valid rows")

    for col in FEATURE_COLUMNS:
        if df[col].isna().all():
            df[col] = 0.0
        else:
            df[col] = df[col].ffill().bfill().fillna(0.0)

    split_index = max(int(len(df) * 0.8), len(df) - 3)
    split_index = min(split_index, len(df) - 1)
    train_df = df.iloc[:split_index]
    val_df = df.iloc[split_index:]
    if val_df.empty:
        raise ValueError("validation split is empty")

    x_train = train_df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y_train = train_df["actual_count"].to_numpy(dtype=float)
    x_val = val_df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y_val = val_df["actual_count"].to_numpy(dtype=float)

    candidates = {
        "LightGBMRegressor": LGBMRegressor(
            n_estimators=300,
            learning_rate=0.05,
            max_depth=-1,
            num_leaves=31,
            subsample=0.9,
            colsample_bytree=0.9,
            random_state=42,
        ),
        "LinearRegression": LinearRegression(),
        "RandomForestRegressor": RandomForestRegressor(
            n_estimators=200,
            random_state=42,
            n_jobs=1,
        ),
    }

    best_name = ""
    best_model = None
    best_pred = None
    best_metrics = None
    best_mape = None
    for name, model in candidates.items():
        model.fit(x_train, y_train)
        pred = model.predict(x_val)
        metrics = {
            "mae": float(mean_absolute_error(y_val, pred)),
            "rmse": float(np.sqrt(mean_squared_error(y_val, pred))),
            "mape": _mape(y_val, pred),
        }
        if best_mape is None or metrics["mape"] < best_mape:
            best_name = name
            best_model = model
            best_pred = pred
            best_metrics = metrics
            best_mape = metrics["mape"]

    assert best_model is not None and best_pred is not None and best_metrics is not None

    # Refit on all available rows to maximize signal.
    x_all = df[FEATURE_COLUMNS].to_numpy(dtype=float)
    y_all = df["actual_count"].to_numpy(dtype=float)
    best_model.fit(x_all, y_all)

    residuals = y_val - best_pred
    q_low = float(np.quantile(residuals, 0.1))
    q_high = float(np.quantile(residuals, 0.9))

    model_version = f"{feature_version}-{county}-{horizon}d-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    model_file = Path(MODELS_DIR) / f"{model_version}.joblib"
    joblib.dump(
        {
            "model": best_model,
            "feature_columns": FEATURE_COLUMNS,
            "residual_q10": q_low,
            "residual_q90": q_high,
        },
        model_file,
    )

    registry = ModelRegistry(
        model_version=model_version,
        county=county,
        feature_version=feature_version,
        horizon=horizon,
        algorithm=best_name,
        metrics_json=json.dumps(best_metrics),
        train_start=min(df["date"]),
        train_end=max(df["date"]),
    )
    db.add(registry)
    db.commit()

    return {
        "model_version": model_version,
        "algorithm": best_name,
        "metrics": best_metrics,
        "train_start": min(df["date"]),
        "train_end": max(df["date"]),
    }
