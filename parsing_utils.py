import re
from datetime import datetime

def extract_date(text):
    patterns = [
        (r"\d{2}/\d{2}/\d{4}", "%m/%d/%Y"),
        (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),
        (r"\d{2}/\d{2}/\d{2}", "%m/%d/%y"),
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

def extract_total(text):
    lines = text.splitlines()
    for line in reversed(lines):
        if "total" in line.lower():
            match = re.search(r"\d+\.\d{2}", line)
            if match:
                return match.group()
    return "Total not found"

def extract_store_name(text):
    lines = text.strip().split("\n")
    for line in lines:
        if line.strip() and len(line.strip()) > 4:
            return line.strip()
    return "Store not found"