import os
import socket
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash
from sqlalchemy import Date, and_, cast, literal, select
from werkzeug.utils import secure_filename

from models import CardSuffix, Category, Receipt, StoreCategoryMap, db
from receipt_parser import parse_receipt


# Allow VSCode to attach to the debug server at port 5678
DEBUG_PORT = 5678
if os.getenv("ENABLE_DEBUGPY", "1") != "0":
    try:
        import debugpy

        def is_port_open(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(("localhost", port)) != 0

        if is_port_open(DEBUG_PORT):
            debugpy.listen(("0.0.0.0", DEBUG_PORT))
            print(f"🔗 debugpy is listening on port {DEBUG_PORT}")
        else:
            print(f"⚠️ Port {DEBUG_PORT} already in use, skipping debugpy.listen")

    except Exception as e:
        print(f"⚠️ debugpy setup failed: {e}")

app = Flask(__name__)
app.secret_key = "super_secret_key_here"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///receipts.db"
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


@app.context_processor
def inject_goblin_sounds():
    folder = os.path.join(app.static_folder, "sounds") if app.static_folder else None
    sounds = []
    if folder and os.path.isdir(folder):
        sounds = [
            f"/static/sounds/{f}" for f in os.listdir(folder) if f.endswith(".mp3")
        ]
    return dict(sounds=sounds)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["receipt"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            result = parse_receipt(filepath)
            store_mapping = StoreCategoryMap.query.filter_by(
                store=result["store"]
            ).first()
            category = store_mapping.category if store_mapping else None

            new_receipt = Receipt(
                store=result["store"],
                date=result["date"],
                total=(
                    float(result["total"])
                    if result["total"] != "Total not found"
                    else 0.0
                ),
                image_filename=result["image_filename"],
                category=category,
                card_number=result.get("card_number"),
            )
            db.session.add(new_receipt)
            db.session.commit()
            return redirect("/")
    return render_template("index.html")


@app.route("/admin")
def admin():
    filter_option = request.args.get("filter", "week")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")
    today = datetime.today()

    def parse_date(s):
        for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m-%d-%Y", "%m/%d/%y"):
            try:
                return datetime.strptime(s, fmt)
            except:
                continue
        return None

    start_date = parse_date(start_date_str) if start_date_str else None
    end_date = parse_date(end_date_str) if end_date_str else None
    query = Receipt.query.join(Category, isouter=True).order_by(
        Receipt.datetime_added.desc()
    )

    if filter_option == "day":
        query = query.filter(Receipt.date == today.strftime("%Y-%m-%d"))  # type: ignore
    elif filter_option == "week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        query = query.filter(
            Receipt.date.between(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")) # type: ignore
        )  # type: ignore
    elif filter_option == "month":
        query = query.filter(Receipt.date.startswith(today.strftime("%Y-%m")))  # type: ignore
    elif filter_option == "range" and start_date and end_date:
        query = query.filter(
            Receipt.date.between( # type: ignore
                start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )
        )  # type: ignore

    receipts = query.all()
    total = sum(r.total for r in receipts)

    latest_receipt = Receipt.query.order_by(Receipt.datetime_added.desc()).first()
    latest_global = latest_receipt.datetime_added.isoformat() if latest_receipt else ""

    return render_template(
        "admin.html",
        receipts=receipts,
        headers=["Added", "Store", "Date", "Total", "Category", "Image"],
        total=f"{total:.2f}",
        filter=filter_option,
        start_date=start_date_str or "",
        end_date=end_date_str or "",
        latest_global=latest_global,
    )

@app.route("/edit_card", methods=["GET", "POST"])
def edit_card():
    cards = CardSuffix.query.order_by(CardSuffix.name).all()
    selected_card_id = request.form.get("card_id") if request.method == "POST" else request.args.get("card_id")

    card = None
    if selected_card_id and selected_card_id != "__new__":
        card = CardSuffix.query.get(int(selected_card_id))

    if request.method == "POST":
        name = request.form["name"]
        last_four = request.form["last_four"]

        if selected_card_id == "__new__" or not selected_card_id:
            existing = CardSuffix.query.filter_by(last_four=last_four).first()
            if existing:
                flash("Card with this number already exists.")
            else:
                new_card = CardSuffix(name=name, last_four=last_four)
                db.session.add(new_card)
        else:
            if card:
                card.name = name
                card.last_four = last_four

        db.session.commit()
        return redirect("/admin")

    # 🔧 Convert cards to dicts so we can serialize to JSON
    cards_dict = [{"id": c.id, "name": c.name, "last_four": c.last_four} for c in cards]

    return render_template(
        "edit_card.html",
        cards=cards_dict,
        selected_card_id=selected_card_id,
        card_name=(card.name if card else ""),
        last_four=(card.last_four if card else "")
    )



@app.route("/edit/<int:receipt_id>", methods=["GET", "POST"])
def edit_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    categories = Category.query.all()
    cards = CardSuffix.query.order_by(CardSuffix.name).all()

    if request.method == "POST":
        receipt.store = request.form["store"]
        try:
            if "date" in request.form:
                receipt.date = datetime.strptime(
                    request.form["date"], "%Y-%m-%d"
                ).date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.")
            return redirect(url_for("edit_receipt", receipt_id=receipt.id))

        receipt.total = float(request.form["total"].replace("$",""))
        receipt.card_number = int(request.form.get("card_number") or 0)

        category_id = request.form.get("category")
        if category_id == "__new__":
            new_name = request.form.get("new_category")
            existing = Category.query.filter_by(name=new_name).first()
            if existing:
                category_id = existing.id
            else:
                if new_name:
                    new_cat = Category(name=new_name)
                    db.session.add(new_cat)
                    db.session.flush()
                    category_id = new_cat.id

        if isinstance(category_id, (str, int)) and category_id:
            receipt.category_id = int(category_id)

        db.session.commit()
        return redirect("/admin")

    return render_template(
        "edit_receipt.html",
        receipt=receipt,
        categories=categories,
        cards=cards,  # ← send to template
    )


@app.route("/categories", methods=["GET", "POST"])
def categories():
    stores = db.session.query(Receipt.store).distinct().all()  # type: ignore[reportCallIssue]
    categories = Category.query.all()
    mappings = {
        mapping.store: mapping.category_id for mapping in StoreCategoryMap.query.all()
    }

    if request.method == "POST":
        for store in stores:
            store_name = store[0]
            category_id = request.form.get(store_name)

            if category_id == "__new__":
                new_name = request.form.get(f"new_{store_name}")
                if new_name:
                    existing = Category.query.filter_by(name=new_name).first()
                    if existing:
                        category_id = existing.id
                    else:
                        new_cat = Category(name=new_name)
                        db.session.add(new_cat)
                        db.session.flush()
                        category_id = new_cat.id

            if isinstance(category_id, (str, int)) and category_id:
                mapping = StoreCategoryMap.query.filter_by(store=store_name).first()
                if not mapping:
                    mapping = StoreCategoryMap(
                        store=store_name, category_id=int(category_id)
                    )
                    db.session.add(mapping)
                    update_receipts = True
                elif str(mapping.category_id) != str(category_id):
                    mapping.category_id = category_id
                    update_receipts = True
                else:
                    update_receipts = False

                if update_receipts:
                    matched_category = Category.query.get(int(category_id))
                    for receipt in Receipt.query.filter_by(store=store_name).all():
                        receipt.category = matched_category

        db.session.commit()
        return redirect("/categories")

    return render_template(
        "categories.html", stores=stores, categories=categories, mappings=mappings
    )


@app.route("/delete/<int:receipt_id>", methods=["POST"])
def delete_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    db.session.delete(receipt)
    db.session.commit()
    print(f"Deleting receipt ID: {receipt_id}")
    return redirect(url_for("admin"))


@app.route("/admin/last_update")
def last_update():
    latest = (
        db.session.query(Receipt.datetime_added)
        .order_by(Receipt.datetime_added.desc())
        .first()
    )
    if latest and latest[0]:
        return {"last_update": latest[0].isoformat()}
    return {"last_update": None}


if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0")
