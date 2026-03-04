import numpy as np
import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import CleanFlowDaily, FeatureDaily


def _holiday_proxy(day_type: str | None) -> int:
    if not day_type:
        return 0
    value = day_type.strip()
    keywords = ["节", "假", "周末", "休"]
    return 1 if any(k in value for k in keywords) and "工作" not in value else 0


def build_features(
    db: Session,
    start_date,
    end_date,
    county: str,
    feature_version: str,
) -> int:
    rows = db.execute(
        select(CleanFlowDaily)
        .where(
            CleanFlowDaily.county == county,
            CleanFlowDaily.date >= start_date,
            CleanFlowDaily.date <= end_date,
        )
        .order_by(CleanFlowDaily.date.asc())
    ).scalars().all()

    if not rows:
        return 0

    df = pd.DataFrame(
        [
            {
                "date": r.date,
                "county": r.county,
                "actual_count": r.actual_count,
                "temp_c": r.temp_c,
                "day_type": r.day_type,
                "weather_type": r.weather_type or "UNKNOWN",
            }
            for r in rows
        ]
    )
    df = df.sort_values("date").reset_index(drop=True)
    df["date"] = pd.to_datetime(df["date"])
    df["day_of_week"] = df["date"].dt.dayofweek
    df["month"] = df["date"].dt.month
    df["is_weekend"] = (df["day_of_week"] >= 5).astype(int)
    df["is_holiday_proxy"] = df["day_type"].apply(_holiday_proxy).astype(int)
    temp_default = float(df["temp_c"].dropna().mean()) if not df["temp_c"].dropna().empty else 20.0
    df["temp_c"] = df["temp_c"].fillna(temp_default)

    weather_categories = sorted(df["weather_type"].fillna("UNKNOWN").unique().tolist())
    weather_map = {k: i for i, k in enumerate(weather_categories)}
    df["weather_type_code"] = df["weather_type"].map(weather_map).fillna(-1).astype(int)

    df["lag_1"] = df["actual_count"].shift(1)
    df["lag_7"] = df["actual_count"].shift(7)
    df["lag_14"] = df["actual_count"].shift(14)
    shifted = df["actual_count"].shift(1)
    df["rolling_mean_7"] = shifted.rolling(7, min_periods=1).mean()
    df["rolling_std_7"] = shifted.rolling(7, min_periods=1).std(ddof=0)
    df = df.replace({np.nan: None})

    db.execute(
        delete(FeatureDaily).where(
            FeatureDaily.feature_version == feature_version,
            FeatureDaily.county == county,
            FeatureDaily.date >= start_date,
            FeatureDaily.date <= end_date,
        )
    )
    for _, r in df.iterrows():
        db.add(
            FeatureDaily(
                date=r["date"].date(),
                county=county,
                feature_version=feature_version,
                actual_count=int(r["actual_count"]) if r["actual_count"] is not None else None,
                day_of_week=int(r["day_of_week"]),
                month=int(r["month"]),
                is_weekend=int(r["is_weekend"]),
                is_holiday_proxy=int(r["is_holiday_proxy"]),
                temp_c=float(r["temp_c"]),
                weather_type_code=int(r["weather_type_code"]),
                lag_1=float(r["lag_1"]) if r["lag_1"] is not None else None,
                lag_7=float(r["lag_7"]) if r["lag_7"] is not None else None,
                lag_14=float(r["lag_14"]) if r["lag_14"] is not None else None,
                rolling_mean_7=float(r["rolling_mean_7"]) if r["rolling_mean_7"] is not None else None,
                rolling_std_7=float(r["rolling_std_7"]) if r["rolling_std_7"] is not None else None,
            )
        )
    db.commit()
    return len(df)
