import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CleanFlowDaily


def correlation_with_actual(db: Session, county: str | None = None):
    stmt = select(CleanFlowDaily)
    if county:
        stmt = stmt.where(CleanFlowDaily.county == county)
    rows = db.execute(stmt).scalars().all()
    if not rows:
        return []

    df = pd.DataFrame(
        [
            {
                "actual_count": r.actual_count,
                "predicted_count_raw": r.predicted_count_raw,
                "temp_c": r.temp_c,
                "prediction_bias_raw": r.prediction_bias_raw,
            }
            for r in rows
        ]
    )
    numeric_df = df.apply(pd.to_numeric, errors="coerce")
    corr = numeric_df.corr(numeric_only=True)["actual_count"].dropna()
    corr = corr.drop(labels=["actual_count"], errors="ignore")
    result = [
        {"feature": name, "correlation": float(value)}
        for name, value in corr.sort_values(ascending=False).items()
    ]
    return result

