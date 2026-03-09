import re

import numpy as np
import pandas as pd
from xgboost import XGBRegressor

from research_app.models.base import ModelResult
from research_app.models.arima_model import prepare_arima_series


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.where(y_true == 0, 1.0, y_true)
    return float(np.mean(np.abs((y_true - y_pred) / denom)))


def _extract_weather_label(raw_weather: str) -> str:
    if not raw_weather:
        return "未知"
    return str(raw_weather).split("，", 1)[0].strip() or "未知"


def _extract_temperature(raw_weather: str) -> float:
    if not raw_weather:
        return np.nan
    match = re.search(r"(-?\d+(?:\.\d+)?)\s*℃", str(raw_weather))
    return float(match.group(1)) if match else np.nan


def _resolve_day_type(date_value: pd.Timestamp, source_row: pd.Series | None) -> str:
    if source_row is not None and "日期属性编码" in source_row and pd.notna(source_row["日期属性编码"]):
        day_type = str(source_row["日期属性编码"]).strip()
        if day_type and day_type.lower() != "nan":
            return day_type
    if date_value.weekday() >= 5:
        return "周末"
    return "工作日"


def _prepare_calendar_lookup(df: pd.DataFrame, county: str | None = None) -> dict[pd.Timestamp, dict[str, object]]:
    work = df.copy()
    if county and "区县" in work.columns:
        work = work[work["区县"].astype(str).str.strip() == county]
    if "日期" not in work.columns:
        return {}

    calendar_rows: dict[pd.Timestamp, dict[str, object]] = {}
    for _, row in work.sort_values("日期").iterrows():
        date_value = pd.Timestamp(row["日期"]).normalize()
        calendar_rows[date_value] = {
            "weather_raw": str(row.get("当日天气", "")).strip(),
            "weather_label": _extract_weather_label(row.get("当日天气", "")),
            "temperature_c": _extract_temperature(row.get("当日天气", "")),
            "day_type": str(row.get("日期属性编码", "")).strip(),
            "holiday_name": str(row.get("节假日名称", "")).strip(),
        }
    return calendar_rows


def _build_feature_frame(df: pd.DataFrame, county: str | None = None) -> pd.DataFrame:
    base_df = prepare_arima_series(df=df, county=county).copy()
    if base_df.empty:
        return pd.DataFrame()

    calendar_lookup = _prepare_calendar_lookup(df=df, county=county)
    base_df["date"] = pd.to_datetime(base_df["date"], errors="coerce")
    base_df["day_of_week"] = base_df["date"].dt.weekday
    base_df["day_of_month"] = base_df["date"].dt.day
    base_df["month"] = base_df["date"].dt.month
    base_df["is_weekend"] = (base_df["day_of_week"] >= 5).astype(int)

    base_df["day_type"] = base_df["date"].apply(
        lambda value: _resolve_day_type(value, pd.Series(calendar_lookup.get(pd.Timestamp(value).normalize(), {})))
    )
    base_df["holiday_name"] = base_df["date"].apply(
        lambda value: str(calendar_lookup.get(pd.Timestamp(value).normalize(), {}).get("holiday_name", "")).strip()
    )
    base_df["is_holiday"] = base_df["holiday_name"].ne("").astype(int)
    base_df["is_makeup_workday"] = base_df["day_type"].eq("调休上班").astype(int)
    base_df["weather_label"] = base_df["date"].apply(
        lambda value: str(calendar_lookup.get(pd.Timestamp(value).normalize(), {}).get("weather_label", "未知")).strip()
        or "未知"
    )
    base_df["temperature_c"] = base_df["date"].apply(
        lambda value: calendar_lookup.get(pd.Timestamp(value).normalize(), {}).get("temperature_c", np.nan)
    )
    base_df["temperature_c"] = base_df["temperature_c"].ffill().bfill()

    base_df["lag_1"] = base_df["actual"].shift(1)
    base_df["lag_7"] = base_df["actual"].shift(7)
    base_df["lag_14"] = base_df["actual"].shift(14)
    base_df["rolling_mean_7"] = base_df["actual"].shift(1).rolling(window=7, min_periods=3).mean()
    base_df["rolling_std_7"] = (
        base_df["actual"].shift(1).rolling(window=7, min_periods=3).std().fillna(0.0)
    )

    model_df = pd.get_dummies(
        base_df,
        columns=["weather_label", "day_type", "holiday_name"],
        prefix=["weather", "day_type", "holiday"],
        prefix_sep="=",
        dtype=float,
    )
    model_df = model_df.dropna(subset=["lag_1", "lag_7", "lag_14", "rolling_mean_7"])
    return model_df.reset_index(drop=True)


