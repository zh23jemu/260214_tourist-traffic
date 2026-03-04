from dataclasses import dataclass

import pandas as pd
from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import CleanFlowDaily, ImportBatch, RawFlowDaily
from app.services.normalization import parse_excel_date, parse_number, parse_prediction_time, parse_weather

REQUIRED_COLUMNS = [
    "日期",
    "省份",
    "区县",
    "当日预测人数",
    "当日实际人数",
    "当日天气",
    "日期属性",
    "日期属性编码",
    "预测生成时间",
    "预测偏差值",
]


@dataclass
class ImportResult:
    batch_id: int
    total_rows: int
    success_rows: int
    error_rows: int
    errors: list[str]


def import_excel_to_db(db: Session, file_path: str, filename: str) -> ImportResult:
    df = pd.read_excel(file_path, sheet_name=0)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    batch = ImportBatch(filename=filename, status="processing")
    db.add(batch)
    db.flush()

    errors: list[str] = []
    if missing:
        msg = f"missing required columns: {', '.join(missing)}"
        batch.status = "failed"
        batch.error_summary = msg
        db.commit()
        raise ValueError(msg)

    total_rows = len(df)
    success_rows = 0
    error_rows = 0

    for idx, row in df.iterrows():
        row_num = idx + 2
        raw = RawFlowDaily(
            batch_id=batch.id,
            row_number=row_num,
            raw_date=str(row.get("日期", "")),
            raw_province=str(row.get("省份", "")),
            raw_county=str(row.get("区县", "")),
            raw_predicted_count=str(row.get("当日预测人数", "")),
            raw_actual_count=str(row.get("当日实际人数", "")),
            raw_weather=str(row.get("当日天气", "")),
            raw_weekday=str(row.get("日期属性", "")),
            raw_day_type=str(row.get("日期属性编码", "")),
            raw_prediction_time=str(row.get("预测生成时间", "")),
            raw_bias=str(row.get("预测偏差值", "")),
            error_message=None,
        )

        date_value = parse_excel_date(row.get("日期"))
        actual_count = parse_number(row.get("当日实际人数"))
        predicted_count = parse_number(row.get("当日预测人数"))
        if date_value is None:
            error_rows += 1
            msg = f"row {row_num}: invalid date"
            raw.error_message = msg
            errors.append(msg)
            db.add(raw)
            continue
        quality_flag = "ok"
        if actual_count is None and predicted_count is not None:
            actual_count = predicted_count
            quality_flag = "actual_imputed_from_predicted"
        if actual_count is None or actual_count < 0:
            error_rows += 1
            msg = f"row {row_num}: invalid actual count"
            raw.error_message = msg
            errors.append(msg)
            db.add(raw)
            continue

        weather_type, temp_c, weather_flag = parse_weather(row.get("当日天气"))
        prediction_bias = parse_number(row.get("预测偏差值"))
        generated_time = parse_prediction_time(row.get("预测生成时间"))

        county = str(row.get("区县", "")).strip() or "未知区县"
        province = str(row.get("省份", "")).strip() or "未知省份"
        weekday = str(row.get("日期属性", "")).strip() or None
        day_type = str(row.get("日期属性编码", "")).strip() or None

        db.execute(
            delete(CleanFlowDaily).where(
                CleanFlowDaily.date == date_value,
                CleanFlowDaily.county == county,
            )
        )
        clean = CleanFlowDaily(
            date=date_value,
            province=province,
            county=county,
            predicted_count_raw=int(predicted_count) if predicted_count is not None else None,
            actual_count=int(actual_count),
            weather_text=None if pd.isna(row.get("当日天气")) else str(row.get("当日天气")),
            weather_type=weather_type,
            temp_c=temp_c,
            weekday_text=weekday,
            day_type=day_type,
            prediction_generated_time=generated_time,
            prediction_bias_raw=prediction_bias,
            quality_flag=weather_flag if weather_flag != "ok" else quality_flag,
            source_batch_id=batch.id,
        )
        db.add(clean)
        db.add(raw)
        success_rows += 1

    batch.total_rows = total_rows
    batch.success_rows = success_rows
    batch.error_rows = error_rows
    if error_rows == total_rows:
        batch.status = "failed"
    elif error_rows > 0:
        batch.status = "partial_success"
    else:
        batch.status = "success"
    batch.error_summary = "; ".join(errors[:20]) if errors else None
    db.commit()

    return ImportResult(
        batch_id=batch.id,
        total_rows=total_rows,
        success_rows=success_rows,
        error_rows=error_rows,
        errors=errors[:50],
    )
