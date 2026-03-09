import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

from research_app.models.base import ModelResult


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.where(y_true == 0, 1.0, y_true)
    return float(np.mean(np.abs((y_true - y_pred) / denom)))


def prepare_arima_series(df: pd.DataFrame, county: str | None = None) -> pd.DataFrame:
    work = df.copy()
    if county and "区县" in work.columns:
        work = work[work["区县"].astype(str).str.strip() == county]
    work = work[work["日期"].notna() & work["当日实际人数"].notna()].copy()
    if work.empty:
        return work
    series_df = (
        work.sort_values("日期")[["日期", "当日实际人数"]]
        .rename(columns={"日期": "date", "当日实际人数": "actual"})
        .drop_duplicates(subset=["date"])
        .reset_index(drop=True)
    )
    return series_df


def train_arima(
    df: pd.DataFrame,
    county: str | None = None,
    order: tuple[int, int, int] = (1, 1, 1),
    forecast_steps: int = 7,
    holdout_size: int = 14,
) -> ModelResult:
    series_df = prepare_arima_series(df=df, county=county)
    if len(series_df) < max(30, holdout_size + 10):
        return ModelResult(
            model_name="ARIMA",
            status="insufficient_data",
            notes="Not enough valid daily rows to train ARIMA.",
        )

    train_df = series_df.iloc[:-holdout_size].copy()
    test_df = series_df.iloc[-holdout_size:].copy()

    model = ARIMA(train_df["actual"], order=order)
    fitted = model.fit()
    test_pred = fitted.forecast(steps=holdout_size)
    test_pred = np.asarray(test_pred, dtype=float)
    y_true = test_df["actual"].to_numpy(dtype=float)

    metrics = {
        "mae": float(np.mean(np.abs(y_true - test_pred))),
        "rmse": float(np.sqrt(np.mean((y_true - test_pred) ** 2))),
        "mape": _mape(y_true, test_pred),
    }

    full_model = ARIMA(series_df["actual"], order=order).fit()
    future_pred = np.asarray(full_model.forecast(steps=forecast_steps), dtype=float)
    last_date = series_df["date"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=forecast_steps, freq="D")

    history_part = test_df.copy()
    history_part["predicted"] = test_pred
    history_part["segment"] = "holdout"

    forecast_part = pd.DataFrame(
        {
            "date": future_dates,
            "actual": np.nan,
            "predicted": future_pred,
            "segment": "forecast",
        }
    )

    result_df = pd.concat([history_part, forecast_part], ignore_index=True)
    return ModelResult(
        model_name="ARIMA",
        status="trained",
        notes=f"ARIMA{order} trained on {len(train_df)} rows with {holdout_size}-day holdout.",
        metrics=metrics,
        forecast_df=result_df,
    )
