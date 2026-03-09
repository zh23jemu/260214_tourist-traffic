import random

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import MinMaxScaler
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from research_app.models.base import ModelResult
from research_app.models.arima_model import prepare_arima_series


class LSTMRegressor(nn.Module):
    def __init__(self, input_size: int = 1, hidden_size: int = 32) -> None:
        super().__init__()
        self.lstm = nn.LSTM(input_size=input_size, hidden_size=hidden_size, batch_first=True)
        self.linear = nn.Linear(hidden_size, 1)

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        outputs, _ = self.lstm(inputs)
        last_hidden = outputs[:, -1, :]
        return self.linear(last_hidden)


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    denom = np.where(y_true == 0, 1.0, y_true)
    return float(np.mean(np.abs((y_true - y_pred) / denom)))


def _set_reproducible_seed(seed: int = 42) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _build_sequences(values: np.ndarray, window_size: int) -> tuple[np.ndarray, np.ndarray]:
    features = []
    labels = []
    for idx in range(window_size, len(values)):
        features.append(values[idx - window_size : idx])
        labels.append(values[idx])
    if not features:
        return np.empty((0, window_size, 1), dtype=np.float32), np.empty((0, 1), dtype=np.float32)
    x_array = np.asarray(features, dtype=np.float32).reshape(-1, window_size, 1)
    y_array = np.asarray(labels, dtype=np.float32).reshape(-1, 1)
    return x_array, y_array


def train_lstm(
    df: pd.DataFrame,
    county: str | None = None,
    forecast_steps: int = 7,
    holdout_size: int = 14,
    window_size: int = 14,
    epochs: int = 180,
    batch_size: int = 16,
    learning_rate: float = 0.01,
) -> ModelResult:
    series_df = prepare_arima_series(df=df, county=county)
    if len(series_df) < max(50, holdout_size + window_size + 10):
        return ModelResult(
            model_name="LSTM",
            status="insufficient_data",
            notes="Not enough valid rows to train the LSTM model.",
        )

    _set_reproducible_seed(42)
    series_values = series_df["actual"].to_numpy(dtype=np.float32).reshape(-1, 1)
    scaler = MinMaxScaler()
    scaled_values = scaler.fit_transform(series_values).astype(np.float32).reshape(-1)

    train_values = scaled_values[:-holdout_size]
    full_x, full_y = _build_sequences(scaled_values, window_size)
    train_x, train_y = _build_sequences(train_values, window_size)
    if len(train_x) == 0 or len(full_x) == 0:
        return ModelResult(
            model_name="LSTM",
            status="insufficient_data",
            notes="Sequence construction failed because the time series is too short.",
        )

    device = torch.device("cpu")
    model = LSTMRegressor().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    loss_fn = nn.MSELoss()

    dataset = TensorDataset(torch.from_numpy(train_x), torch.from_numpy(train_y))
    loader = DataLoader(dataset, batch_size=min(batch_size, len(dataset)), shuffle=False)

    model.train()
    for _ in range(epochs):
        for batch_x, batch_y in loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            optimizer.zero_grad()
            preds = model(batch_x)
            loss = loss_fn(preds, batch_y)
            loss.backward()
            optimizer.step()

    holdout_x = full_x[-holdout_size:]
    holdout_dates = series_df["date"].iloc[-holdout_size:].reset_index(drop=True)
    holdout_actual = series_df["actual"].iloc[-holdout_size:].to_numpy(dtype=float)

    model.eval()
    with torch.no_grad():
        holdout_pred_scaled = model(torch.from_numpy(holdout_x).to(device)).cpu().numpy()
    holdout_pred = scaler.inverse_transform(holdout_pred_scaled).reshape(-1)

    metrics = {
        "mae": float(np.mean(np.abs(holdout_actual - holdout_pred))),
        "rmse": float(np.sqrt(np.mean((holdout_actual - holdout_pred) ** 2))),
        "mape": _mape(holdout_actual, holdout_pred),
    }

    full_model = LSTMRegressor().to(device)
    full_optimizer = torch.optim.Adam(full_model.parameters(), lr=learning_rate)
    full_dataset = TensorDataset(torch.from_numpy(full_x), torch.from_numpy(full_y))
    full_loader = DataLoader(full_dataset, batch_size=min(batch_size, len(full_dataset)), shuffle=False)

    full_model.train()
    for _ in range(epochs):
        for batch_x, batch_y in full_loader:
            batch_x = batch_x.to(device)
            batch_y = batch_y.to(device)
            full_optimizer.zero_grad()
            preds = full_model(batch_x)
            loss = loss_fn(preds, batch_y)
            loss.backward()
            full_optimizer.step()

    history_scaled = scaled_values.tolist()
    future_predictions = []
    last_date = pd.Timestamp(series_df["date"].max())

    full_model.eval()
    for step in range(1, forecast_steps + 1):
        window_values = np.asarray(history_scaled[-window_size:], dtype=np.float32).reshape(1, window_size, 1)
        with torch.no_grad():
            next_scaled = full_model(torch.from_numpy(window_values).to(device)).cpu().numpy().reshape(-1)[0]
        history_scaled.append(float(next_scaled))
        next_value = float(scaler.inverse_transform(np.array([[next_scaled]], dtype=np.float32))[0, 0])
        future_predictions.append(
            {
                "date": last_date + pd.Timedelta(days=step),
                "actual": np.nan,
                "predicted": next_value,
                "segment": "forecast",
            }
        )

    holdout_df = pd.DataFrame(
        {
            "date": holdout_dates,
            "actual": holdout_actual,
            "predicted": holdout_pred,
            "segment": "holdout",
        }
    )
    result_df = pd.concat([holdout_df, pd.DataFrame(future_predictions)], ignore_index=True)

    return ModelResult(
        model_name="LSTM",
        status="trained",
        notes=f"LSTM trained on {len(train_x)} sequences with window={window_size} and {holdout_size}-row holdout.",
        metrics=metrics,
        forecast_df=result_df,
    )
