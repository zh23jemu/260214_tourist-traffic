import pandas as pd


def build_overview_metrics(df: pd.DataFrame) -> dict[str, str | int]:
    valid = df[df["日期"].notna()].copy() if "日期" in df.columns else df.copy()
    valid_actual = valid[valid["当日实际人数"].notna()].copy() if "当日实际人数" in valid.columns else valid

    date_range = "-"
    if not valid.empty and "日期" in valid.columns:
        start = valid["日期"].min()
        end = valid["日期"].max()
        if pd.notna(start) and pd.notna(end):
            date_range = f"{start.date()} ~ {end.date()}"

    holiday_type_count = 0
    if "节假日名称" in valid.columns:
        holiday_type_count = int(valid["节假日名称"].replace("", pd.NA).dropna().nunique())

    return {
        "valid_dates": int(valid["日期"].dropna().nunique()) if "日期" in valid.columns else 0,
        "valid_actual_rows": int(len(valid_actual)),
        "date_range": date_range,
        "holiday_type_count": holiday_type_count,
    }


def build_day_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    if "日期类型" not in df.columns or "当日实际人数" not in df.columns:
        return pd.DataFrame()
    valid = df[df["当日实际人数"].notna()].copy()
    if valid.empty:
        return pd.DataFrame()
    summary = (
        valid.groupby("日期类型")["当日实际人数"]
        .agg(["count", "mean", "median", "min", "max", "std"])
        .reset_index()
    )
    return summary.round(2)


def build_holiday_summary(df: pd.DataFrame) -> pd.DataFrame:
    if "节假日名称展示" not in df.columns or "当日实际人数" not in df.columns:
        return pd.DataFrame()
    valid = df[(df["当日实际人数"].notna()) & (df["节假日名称展示"] != "无")].copy()
    if valid.empty:
        return pd.DataFrame()
    summary = (
        valid.groupby(["日期类型", "节假日名称展示"])["当日实际人数"]
        .agg(["count", "mean", "median", "min", "max"])
        .reset_index()
    )
    return summary.round(2)
