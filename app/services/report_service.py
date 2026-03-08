import csv
from io import BytesIO, StringIO

import matplotlib
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import CleanFlowDaily, PredictionDaily

matplotlib.use("Agg")
from matplotlib import pyplot as plt


def build_csv_report(db: Session, county: str | None = None, model_version: str | None = None) -> str:
    clean_stmt = select(CleanFlowDaily).order_by(CleanFlowDaily.date.asc())
    if county:
        clean_stmt = clean_stmt.where(CleanFlowDaily.county == county)
    clean_rows = db.execute(clean_stmt).scalars().all()

    pred_map: dict[tuple, PredictionDaily] = {}
    if model_version:
        pred_stmt = (
            select(PredictionDaily)
            .where(PredictionDaily.model_version == model_version)
            .order_by(PredictionDaily.date.asc())
        )
        if county:
            pred_stmt = pred_stmt.where(PredictionDaily.county == county)
        pred_rows = db.execute(pred_stmt).scalars().all()
        pred_map = {(row.date, row.county): row for row in pred_rows}

    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "date",
            "county",
            "actual_count",
            "predicted_count_raw",
            "quality_flag",
            "model_version",
            "y_pred",
            "y_low",
            "y_high",
        ]
    )
    for row in clean_rows:
        pred = pred_map.get((row.date, row.county))
        writer.writerow(
            [
                row.date.isoformat(),
                row.county,
                row.actual_count,
                row.predicted_count_raw,
                row.quality_flag,
                pred.model_version if pred else "",
                pred.y_pred if pred else "",
                pred.y_low if pred else "",
                pred.y_high if pred else "",
            ]
        )
    return buffer.getvalue()


def build_png_report(db: Session, county: str | None = None, model_version: str | None = None) -> bytes:
    clean_stmt = select(CleanFlowDaily).order_by(CleanFlowDaily.date.asc())
    if county:
        clean_stmt = clean_stmt.where(CleanFlowDaily.county == county)
    clean_rows = db.execute(clean_stmt).scalars().all()
    if not clean_rows:
        raise ValueError("no clean flow data available for report")

    df = pd.DataFrame(
        [{"date": row.date, "actual_count": row.actual_count, "county": row.county} for row in clean_rows]
    )

    plt.figure(figsize=(12, 5))
    plt.plot(df["date"], df["actual_count"], label="actual_count", linewidth=2)

    if model_version:
        pred_stmt = (
            select(PredictionDaily)
            .where(PredictionDaily.model_version == model_version)
            .order_by(PredictionDaily.date.asc())
        )
        if county:
            pred_stmt = pred_stmt.where(PredictionDaily.county == county)
        pred_rows = db.execute(pred_stmt).scalars().all()
        if pred_rows:
            pred_df = pd.DataFrame([{"date": row.date, "y_pred": row.y_pred} for row in pred_rows])
            plt.plot(pred_df["date"], pred_df["y_pred"], label="prediction", linestyle="--")

    title = "Tourist Traffic Report"
    if county:
        title = f"{title} - {county}"
    plt.title(title)
    plt.xlabel("Date")
    plt.ylabel("Visitor Count")
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png", dpi=160)
    plt.close()
    return buffer.getvalue()
