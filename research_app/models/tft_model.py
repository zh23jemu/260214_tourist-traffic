import warnings

import numpy as np
import pandas as pd
import torch
from lightning.pytorch import Trainer, seed_everything
from lightning.pytorch.callbacks import EarlyStopping
from lightning.pytorch.loggers import CSVLogger
from pytorch_forecasting import TemporalFusionTransformer, TimeSeriesDataSet
from pytorch_forecasting.data import GroupNormalizer, NaNLabelEncoder
from pytorch_forecasting.metrics import QuantileLoss

from research_app.config import RESEARCH_DIR
from research_app.models.base import ModelResult
from research_app.models.xgboost_model import _extract_temperature, _extract_weather_label, _resolve_day_type


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.where(y_true == 0, 1.0, y_true)
    return float(np.mean(np.abs((y_true - y_pred) / denom)))


def _build_tft_frame(df: pd.DataFrame, county: str | None = None) -> pd.DataFrame:
    work = df.copy()
    if county and "区县" in work.columns:
        work = work[work["区县"].astype(str).str.strip() == county]
    work = work[work["日期"].notna() & work["当日实际人数"].notna()].copy()
    if work.empty:
        return pd.DataFrame()

    work["date"] = pd.to_datetime(work["日期"], errors="coerce")
    work["actual"] = pd.to_numeric(work["当日实际人数"], errors="coerce")
    work = work[work["date"].notna() & work["actual"].notna()].sort_values("date").copy()
    work = work.drop_duplicates(subset=["date"]).reset_index(drop=True)

    work["weather_raw"] = work.get("当日天气", "").fillna("").astype(str).str.strip()
    work["weather_label"] = work["weather_raw"].map(_extract_weather_label)
    work["temperature_c"] = work["weather_raw"].map(_extract_temperature)
    work["temperature_c"] = work["temperature_c"].ffill().bfill()
    work["day_type"] = work.apply(
        lambda row: _resolve_day_type(pd.Timestamp(row["date"]), row),
        axis=1,
    )
    work["holiday_name"] = work.get("节假日名称", "").fillna("").astype(str).str.strip()
    work["holiday_name"] = work["holiday_name"].replace("", "无")
    work["series_id"] = county or "荔波县"
    work["time_idx"] = (work["date"] - work["date"].min()).dt.days.astype(int)
    work["day_of_week"] = work["date"].dt.weekday.astype(str)
    work["month"] = work["date"].dt.month.astype(str)
    work["day_of_month"] = work["date"].dt.day.astype(float)
    work["is_weekend"] = (work["date"].dt.weekday >= 5).astype(int)
    work["is_holiday"] = work["holiday_name"].ne("无").astype(int)
    work["is_makeup_workday"] = work["day_type"].eq("调休上班").astype(int)
    work["is_future"] = 0
    return work[
        [
            "date",
            "time_idx",
            "series_id",
            "actual",
            "weather_label",
            "temperature_c",
            "day_type",
            "holiday_name",
            "day_of_week",
            "month",
            "day_of_month",
            "is_weekend",
            "is_holiday",
            "is_makeup_workday",
            "is_future",
        ]
    ].reset_index(drop=True)


def _infer_future_rows(history_df: pd.DataFrame, forecast_steps: int) -> pd.DataFrame:
    future_rows: list[dict[str, object]] = []
    last_date = pd.Timestamp(history_df["date"].max())
    last_time_idx = int(history_df["time_idx"].max())
    last_actual = float(history_df["actual"].dropna().iloc[-1])
    fallback_temp = float(history_df["temperature_c"].dropna().iloc[-1]) if history_df["temperature_c"].notna().any() else 20.0
    series_id = str(history_df["series_id"].iloc[0])

    for step in range(1, forecast_steps + 1):
        current_date = last_date + pd.Timedelta(days=step)
        day_type = "周末" if current_date.weekday() >= 5 else "工作日"
        future_rows.append(
            {
                "date": current_date,
                "time_idx": last_time_idx + step,
                "series_id": series_id,
                "actual": last_actual,
                "weather_label": "未知",
                "temperature_c": fallback_temp,
                "day_type": day_type,
                "holiday_name": "无",
                "day_of_week": str(current_date.weekday()),
                "month": str(current_date.month),
                "day_of_month": float(current_date.day),
                "is_weekend": int(current_date.weekday() >= 5),
                "is_holiday": 0,
                "is_makeup_workday": 0,
                "is_future": 1,
            }
        )
    return pd.DataFrame(future_rows)


