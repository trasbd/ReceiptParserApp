from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import os
import cv2
import pytesseract
import re
import fitz  # PyMuPDF


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def pdf_has_text(filepath):
    with fitz.open(filepath) as pdf:
        for page in pdf:
            if page.get_text().strip():
                return True
    return False


def extract_text_from_pdf(filepath):
    text = ""
    with fitz.open(filepath) as pdf:
        for page in pdf:
            text += page.get_text()
    return text


def extract_text_from_file(filepath):
    text = ""
    filename = os.path.basename(filepath)

    if filepath.lower().endswith(".pdf"):

        # Convert all pages of the PDF into images
        images = convert_from_path(filepath)  # all pages

        # Get total width and total height (stacked)
        width = max(img.width for img in images)
        total_height = sum(img.height for img in images)

        # Create a blank image to paste into
        combined = Image.new("RGB", (width, total_height), color=(255, 255, 255))

        # Paste each page image one below the other
        y_offset = 0
        for img in images:
            combined.paste(img, (0, y_offset))
            y_offset += img.height

        # Save the final combined image
        if combined:
            image = combined
            image_filename = filename.replace(".pdf", ".jpg")
            save_path = os.path.join("static/uploads", image_filename)
            image.save(save_path, "JPEG")

            filename = image_filename

            if pdf_has_text(filepath):
                text = extract_text_from_pdf(filepath)

            else:
                text = pytesseract.image_to_string(image)

    else:
        img = cv2.imread(filepath)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        text = pytesseract.image_to_string(gray)
    return text, filename


def parse_walmart(text):
    total = re.search(r"Total\s*\$?(\d+\.\d{2})", text)
    return {
        "store": "Walmart",
        "date": extract_date(text),
        "total": total.group(1) if total else "Total not found",
    }

def parse_schnucks(text):
    total = re.search(r"Total\s*\$?(\d+\.\d{2})", text)
    return {
        "store": "Schnucks",
        "date": extract_date(text),
        "total": total.group(1) if total else "Total not found",
    }


STORE_PARSERS = {"walmart": parse_walmart, "schnucks":parse_schnucks }


def extract_store_name(text):
    lines = text.strip().split("\n")
    for line in lines:
        if line.strip() and len(line.strip()) > 4:
            return line.strip()
    return "Store not found"


def extract_date(text):
    # Pattern: regex + corresponding date format
    patterns = [
        (r"\d{2}/\d{2}/\d{4}", "%m/%d/%Y"),  # 04/13/2025
        (r"\d{4}-\d{2}-\d{2}", "%Y-%m-%d"),  # 2025-04-13
        (r"\d{2}/\d{2}/\d{2}", "%m/%d/%y"),  # 04/13/25
        (
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},\s+\d{4}\b",
            "%b %d, %Y",
        ),  # Apr 13, 2025
    ]

    for pattern, fmt in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                return datetime.strptime(match.group(), fmt).date()
            except ValueError:
                continue  # If the date string doesn't match the format strictly

    return None  # Or raise ValueError("Date not found")


def extract_total(text):
    lines = text.splitlines()
    for line in reversed(lines):
        if "total" in line.lower():
            match = re.search(r"\d+\.\d{2}", line)
            if match:
                return match.group()
    return "Total not found"


def parse_receipt(filepath):
    text, image_filename = extract_text_from_file(filepath)
    lower = text.lower()

    with open(".\\temp\\output.txt", "w", encoding="utf-8") as f:
        f.write(text)

    for key, parser in STORE_PARSERS.items():
        if key in lower:
            result = parser(text)
            result["image_filename"] = image_filename
            return result

    return {
        "store": extract_store_name(text),
        "date": extract_date(text),
        "total": extract_total(text),
        "image_filename": image_filename,
    }
