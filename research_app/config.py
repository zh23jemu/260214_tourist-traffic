from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESEARCH_DIR = BASE_DIR / "research_app"
ARTIFACTS_DIR = DATA_DIR / "research_artifacts"
DEFAULT_DATASET_CSV = BASE_DIR / "毕设数据统计.csv"
DEFAULT_DATASET_XLSX = BASE_DIR / "毕设数据统计.xlsx"
