from datetime import datetime
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, CheckConstraint, DateTime  
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Category(db.Model):
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    receipts = relationship("Receipt", backref="category", lazy=True)

    def __init__(self, name: str):
        self.name = name

class Receipt(db.Model):
    id = Column(Integer, primary_key=True)
    datetime_added = Column(DateTime, default=datetime.now)
    store = Column(String(120), nullable=False)
    date = Column(Date)
    total = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    image_filename = Column(String(200), nullable=True)
    card_number = Column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint("card_number BETWEEN 0 AND 9999", name="check_card_number_range"),
    )

    def __init__(self, store: str, date: Date, total: float,
                 image_filename: Optional[str] = None, category=None, card_number: Optional[int] = None):
        self.store = store
        self.date = date
        self.total = total
        self.image_filename = image_filename
        self.category = category
        self.card_number = card_number

class StoreCategoryMap(db.Model):
    __tablename__ = "store_category_map"

    store = Column(String(120), primary_key=True)
    category_id = Column(Integer, ForeignKey("category.id"), nullable=True)
    category = relationship("Category", backref="store_mappings", lazy=True)

    def __init__(self, store: str, category_id: int):
        self.store = store
        self.category_id = category_id

class CardSuffix(db.Model):
    id = Column(Integer, primary_key=True)
    last_four = Column(String(4), unique=True, nullable=False)
    name = Column(String(120))

    def __init__(self, last_four: str, name: str):
        self.last_four = last_four
        self.name = name