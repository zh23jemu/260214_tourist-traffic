from dataclasses import dataclass

import numpy as np
import pandas as pd
import shap
from xgboost import XGBRegressor

from research_app.models.xgboost_model import prepare_xgboost_training_data


@dataclass
class ShapAnalysisResult:
    status: str
    notes: str
    summary_df: pd.DataFrame | None = None
    detail_df: pd.DataFrame | None = None
    sample_date: pd.Timestamp | None = None


def explainability_status() -> str:
    return "SHAP explainability is enabled for the XGBoost research model."


def build_xgboost_shap_analysis(
    df: pd.DataFrame,
    county: str | None = None,
    holdout_size: int = 14,
    max_background_rows: int = 120,
) -> ShapAnalysisResult:
    model_df, train_df, feature_cols = prepare_xgboost_training_data(
        df=df,
        county=county,
        holdout_size=holdout_size,
    )
    if model_df.empty or train_df.empty or not feature_cols:
        return ShapAnalysisResult(
            status="insufficient_data",
            notes="Not enough rows to compute SHAP values for XGBoost.",
        )

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
    model.fit(train_df[feature_cols], train_df["actual"])

    sample_size = min(len(train_df), max_background_rows)
    sample_df = train_df.tail(sample_size).copy()
    explainer = shap.TreeExplainer(model)
    shap_values = explainer.shap_values(sample_df[feature_cols])
    shap_matrix = np.asarray(shap_values, dtype=float)

    mean_abs = np.mean(np.abs(shap_matrix), axis=0)
    summary_df = pd.DataFrame(
        {
            "feature": feature_cols,
            "mean_abs_shap": mean_abs,
            "feature_mean": sample_df[feature_cols].mean().to_numpy(dtype=float),
        }
    ).sort_values("mean_abs_shap", ascending=False)

    sample_idx = len(sample_df) - 1
    sample_shap = shap_matrix[sample_idx]
    sample_values = sample_df.iloc[sample_idx][feature_cols].to_numpy(dtype=float)
    detail_df = pd.DataFrame(
        {
            "feature": feature_cols,
            "feature_value": sample_values,
            "shap_value": sample_shap,
            "abs_shap_value": np.abs(sample_shap),
        }
    ).sort_values("abs_shap_value", ascending=False)

    return ShapAnalysisResult(
        status="ready",
        notes=f"SHAP computed on {len(sample_df)} XGBoost training rows.",
        summary_df=summary_df.reset_index(drop=True),
        detail_df=detail_df.reset_index(drop=True),
        sample_date=pd.Timestamp(sample_df.iloc[sample_idx]["date"]),
    )
