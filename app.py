from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from datetime import datetime

from receipt_parser import parse_receipt

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///receipts.db"
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    receipts = db.relationship("Receipt", backref="category", lazy=True)


class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date)
    total = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=True)
    image_filename = db.Column(db.String(200), nullable=True)

@app.context_processor
def inject_goblin_sounds():
    folder = os.path.join(app.static_folder, "sounds")
    sounds = [f"/static/sounds/{f}" for f in os.listdir(folder) if f.endswith(".mp3")]
    return dict(sounds=sounds)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files["receipt"]
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(filepath)

            result = parse_receipt(filepath)
            matched_receipt = Receipt.query.filter_by(store=result["store"]).first()
            category = (
                matched_receipt.category
                if matched_receipt and matched_receipt.category
                else None
            )

            new_receipt = Receipt(
                store=result["store"],
                date=result["date"],
                total=float(result["total"])
                if result["total"] != "Total not found"
                else 0.0,
                image_filename=result["image_filename"],
                category=category,
            )
            db.session.add(new_receipt)
            db.session.commit()
            return redirect("/")
    return render_template("index.html")


@app.route("/admin")
def admin():
    from datetime import datetime, timedelta

    filter_option = request.args.get("filter", "all")
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

    query = Receipt.query.join(Category, isouter=True)

    if filter_option == "day":
        query = query.filter(Receipt.date == today.strftime("%Y-%m-%d"))
    elif filter_option == "week":
        start = today - timedelta(days=today.weekday())
        end = start + timedelta(days=6)
        query = query.filter(
            Receipt.date.between(start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d"))
        )
    elif filter_option == "month":
        query = query.filter(Receipt.date.startswith(today.strftime("%Y-%m")))
    elif filter_option == "range" and start_date and end_date:
        query = query.filter(
            Receipt.date.between(
                start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")
            )
        )

    receipts = query.all()
    total = sum(r.total for r in receipts)

    return render_template(
        "admin.html",
        receipts=receipts,
        headers=["Store", "Date", "Total", "Category", "Image"],
        total=f"{total:.2f}",
        filter=filter_option,
        start_date=start_date_str or "",
        end_date=end_date_str or "",
    )


@app.route("/edit/<int:receipt_id>", methods=["GET", "POST"])
def edit_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    categories = Category.query.all()

    if request.method == "POST":
        receipt.store = request.form["store"]
        try:
            receipt.date = datetime.strptime(request.form["date"], "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD.")
            return redirect(url_for("edit_receipt", receipt_id=receipt.id))
        receipt.total = float(request.form["total"])
        category_id = request.form.get("category")
        receipt.category_id = int(category_id) if category_id else None
        db.session.commit()
        return redirect("/admin")

    return render_template("edit_receipt.html", receipt=receipt, categories=categories)


@app.route("/categories", methods=["GET", "POST"])
def categories():
    stores = db.session.query(Receipt.store).distinct().all()
    categories = Category.query.all()

    if request.method == "POST":
        for store in stores:
            store_name = store[0]
            category_id = request.form.get(store_name)
            if category_id == "__new__":
                new_name = request.form.get(f"new_{store_name}")
                if new_name:
                    new_cat = Category(name=new_name)
                    db.session.add(new_cat)
                    db.session.flush()
                    category_id = new_cat.id
            if category_id:
                matched_category = Category.query.get(int(category_id))
                receipts = Receipt.query.filter_by(store=store_name).all()
                for receipt in receipts:
                    receipt.category = matched_category
        db.session.commit()
        return redirect("/categories")

    return render_template("categories.html", stores=stores, categories=categories)

@app.route("/delete/<int:receipt_id>", methods=["POST"])
def delete_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    db.session.delete(receipt)
    db.session.commit()
    return redirect(url_for("admin"))



if __name__ == "__main__":
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0")