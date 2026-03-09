MODEL_REGISTRY = {
    "ARIMA": {
        "family": "time_series",
        "status": "implemented",
        "module": "research_app.models.arima_model",
    },
    "Prophet": {
        "family": "time_series",
        "status": "implemented",
        "module": "research_app.models.prophet_model",
    },
    "XGBoost": {
        "family": "tree_boosting",
        "status": "implemented",
        "module": "research_app.models.xgboost_model",
    },
    "LightGBM": {
        "family": "tree_boosting",
        "status": "prototype_exists",
        "module": "app.services.model_service",
    },
    "LSTM": {
        "family": "deep_learning",
        "status": "implemented",
        "module": "research_app.models.lstm_model",
    },
    "TFT": {
        "family": "deep_learning",
        "status": "implemented",
        "module": "research_app.models.tft_model",
    },
}