def train_tft(
    df: pd.DataFrame,
    county: str | None = None,
    forecast_steps: int = 7,
    holdout_size: int = 14,
    encoder_length: int = 30,
    max_epochs: int = 12,
) -> ModelResult:
    warnings.filterwarnings("ignore", category=UserWarning)
    history_df = _build_tft_frame(df=df, county=county)
    if len(history_df) < max(70, encoder_length + holdout_size + 10):
        return ModelResult(
            model_name="TFT",
            status="insufficient_data",
            notes="Not enough valid rows to train the TFT model.",
        )

    seed_everything(42, workers=True)
    device = "cpu"
    max_prediction_length = max(forecast_steps, holdout_size)
    cutoff = int(history_df["time_idx"].max()) - holdout_size
    min_encoder_length = min(14, encoder_length)
    log_dir = RESEARCH_DIR / ".artifacts"
    log_dir.mkdir(parents=True, exist_ok=True)
    train_history_df = history_df[history_df["time_idx"] <= cutoff].copy()

    training = TimeSeriesDataSet(
        train_history_df,
        time_idx="time_idx",
        target="actual",
        group_ids=["series_id"],
        min_encoder_length=min_encoder_length,
        max_encoder_length=encoder_length,
        min_prediction_length=1,
        max_prediction_length=max_prediction_length,
        static_categoricals=["series_id"],
        time_varying_known_categoricals=["day_of_week", "month", "day_type", "holiday_name", "weather_label"],
        time_varying_known_reals=["time_idx", "temperature_c", "day_of_month", "is_weekend", "is_holiday", "is_makeup_workday"],
        time_varying_unknown_reals=["actual"],
        target_normalizer=GroupNormalizer(groups=["series_id"]),
        categorical_encoders={
            "series_id": NaNLabelEncoder(add_nan=True),
            "day_of_week": NaNLabelEncoder(add_nan=True),
            "month": NaNLabelEncoder(add_nan=True),
            "day_type": NaNLabelEncoder(add_nan=True),
            "holiday_name": NaNLabelEncoder(add_nan=True),
            "weather_label": NaNLabelEncoder(add_nan=True),
        },
        add_relative_time_idx=True,
        add_target_scales=True,
        add_encoder_length=True,
        allow_missing_timesteps=True,
    )

    validation = TimeSeriesDataSet.from_dataset(
        training,
        history_df.copy(),
        predict=True,
        stop_randomization=True,
    )

    train_loader = training.to_dataloader(train=True, batch_size=32, num_workers=0)
    val_loader = validation.to_dataloader(train=False, batch_size=64, num_workers=0)

    tft = TemporalFusionTransformer.from_dataset(
        training,
        learning_rate=0.03,
        hidden_size=16,
        attention_head_size=2,
        dropout=0.1,
        hidden_continuous_size=8,
        loss=QuantileLoss(),
        log_interval=-1,
        optimizer="Adam",
        reduce_on_plateau_patience=2,
    )

    trainer = Trainer(
        max_epochs=max_epochs,
        accelerator=device,
        devices=1,
        logger=CSVLogger(str(log_dir), name="tft_logs"),
        enable_checkpointing=False,
        enable_model_summary=False,
        enable_progress_bar=False,
        gradient_clip_val=0.1,
        callbacks=[EarlyStopping(monitor="val_loss", patience=3, min_delta=1e-4, mode="min")],
    )
    trainer.fit(tft, train_dataloaders=train_loader, val_dataloaders=val_loader)

    raw_predictions = tft.predict(val_loader)
    prediction_values = raw_predictions.detach().cpu().numpy().reshape(-1)
    holdout_frame = history_df[history_df["time_idx"] > cutoff].head(holdout_size).copy()
    holdout_actual = holdout_frame["actual"].to_numpy(dtype=float)
    holdout_dates = holdout_frame["date"].reset_index(drop=True)
    prediction_values = prediction_values[: len(holdout_actual)]

    metrics = {
        "mae": float(np.mean(np.abs(holdout_actual - prediction_values))),
        "rmse": float(np.sqrt(np.mean((holdout_actual - prediction_values) ** 2))),
        "mape": _mape(holdout_actual, prediction_values),
    }

    predict_df = pd.concat([history_df, _infer_future_rows(history_df, max_prediction_length)], ignore_index=True)
    prediction_dataset = TimeSeriesDataSet.from_dataset(
        training,
        predict_df,
        predict=True,
        stop_randomization=True,
    )
    prediction_loader = prediction_dataset.to_dataloader(train=False, batch_size=64, num_workers=0)
    future_predictions = tft.predict(prediction_loader).detach().cpu().numpy().reshape(-1)
    future_dates = predict_df[predict_df["is_future"] == 1]["date"].reset_index(drop=True).head(forecast_steps)
    future_predictions = future_predictions[: len(future_dates)]

    holdout_df = pd.DataFrame(
        {
            "date": holdout_dates,
            "actual": holdout_actual,
            "predicted": prediction_values[: len(holdout_actual)],
            "segment": "holdout",
        }
    )
    forecast_df = pd.DataFrame(
        {
            "date": future_dates,
            "actual": np.nan,
            "predicted": future_predictions[: len(future_dates)],
            "segment": "forecast",
        }
    )
    result_df = pd.concat([holdout_df, forecast_df], ignore_index=True)

    return ModelResult(
        model_name="TFT",
        status="trained",
        notes=(
            f"TFT trained on {len(training)} training windows "
            f"from {len(train_history_df)} history rows with encoder={encoder_length} "
            f"and {len(holdout_actual)}-day holdout."
        ),
        metrics=metrics,
        forecast_df=result_df,
    )
