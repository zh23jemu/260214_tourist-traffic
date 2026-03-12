import re
from datetime import date, datetime

import pandas as pd

WEATHER_RE = re.compile(r"^\s*([^,，]+)\s*[,，]\s*(-?\d+(?:\.\d+)?)\s*℃\s*$")


def parse_excel_date(value) -> date | None:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, (int, float)):
        if value > 30000:
            parsed = pd.to_datetime(value, unit="D", origin="1899-12-30", errors="coerce")
            return None if pd.isna(parsed) else parsed.date()
    parsed = pd.to_datetime(str(value), errors="coerce")
    return None if pd.isna(parsed) else parsed.date()


def parse_number(value) -> float | None:
    if pd.isna(value):
        return None
    parsed = pd.to_numeric(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return float(parsed)


def parse_weather(value: str | None) -> tuple[str | None, float | None, str]:
    if not value:
        return None, None, "weather_missing"
    m = WEATHER_RE.match(str(value))
    if not m:
        return str(value), None, "weather_parse_failed"
    weather_type = m.group(1).strip()
    temp = float(m.group(2))
    return weather_type, temp, "ok"


def parse_prediction_time(value) -> datetime | None:
    if pd.isna(value):
        return None
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.to_pydatetime()

