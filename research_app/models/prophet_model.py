import os
from pathlib import Path

import numpy as np
import pandas as pd
from cmdstanpy import set_cmdstan_path
from cmdstanpy.utils.cmdstan import validate_cmdstan_path
from prophet import Prophet
from prophet.models import CmdStanPyBackend

from research_app.models.base import ModelResult
from research_app.models.arima_model import prepare_arima_series


def _configure_cmdstan_backend() -> None:
    default_backend_init = getattr(CmdStanPyBackend, "__patched_init__", None)
    if default_backend_init:
        return

    original_init = CmdStanPyBackend.__init__

    def patched_init(self):
        package_cmdstan = (
            Path(__file__).resolve().parents[2]
            / "venv312"
            / "Lib"
            / "site-packages"
            / "prophet"
            / "stan_model"
            / f"cmdstan-{self.CMDSTAN_VERSION}"
        )
        global_cmdstan = Path.home() / ".cmdstan" / "cmdstan-2.38.0"
        package_tbb = package_cmdstan / "stan" / "lib" / "stan_math" / "lib" / "tbb"

        if package_tbb.exists():
            os.environ["PATH"] = f"{package_tbb}{os.pathsep}{os.environ.get('PATH', '')}"

        for candidate in (package_cmdstan, global_cmdstan):
            try:
                validate_cmdstan_path(str(candidate))
                set_cmdstan_path(str(candidate))
                break
            except Exception:
                continue

        super(CmdStanPyBackend, self).__init__()

    CmdStanPyBackend.__patched_init__ = original_init
    CmdStanPyBackend.__init__ = patched_init


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.where(y_true == 0, 1.0, y_true)
    return float(np.mean(np.abs((y_true - y_pred) / denom)))


def train_prophet(
    df: pd.DataFrame,
    county: str | None = None,
    forecast_steps: int = 7,
    holdout_size: int = 14,
) -> ModelResult:
    series_df = prepare_arima_series(df=df, county=county)
    if len(series_df) < max(30, holdout_size + 10):
        return ModelResult(
            model_name="Prophet",
            status="insufficient_data",
            notes="Not enough valid daily rows to train Prophet.",
        )

    prophet_df = series_df.rename(columns={"date": "ds", "actual": "y"})
    train_df = prophet_df.iloc[:-holdout_size].copy()
    test_df = prophet_df.iloc[-holdout_size:].copy()

    try:
        _configure_cmdstan_backend()
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            daily_seasonality=False,
            stan_backend="CMDSTANPY",
        )
    except Exception as exc:
        return ModelResult(
            model_name="Prophet",
            status="environment_error",
            notes=f"Prophet backend is unavailable: {exc}",
        )
    model.fit(train_df)

    pred_test = model.predict(test_df[["ds"]])[["ds", "yhat"]]
    merged_test = test_df.merge(pred_test, on="ds", how="left")
    valid_test = merged_test.dropna(subset=["y", "yhat"]).copy()
    y_true = valid_test["y"].to_numpy(dtype=float)
    y_pred = valid_test["yhat"].to_numpy(dtype=float)

    metrics = {
        "mae": float(np.mean(np.abs(y_true - y_pred))),
        "rmse": float(np.sqrt(np.mean((y_true - y_pred) ** 2))),
        "mape": _mape(y_true, y_pred),
    }

    full_model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
        stan_backend="CMDSTANPY",
    )
    full_model.fit(prophet_df)
    future_forecast = full_model.make_future_dataframe(periods=forecast_steps, freq="D", include_history=False)
    forecast_df = full_model.predict(future_forecast)[["ds", "yhat"]]

    holdout_part = valid_test.rename(columns={"ds": "date", "y": "actual", "yhat": "predicted"})
    holdout_part["segment"] = "holdout"

    future_part = forecast_df.rename(columns={"ds": "date", "yhat": "predicted"})
    future_part["actual"] = np.nan
    future_part["segment"] = "forecast"

    result_df = pd.concat(
        [
            holdout_part[["date", "actual", "predicted", "segment"]],
            future_part[["date", "actual", "predicted", "segment"]],
        ],
        ignore_index=True,
    )

    return ModelResult(
        model_name="Prophet",
        status="trained",
        notes=f"Prophet trained on {len(train_df)} rows with {holdout_size}-day holdout.",
        metrics=metrics,
        forecast_df=result_df,
    )
