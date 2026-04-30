import re
from collections import Counter
from typing import List

EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")


def is_valid_email(value: str) -> bool:
    if not isinstance(value, str):
        return False
    return bool(EMAIL_RE.match(value.strip()))


def assign_statuses(emails: List[str]) -> List[str]:
    normalized = [e.strip().lower() if isinstance(e, str) else "" for e in emails]
    counts = Counter(e for e in normalized if e)
    statuses = []
    for raw, email in zip(emails, normalized):
        if not email:
            statuses.append("invalid_email")
        elif not is_valid_email(raw):
            statuses.append("invalid_email")
        elif counts[email] > 1:
            statuses.append("duplicate")
        else:
            statuses.append("ready")
    return statuses
