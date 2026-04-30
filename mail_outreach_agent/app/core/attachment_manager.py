from pathlib import Path

ALLOWED_EXT = {".pdf", ".docx", ".xlsx"}


def attachment_info(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError("Файл вложения не найден")
    if p.suffix.lower() not in ALLOWED_EXT:
        raise ValueError("Допустимы только PDF/DOCX/XLSX")
    return {"name": p.name, "path": str(p), "size": p.stat().st_size}
