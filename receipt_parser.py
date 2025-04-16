from datetime import datetime
from pdf2image import convert_from_path
from PIL import Image
import os
import cv2
import pytesseract
import re
import fitz  # PyMuPDF

from store_parsers import STORE_PARSERS
from parsing_utils import *

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
