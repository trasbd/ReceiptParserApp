import re
from parsing_utils import extract_date

def parse_generic_store(text, store_name, total_pattern=r"Total\s*\$?(\d+\.\d{2})"):
    total = re.search(total_pattern, text)
    return {
        "store": store_name,
        "date": extract_date(text),
        "total": total.group(1) if total else "Total not found",
    }

def parse_walmart(text):
    return parse_generic_store(text, "Walmart")

def parse_schnucks(text):
    return parse_generic_store(text, "Schnucks")



STORE_PARSERS = {
    "walmart": parse_walmart,
    "schnucks": parse_schnucks,
}
