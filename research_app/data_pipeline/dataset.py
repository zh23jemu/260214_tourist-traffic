import pandas as pd

from research_app.config import DEFAULT_DATASET_CSV, DEFAULT_DATASET_XLSX


def load_source_dataset() -> pd.DataFrame:
    if DEFAULT_DATASET_CSV.exists():
        df = pd.read_csv(DEFAULT_DATASET_CSV)
    elif DEFAULT_DATASET_XLSX.exists():
        df = pd.read_excel(DEFAULT_DATASET_XLSX, sheet_name=0)
    else:
        raise FileNotFoundError("No source dataset found for research_app")

    if "日期" in df.columns:
        df["日期"] = pd.to_datetime(df["日期"], errors="coerce")
    if "当日实际人数" in df.columns:
        df["当日实际人数"] = pd.to_numeric(df["当日实际人数"], errors="coerce")
    if "日期属性编码" in df.columns:
        df["日期属性编码"] = df["日期属性编码"].astype(str).str.strip()
    if "节假日名称" in df.columns:
        df["节假日名称"] = df["节假日名称"].astype(str).replace({"nan": ""}).str.strip()
    return df


def prepare_dashboard_dataset(df: pd.DataFrame) -> pd.DataFrame:
    prepared = df.copy()
    if "日期" in prepared.columns:
        prepared["日期"] = pd.to_datetime(prepared["日期"], errors="coerce")
    if "当日实际人数" in prepared.columns:
        prepared["当日实际人数"] = pd.to_numeric(prepared["当日实际人数"], errors="coerce")
    if "当日预测人数" in prepared.columns:
        prepared["当日预测人数"] = pd.to_numeric(prepared["当日预测人数"], errors="coerce")
    if "日期属性编码" in prepared.columns:
        prepared["日期属性编码"] = prepared["日期属性编码"].fillna("").astype(str).str.strip()
    if "节假日名称" in prepared.columns:
        prepared["节假日名称"] = prepared["节假日名称"].fillna("").astype(str).str.strip()
    if "当日天气" in prepared.columns:
        prepared["当日天气"] = prepared["当日天气"].fillna("").astype(str).str.strip()

    prepared["日期类型"] = prepared.get("日期属性编码", "")
    prepared["节假日名称展示"] = prepared.get("节假日名称", "").replace("", "无")
    prepared["月份"] = prepared["日期"].dt.month if "日期" in prepared.columns else pd.NA
    prepared["年份"] = prepared["日期"].dt.year if "日期" in prepared.columns else pd.NA
    return prepared


def filter_dashboard_dataset(
    df: pd.DataFrame,
    county: str | None = None,
    day_types: list[str] | None = None,
    start_date=None,
    end_date=None,
) -> pd.DataFrame:
    filtered = df.copy()
    if county and "区县" in filtered.columns:
        filtered = filtered[filtered["区县"].astype(str).str.strip() == county]
    if day_types and "日期类型" in filtered.columns:
        filtered = filtered[filtered["日期类型"].isin(day_types)]
    if start_date is not None and "日期" in filtered.columns:
        filtered = filtered[filtered["日期"] >= pd.Timestamp(start_date)]
    if end_date is not None and "日期" in filtered.columns:
        filtered = filtered[filtered["日期"] <= pd.Timestamp(end_date)]
    return filtered
