"""Shared paths for pipeline temporary files."""

from pathlib import Path

PIPELINE_DIR = Path(__file__).resolve().parent
TEMP_DIR = PIPELINE_DIR / "temp"
TEMP_DIR.mkdir(parents=True, exist_ok=True)

EXHIBITION_DATA_FILE = TEMP_DIR / "exhibition_data.csv"
HISTORICAL_DATA_FILE = TEMP_DIR / "historical_data.csv"
CLEAN_EXHIBITION_FILE = TEMP_DIR / "clean_exhibition.csv"
CLEAN_HISTORICAL_FILE = TEMP_DIR / "clean_historical.csv"
