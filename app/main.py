import os
import tempfile
from datetime import date
from json import loads

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.models import CleanFlowDaily, ModelRegistry, PredictionDaily
from app.schemas import (
    CorrelationItem,
    DataPreviewItem,
    FeatureBuildRequest,
    FeatureBuildResponse,
    ImportResponse,
    PredictRequest,
    PredictResponse,
    PredictionItem,
    TrainRequest,
    TrainResponse,
)
from app.services.analysis_service import correlation_with_actual
from app.services.feature_service import build_features
from app.services.import_service import import_excel_to_db
from app.services.model_service import train_model
from app.services.predict_service import run_prediction

app = FastAPI(title="Tourist Traffic API", version="0.1.0")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/v1/data/import/excel", response_model=ImportResponse)
async def import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="only .xlsx is supported")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp_path = tmp.name
            content = await file.read()
            tmp.write(content)
        result = import_excel_to_db(db=db, file_path=tmp_path, filename=file.filename)
        return ImportResponse(
            batch_id=result.batch_id,
            total_rows=result.total_rows,
            success_rows=result.success_rows,
            error_rows=result.error_rows,
            errors=result.errors,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/api/v1/data/preview", response_model=list[DataPreviewItem])
def preview_data(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    county: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(CleanFlowDaily).order_by(CleanFlowDaily.date.asc())
    if start_date:
        stmt = stmt.where(CleanFlowDaily.date >= start_date)
    if end_date:
        stmt = stmt.where(CleanFlowDaily.date <= end_date)
    if county:
        stmt = stmt.where(CleanFlowDaily.county == county)

    rows = db.execute(stmt).scalars().all()
    return [
        DataPreviewItem(
            date=r.date,
            province=r.province,
            county=r.county,
            actual_count=r.actual_count,
            predicted_count_raw=r.predicted_count_raw,
            weather_type=r.weather_type,
            temp_c=r.temp_c,
            weekday_text=r.weekday_text,
            day_type=r.day_type,
            quality_flag=r.quality_flag,
        )
        for r in rows
    ]


@app.post("/api/v1/features/build", response_model=FeatureBuildResponse)
def build_feature_snapshot(req: FeatureBuildRequest, db: Session = Depends(get_db)):
    rows = build_features(
        db=db,
        start_date=req.start_date,
        end_date=req.end_date,
        county=req.county,
        feature_version=req.feature_version,
    )
    if rows == 0:
        raise HTTPException(status_code=404, detail="no rows found in the specified range")
    return FeatureBuildResponse(
        feature_version=req.feature_version,
        county=req.county,
        rows_generated=rows,
    )


@app.post("/api/v1/models/train", response_model=TrainResponse)
def train(req: TrainRequest, db: Session = Depends(get_db)):
    try:
        result = train_model(
            db=db,
            feature_version=req.feature_version,
            horizon=req.horizon,
            county=req.county,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return TrainResponse(
        model_version=result["model_version"],
        algorithm=result["algorithm"],
        metrics=result["metrics"],
        train_start=result["train_start"],
        train_end=result["train_end"],
    )


@app.get("/api/v1/models/metrics")
def list_model_metrics(
    county: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(ModelRegistry).order_by(ModelRegistry.created_at.desc())
    if county:
        stmt = stmt.where(ModelRegistry.county == county)
    rows = db.execute(stmt).scalars().all()
    return [
        {
            "model_version": r.model_version,
            "county": r.county,
            "feature_version": r.feature_version,
            "horizon": r.horizon,
            "algorithm": r.algorithm,
            "metrics": loads(r.metrics_json),
            "train_start": r.train_start,
            "train_end": r.train_end,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@app.post("/api/v1/models/predict", response_model=PredictResponse)
def predict(req: PredictRequest, db: Session = Depends(get_db)):
    try:
        inserted = run_prediction(
            db=db,
            model_version=req.model_version,
            horizon=req.horizon,
            start_date=req.start_date,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return PredictResponse(
        model_version=req.model_version,
        horizon=req.horizon,
        inserted_rows=inserted,
        start_date=req.start_date,
    )


@app.get("/api/v1/predictions", response_model=list[PredictionItem])
def list_predictions(
    model_version: str,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    county: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(PredictionDaily).where(PredictionDaily.model_version == model_version)
    if start_date:
        stmt = stmt.where(PredictionDaily.date >= start_date)
    if end_date:
        stmt = stmt.where(PredictionDaily.date <= end_date)
    if county:
        stmt = stmt.where(PredictionDaily.county == county)
    stmt = stmt.order_by(PredictionDaily.date.asc())
    rows = db.execute(stmt).scalars().all()
    return [
        PredictionItem(
            date=r.date,
            county=r.county,
            horizon=r.horizon,
            model_version=r.model_version,
            y_pred=r.y_pred,
            y_low=r.y_low,
            y_high=r.y_high,
        )
        for r in rows
    ]


@app.get("/api/v1/analysis/correlation", response_model=list[CorrelationItem])
def correlation(
    county: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    rows = correlation_with_actual(db=db, county=county)
    return [CorrelationItem(feature=r["feature"], correlation=r["correlation"]) for r in rows]
