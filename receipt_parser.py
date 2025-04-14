from pdf2image import convert_from_path
import os
import cv2
import pytesseract
import re

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_image(image_path):
    text = ""
    if image_path.lower().endswith(".pdf"):
        images = convert_from_path(image_path, first_page=1, last_page=1)
        for img in images:
            text += pytesseract.image_to_string(img)
    else:
        img = cv2.imread(image_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
    return text


def parse_walmart(text):
    date = re.search(r'\d{2}/\d{2}/\d{4}', text)
    total = re.search(r'TOTAL\s*\$?(\d+\.\d{2})', text)
    return {
        'store': 'Walmart',
        'date': date.group() if date else 'Date not found',
        'total': total.group(1) if total else 'Total not found'
    }

def parse_target(text):
    date = re.search(r'\d{2}/\d{2}/\d{4}', text)
    total = re.search(r'Total:\s*\$?(\d+\.\d{2})', text)
    return {
        'store': 'Target',
        'date': date.group() if date else 'Date not found',
        'total': total.group(1) if total else 'Total not found'
    }

STORE_PARSERS = {
    'walmart': parse_walmart,
    'target': parse_target
}

def extract_store_name(text):
    lines = text.strip().split('\n')
    for line in lines:
        if line.strip() and len(line.strip()) > 4:
            return line.strip()
    return "Store not found"

def extract_date(text):
    patterns = [r'\d{2}/\d{2}/\d{4}', r'\d{4}-\d{2}-\d{2}']
    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group()
    return "Date not found"

def extract_total(text):
    lines = text.splitlines()
    for line in reversed(lines):
        if "total" in line.lower():
            match = re.search(r'\d+\.\d{2}', line)
            if match:
                return match.group()
    return "Total not found"

def parse_receipt(image_path):
    text = extract_text_from_image(image_path)
    lower = text.lower()
    for key, func in STORE_PARSERS.items():
        if key in lower:
            return func(text)
    return {
        "store": extract_store_name(text),
        "date": extract_date(text),
        "total": extract_total(text)
    }
