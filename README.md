# 🧾 Receipt Parser App

A Flask-based web app for uploading and parsing receipts from images or PDFs. It extracts store name, date, and total using OCR, then stores and displays the data in an admin dashboard with filters, categories, and editing options.

---

## ✨ Features

- 📤 Upload **images or PDFs** of receipts
- 🔍 Extract **store**, **date**, and **total** using Tesseract OCR
- 🧠 Supports **custom parsing logic per store** (e.g., Walmart, Target)
- 🗂️ Assign categories to stores — either from dropdown or by creating new ones
- 📅 Filter receipts by **day**, **week**, **month**, or **custom date range**
- 🧾 Editable receipt list with inline **image previews**
- 💾 All data stored in a lightweight **SQLite database**

---

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/trasbd/ReceiptParserApp.git
cd ReceiptParserApp
```

### 2. Set Up the Environment

```bash
python -m venv venv
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```

### 3. Install Tesseract & Poppler

- 🔤 [Tesseract OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki)
- 📄 [Poppler for PDF support](https://github.com/oschwartz10612/poppler-windows/releases)

> Add both to your system **PATH** after installation.

---

## 💻 Running the App

```bash
python app.py
```

Then go to `http://localhost:5000` in your browser.

---

## 🧐 Custom Receipt Parsing

Store-specific parsing logic is defined in `store_parsers.py`.  
Each store has its own parser function, and simple matching rules determine which parser is used.

```python
# store_parsers.py

def parse_walmart(text):
    return parse_generic_store(text, "Walmart")

STORE_PARSERS = [
    (lambda text: "walmart" in text.lower(), parse_walmart),
    (lambda text: "mcdonald" in text.lower(), parse_mcdonalds),
    ...
]
```

- **`parse_generic_store`** is used for most stores.
- Some stores (like McDonald's or Taco Bell) use custom regex extraction.
- When uploading a receipt, the app automatically selects the appropriate parser based on keywords found in the OCR text.

---

## 🗂 Folder Structure

```
ReceiptParserApp/
├── app.py               # Flask backend
├── receipt_parser.py    # OCR + store-specific logic
├── templates/           # HTML pages (Jinja2)
├── static/uploads/      # Saved receipt images
├── receipts.db          # SQLite database
├── requirements.txt     # Pip dependencies
└── run_app.bat          # Windows launcher
```

---

## 📸 Screenshots

_You can include screenshots here of:_
- The upload form
- The admin filter dashboard
- The category assignment UI

---

## 🧑‍💻 Credits

Built by [trasbd](https://github.com/trasbd) with guidance, collaboration, and code assistance from [ChatGPT](https://openai.com/chatgpt).  
Design, features, and functionality were iteratively developed with an AI assistant, focused on clarity, extensibility, and style.

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
