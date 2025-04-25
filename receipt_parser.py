from datetime import datetime
import fitz
from pdf2image import convert_from_path
from PIL import Image
import os
import cv2
import pytesseract
import re
from fitz import Page  # PyMuPDF

from store_parsers import STORE_PARSERS
from parsing_utils import *
from models import CardSuffix

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


def extract_card_last_four(text, known_suffixes):
    matches = re.findall(r"\b\d{4}\b", text)
    for match in matches:
        if match in known_suffixes:
            return int(match)
    return None


def pdf_has_text(filepath: str) -> bool:
    with fitz.open(filepath) as pdf:
        for i in range(len(pdf)):
            page: Page = pdf[i]
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
        images = images = convert_from_path(filepath, poppler_path=os.path.join(os.getcwd(), "poppler", "Library", "bin"))


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

        # Save the final combined image with unique name
        if combined:
            image = combined
            name, ext = os.path.splitext(filename.replace(".pdf", ".jpg"))
            upload_dir = "static/uploads"
            counter = 1
            unique_filename = f"{name}{ext}"
            save_path = os.path.join(upload_dir, unique_filename)

            while os.path.exists(save_path):
                unique_filename = f"{name}_{counter}{ext}"
                save_path = os.path.join(upload_dir, unique_filename)
                counter += 1

            image.save(save_path, "JPEG")
            filename = unique_filename

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

    known_suffixes = [c.last_four for c in CardSuffix.query.all()]
    matched_suffix = extract_card_last_four(text, known_suffixes)

    for matcher, parser in STORE_PARSERS:
        if matcher(text):
            result = parser(text)
            result["image_filename"] = image_filename
            result["card_number"] = matched_suffix
            return result

    return {
        "store": extract_store_name(text),
        "date": extract_date(text),
        "total": extract_total(text),
        "image_filename": image_filename,
        "card_number": matched_suffix,
    }
