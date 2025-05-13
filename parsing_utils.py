import re
from datetime import datetime
from typing import Optional

def extract_date(text):
    patterns = [
        (r"\d{2}/\d{2}/\d{4}", "%m/%d/%Y"),
        (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
        (r"\d{2}/\d{2}/\d{2}", "%m/%d/%y"),
        (r"\b\d{1,2}/\d{1,2}/\d{2}\b", "%m/%d/%y"),
        (r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b", "%b %d, %Y"),
        (r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b", "%B %d, %Y"),
    ]


    for pattern, fmt in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return datetime.strptime(match.group(), fmt).date()
            except ValueError:
                continue
    return None

import re

def extract_total(text: str, total_pattern: Optional[str] = None) -> float:
    lines = text.splitlines()

    # Default pattern if none is provided or blank
    if not total_pattern:
        total_pattern = r"(?<!sub)\btotal\b[\s:\n]*\$?(\d+\.\d{2})\b(?!\s*purchase)"

    # Try full-text regex match first
    match = re.search(total_pattern, text, re.IGNORECASE)
    if match:
        return float(match.group(1))

    # Fallback 1: line with "total"
    for line in reversed(lines):
        if "total" in line.lower():
            match = re.search(r"\$?\s*(\d+\.\d{2})", line)
            if match:
                return float(match.group(1))

    # Fallback 2: line with "amount"
    for line in reversed(lines):
        if "amount" in line.lower():
            match = re.search(r"\$?\s*(\d+\.\d{2})", line)
            if match:
                return float(match.group(1))

    return 0.0



def extract_store_name(text):
    lines = text.strip().split("\n")
    for line in lines:
        if line.strip() and len(line.strip()) > 4:
            return line.strip()
    return "Store not found"