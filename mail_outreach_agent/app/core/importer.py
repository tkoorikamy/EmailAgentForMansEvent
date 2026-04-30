from pathlib import Path
import pandas as pd

REQUIRED_COLUMNS = ["company", "email"]
OPTIONAL_COLUMNS = ["contact_name", "category", "city", "comment", "website", "ai_comment"]


def load_recipients(file_path: str) -> pd.DataFrame:
    path = Path(file_path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() in {".xlsx", ".xlsm"}:
        df = pd.read_excel(path, engine="openpyxl")
    else:
        raise ValueError("Поддерживаются только CSV/XLSX")

    df.columns = [str(c).strip().lower() for c in df.columns]
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(f"Отсутствует обязательная колонка: {col}")
    for col in OPTIONAL_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    return df[REQUIRED_COLUMNS + OPTIONAL_COLUMNS].fillna("")