def prepare_xgboost_training_data(
    df: pd.DataFrame,
    county: str | None = None,
    holdout_size: int = 14,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    model_df = _build_feature_frame(df=df, county=county)
    if model_df.empty:
        return model_df, model_df, []

    target_col = "actual"
    date_col = "date"
    feature_cols = [col for col in model_df.columns if col not in {target_col, date_col}]
    train_df = model_df.iloc[:-holdout_size].copy() if len(model_df) > holdout_size else model_df.iloc[0:0].copy()
    return model_df, train_df, feature_cols


def _build_future_feature_row(
    current_date: pd.Timestamp,
    history_values: list[float],
    calendar_lookup: dict[pd.Timestamp, dict[str, object]],
    fallback_temp: float,
) -> dict[str, object]:
    lookup_row = calendar_lookup.get(current_date.normalize())
    day_type = _resolve_day_type(current_date, pd.Series(lookup_row or {}))
    holiday_name = ""
    weather_label = "未知"
    temperature_c = fallback_temp
    if lookup_row:
        holiday_name = str(lookup_row.get("holiday_name", "")).strip()
        weather_label = str(lookup_row.get("weather_label", "未知")).strip() or "未知"
        lookup_temp = lookup_row.get("temperature_c", np.nan)
        if pd.notna(lookup_temp):
            temperature_c = float(lookup_temp)

    lag_1 = history_values[-1]
    lag_7 = history_values[-7] if len(history_values) >= 7 else history_values[0]
    lag_14 = history_values[-14] if len(history_values) >= 14 else history_values[0]
    recent_window = history_values[-7:] if len(history_values) >= 7 else history_values

    return {
        "date": current_date,
        "day_of_week": current_date.weekday(),
        "day_of_month": current_date.day,
        "month": current_date.month,
        "is_weekend": int(current_date.weekday() >= 5),
        "is_holiday": int(bool(holiday_name)),
        "is_makeup_workday": int(day_type == "调休上班"),
        "temperature_c": float(temperature_c),
        "lag_1": float(lag_1),
        "lag_7": float(lag_7),
        "lag_14": float(lag_14),
        "rolling_mean_7": float(np.mean(recent_window)),
        "rolling_std_7": float(np.std(recent_window, ddof=0)) if len(recent_window) > 1 else 0.0,
        "weather_label": weather_label,
        "day_type": day_type,
        "holiday_name": holiday_name,
    }


def train_xgboost(
    df: pd.DataFrame,
    county: str | None = None,
    forecast_steps: int = 7,
    holdout_size: int = 14,
) -> ModelResult:
    model_df, train_df, feature_cols = prepare_xgboost_training_data(
        df=df,
        county=county,
        holdout_size=holdout_size,
    )
    if len(model_df) < max(40, holdout_size + 10):
        return ModelResult(
            model_name="XGBoost",
            status="insufficient_data",
            notes="Not enough valid rows to train XGBoost with lag features.",
        )

    target_col = "actual"
    date_col = "date"
    test_df = model_df.iloc[-holdout_size:].copy()

    model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=1,
    )
    model.fit(train_df[feature_cols], train_df[target_col])

    holdout_pred = model.predict(test_df[feature_cols]).astype(float)
    y_true = test_df[target_col].to_numpy(dtype=float)
    metrics = {
        "mae": float(np.mean(np.abs(y_true - holdout_pred))),
        "rmse": float(np.sqrt(np.mean((y_true - holdout_pred) ** 2))),
        "mape": _mape(y_true, holdout_pred),
    }

    full_model = XGBRegressor(
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        objective="reg:squarederror",
        random_state=42,
        n_jobs=1,
    )
    full_model.fit(model_df[feature_cols], model_df[target_col])

    calendar_lookup = _prepare_calendar_lookup(df=df, county=county)
    history_values = prepare_arima_series(df=df, county=county)["actual"].astype(float).tolist()
    last_date = pd.Timestamp(prepare_arima_series(df=df, county=county)["date"].max())
    fallback_temp = float(model_df["temperature_c"].dropna().iloc[-1]) if model_df["temperature_c"].notna().any() else 20.0

    future_rows = []
    for step in range(1, forecast_steps + 1):
        current_date = last_date + pd.Timedelta(days=step)
        future_row = _build_future_feature_row(
            current_date=current_date,
            history_values=history_values,
            calendar_lookup=calendar_lookup,
            fallback_temp=fallback_temp,
        )
        future_frame = pd.DataFrame([future_row])
        future_frame = pd.get_dummies(
            future_frame,
            columns=["weather_label", "day_type", "holiday_name"],
            prefix=["weather", "day_type", "holiday"],
            prefix_sep="=",
            dtype=float,
        )
        future_frame = future_frame.reindex(columns=[date_col] + feature_cols, fill_value=0.0)
        predicted_value = float(full_model.predict(future_frame[feature_cols])[0])
        history_values.append(predicted_value)
        future_rows.append(
            {
                "date": current_date,
                "actual": np.nan,
                "predicted": predicted_value,
                "segment": "forecast",
            }
        )

    holdout_part = test_df[[date_col, target_col]].copy()
    holdout_part["predicted"] = holdout_pred
    holdout_part["segment"] = "holdout"
    holdout_part = holdout_part.rename(columns={date_col: "date", target_col: "actual"})

    result_df = pd.concat([holdout_part, pd.DataFrame(future_rows)], ignore_index=True)

    return ModelResult(
        model_name="XGBoost",
        status="trained",
        notes=f"XGBoost trained on {len(train_df)} rows with {holdout_size}-row holdout.",
        metrics=metrics,
        forecast_df=result_df,
    )
