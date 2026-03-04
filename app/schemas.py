from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class ImportResponse(BaseModel):
    batch_id: int
    total_rows: int
    success_rows: int
    error_rows: int
    errors: list[str]


class DataPreviewItem(BaseModel):
    date: date
    province: str
    county: str
    actual_count: int
    predicted_count_raw: int | None
    weather_type: str | None
    temp_c: float | None
    weekday_text: str | None
    day_type: str | None
    quality_flag: str


class FeatureBuildRequest(BaseModel):
    start_date: date
    end_date: date
    county: str = Field(default="荔波县")
    feature_version: str = Field(default="v1")


class FeatureBuildResponse(BaseModel):
    feature_version: str
    county: str
    rows_generated: int


class TrainRequest(BaseModel):
    feature_version: str = Field(default="v1")
    horizon: Literal[7, 30] = 7
    county: str = Field(default="荔波县")


class TrainResponse(BaseModel):
    model_version: str
    algorithm: str
    metrics: dict[str, float]
    train_start: date
    train_end: date


class PredictRequest(BaseModel):
    model_version: str
    horizon: Literal[7, 30] = 7
    start_date: date


class PredictResponse(BaseModel):
    model_version: str
    horizon: int
    inserted_rows: int
    start_date: date


class PredictionItem(BaseModel):
    date: date
    county: str
    horizon: int
    model_version: str
    y_pred: float
    y_low: float
    y_high: float


class CorrelationItem(BaseModel):
    feature: str
    correlation: float
