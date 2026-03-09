from dataclasses import dataclass, field

import pandas as pd


@dataclass
class ModelResult:
    model_name: str
    status: str
    notes: str
    metrics: dict[str, float] = field(default_factory=dict)
    forecast_df: pd.DataFrame | None = None
