import re
from typing import Optional
from parsing_utils import extract_date, extract_total

def parse_generic_store(text: str, store_name: str, total_pattern: Optional[str] = None) -> dict:
    return {
        "store": store_name,
        "date": extract_date(text),
        "total": extract_total(text, total_pattern),
    }


def parse_walmart(text):
    return parse_generic_store(text, "Walmart")

def parse_amazon(text):
    return parse_generic_store(text=text, store_name="Amazon.com")

def parse_schnucks(text):
    return parse_generic_store(text, "Schnucks")

def parse_mcdonalds(text):
    total = re.search(r"Cashless\s*(\d+\.\d{2})", text)
    return {
        "store": "McDonald's",
        "date": extract_date(text),
        "total": total.group(1) if total else 0
    }


def parse_tacobell(text):
    # Use regex that anchors to a line starting with TOTAL
    match = re.search(r"(?i)^TOTAL\s*\n?\s*\$?(\d+\.\d{2})", text, re.MULTILINE)
    match_val = match.group(1) if match else "0.00"

    return {
        "store": "Taco Bell",
        "date": extract_date(text),
        "total": match_val
    }

def parse_on_the_run(text):
    totals = re.findall(r"\$\s?(\d+\.\d{2})", text)
    total = totals[-1] if totals else "0.00"

    return {
        "store": "Mobil",
        "date": extract_date(text),
        "total": total
    }


STORE_PARSERS = [
    (lambda t: "walmart" in t.lower(), parse_walmart),
    (lambda t: "schnucks" in t.lower(), parse_schnucks),
    (lambda t: "mcdonald" in t.lower(), parse_mcdonalds),
    (lambda t: "mild sauce packet" in t.lower(), parse_tacobell),
    (lambda t: re.search(r"\bON\s*[-.\s]*THE\s*[-.\s]*RUN\b", t, re.IGNORECASE), parse_on_the_run),
    (lambda t: "Amazon.com".lower() in t.lower(), parse_amazon),
]
