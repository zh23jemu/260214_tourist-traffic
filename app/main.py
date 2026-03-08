import os
import tempfile
from datetime import date
from io import BytesIO
from json import loads

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import Base, SessionLocal, engine, get_db
from app.models import CleanFlowDaily, FeatureDaily, ModelRegistry, PredictionDaily
from app.schemas import (
    CorrelationItem,
    DataPreviewItem,
    DashboardOverviewResponse,
    DashboardPredictionPoint,
    DashboardSeriesPoint,
    FeatureBuildRequest,
    FeatureBuildResponse,
    ImportResponse,
    LoginRequest,
    LoginResponse,
    PredictRequest,
    PredictResponse,
    PredictionItem,
    TrainRequest,
    TrainResponse,
)
from app.services.analysis_service import correlation_with_actual
from app.services.auth_service import authenticate_user, create_access_token, ensure_default_admin, get_current_user
from app.services.feature_service import build_features
from app.services.import_service import import_excel_to_db
from app.services.model_service import train_model
from app.services.predict_service import run_prediction
from app.services.report_service import build_csv_report, build_png_report

app = FastAPI(title="Tourist Traffic API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:3000",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        ensure_default_admin(db)
    finally:
        db.close()


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/v1/auth/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db=db, username=req.username, password=req.password)
    if user is None:
        raise HTTPException(status_code=401, detail="invalid username or password")
    token, expires_in = create_access_token(user)
    return LoginResponse(access_token=token, expires_in=expires_in)


@app.post("/api/v1/data/import/excel", response_model=ImportResponse)
async def import_excel(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
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
            quality_flag_counts=result.quality_flag_counts,
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
def build_feature_snapshot(
    req: FeatureBuildRequest,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
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
def train(
    req: TrainRequest,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
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
def predict(
    req: PredictRequest,
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
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


@app.get("/api/v1/dashboard/overview", response_model=DashboardOverviewResponse)
def dashboard_overview(
    county: str | None = Query(default=None),
    model_version: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    clean_stmt = select(CleanFlowDaily)
    if county:
        clean_stmt = clean_stmt.where(CleanFlowDaily.county == county)
    clean_rows = db.execute(clean_stmt.order_by(CleanFlowDaily.date.asc())).scalars().all()

    feature_count_stmt = select(func.count()).select_from(FeatureDaily)
    if county:
        feature_count_stmt = feature_count_stmt.where(FeatureDaily.county == county)
    feature_row_count = db.execute(feature_count_stmt).scalar_one()

    prediction_count_stmt = select(func.count()).select_from(PredictionDaily)
    if county:
        prediction_count_stmt = prediction_count_stmt.where(PredictionDaily.county == county)
    if model_version:
        prediction_count_stmt = prediction_count_stmt.where(PredictionDaily.model_version == model_version)
    prediction_row_count = db.execute(prediction_count_stmt).scalar_one()

    county_stmt = select(func.count(func.distinct(CleanFlowDaily.county))).select_from(CleanFlowDaily)
    county_count = db.execute(county_stmt).scalar_one()

    latest_model_stmt = select(ModelRegistry).order_by(ModelRegistry.created_at.desc())
    if county:
        latest_model_stmt = latest_model_stmt.where(ModelRegistry.county == county)
    if model_version:
        latest_model_stmt = latest_model_stmt.where(ModelRegistry.model_version == model_version)
    latest_model = db.execute(latest_model_stmt).scalars().first()

    recent_actual_series = [
        DashboardSeriesPoint(date=row.date, actual_count=float(row.actual_count))
        for row in clean_rows[-30:]
    ]

    pred_stmt = select(PredictionDaily).order_by(PredictionDaily.date.asc())
    if county:
        pred_stmt = pred_stmt.where(PredictionDaily.county == county)
    if model_version:
        pred_stmt = pred_stmt.where(PredictionDaily.model_version == model_version)
    elif latest_model is not None:
        pred_stmt = pred_stmt.where(PredictionDaily.model_version == latest_model.model_version)
    recent_prediction_rows = db.execute(pred_stmt).scalars().all()
    recent_prediction_series = [
        DashboardPredictionPoint(date=row.date, y_pred=row.y_pred, y_low=row.y_low, y_high=row.y_high)
        for row in recent_prediction_rows[-30:]
    ]

    latest_model_payload = None
    if latest_model is not None:
        latest_model_payload = {
            "model_version": latest_model.model_version,
            "county": latest_model.county,
            "feature_version": latest_model.feature_version,
            "horizon": latest_model.horizon,
            "algorithm": latest_model.algorithm,
            "metrics": loads(latest_model.metrics_json),
            "train_start": latest_model.train_start,
            "train_end": latest_model.train_end,
            "created_at": latest_model.created_at,
        }

    return DashboardOverviewResponse(
        county_count=county_count,
        clean_row_count=len(clean_rows),
        feature_row_count=feature_row_count,
        prediction_row_count=prediction_row_count,
        date_range={
            "start": clean_rows[0].date if clean_rows else None,
            "end": clean_rows[-1].date if clean_rows else None,
        },
        latest_model=latest_model_payload,
        recent_actual_series=recent_actual_series,
        recent_prediction_series=recent_prediction_series,
    )


@app.get("/api/v1/export/report")
def export_report(
    format: str = Query(pattern="^(csv|png)$"),
    county: str | None = Query(default=None),
    model_version: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    if format == "csv":
        csv_content = build_csv_report(db=db, county=county, model_version=model_version)
        filename = "tourist_traffic_report.csv"
        return StreamingResponse(
            iter([csv_content.encode("utf-8-sig")]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    try:
        png_content = build_png_report(db=db, county=county, model_version=model_version)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    filename = "tourist_traffic_report.png"
    return StreamingResponse(
        BytesIO(png_content),
        media_type="image/png",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
