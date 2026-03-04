from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ImportBatch(Base):
    __tablename__ = "import_batch"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="processing")
    total_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_rows: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    raw_rows: Mapped[list["RawFlowDaily"]] = relationship(back_populates="batch")


class RawFlowDaily(Base):
    __tablename__ = "raw_flow_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batch.id"), nullable=False, index=True)
    row_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_date: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_province: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_county: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_predicted_count: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_actual_count: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_weather: Mapped[str | None] = mapped_column(String(128), nullable=True)
    raw_weekday: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_day_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_prediction_time: Mapped[str | None] = mapped_column(String(64), nullable=True)
    raw_bias: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    batch: Mapped[ImportBatch] = relationship(back_populates="raw_rows")


class CleanFlowDaily(Base):
    __tablename__ = "clean_flow_daily"
    __table_args__ = (UniqueConstraint("date", "county", name="uq_clean_date_county"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    province: Mapped[str] = mapped_column(String(64), nullable=False)
    county: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    predicted_count_raw: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_count: Mapped[int] = mapped_column(Integer, nullable=False)
    weather_text: Mapped[str | None] = mapped_column(String(128), nullable=True)
    weather_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    weekday_text: Mapped[str | None] = mapped_column(String(64), nullable=True)
    day_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    prediction_generated_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    prediction_bias_raw: Mapped[float | None] = mapped_column(Float, nullable=True)
    quality_flag: Mapped[str] = mapped_column(String(32), nullable=False, default="ok")
    source_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batch.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )


class FeatureDaily(Base):
    __tablename__ = "feature_daily"
    __table_args__ = (UniqueConstraint("date", "county", "feature_version", name="uq_feature_key"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    county: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    feature_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    actual_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    is_weekend: Mapped[int] = mapped_column(Integer, nullable=False)
    is_holiday_proxy: Mapped[int] = mapped_column(Integer, nullable=False)
    temp_c: Mapped[float] = mapped_column(Float, nullable=False)
    weather_type_code: Mapped[int] = mapped_column(Integer, nullable=False)
    lag_1: Mapped[float | None] = mapped_column(Float, nullable=True)
    lag_7: Mapped[float | None] = mapped_column(Float, nullable=True)
    lag_14: Mapped[float | None] = mapped_column(Float, nullable=True)
    rolling_mean_7: Mapped[float | None] = mapped_column(Float, nullable=True)
    rolling_std_7: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    model_version: Mapped[str] = mapped_column(String(64), primary_key=True)
    county: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    feature_version: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    horizon: Mapped[int] = mapped_column(Integer, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False)
    metrics_json: Mapped[str] = mapped_column(Text, nullable=False)
    train_start: Mapped[date] = mapped_column(Date, nullable=False)
    train_end: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class PredictionDaily(Base):
    __tablename__ = "prediction_daily"
    __table_args__ = (
        UniqueConstraint("date", "county", "horizon", "model_version", name="uq_prediction_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    county: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    horizon: Mapped[int] = mapped_column(Integer, nullable=False)
    model_version: Mapped[str] = mapped_column(ForeignKey("model_registry.model_version"), nullable=False, index=True)
    y_pred: Mapped[float] = mapped_column(Float, nullable=False)
    y_low: Mapped[float] = mapped_column(Float, nullable=False)
    y_high: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

