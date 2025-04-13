from flask_sqlalchemy import SQLAlchemy # type: ignore
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()  # Just initialize, don't attach to app yet
class Admin(db.Model):
    __tablename__ = 'admin'
    username = db.Column(db.String(32), unique=True, primary_key=True)
    passhash = db.Column(db.String(512), nullable=False)

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    passhash = db.Column(db.String(512), nullable=False)
    name = db.Column(db.String(64), nullable=True)

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    @password.setter
    def password(self, password):
        self.passhash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.passhash, password)

class Product(db.Model):  # Class names should start with uppercase
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    price = db.Column(db.Float, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    man_date = db.Column(db.Date, nullable=False)
    category = db.relationship('Category', back_populates='products')

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    products = db.relationship('Product', back_populates='category', cascade='all, delete')

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    product = db.relationship("Product", backref="cart_items")

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    datetime = db.Column(db.DateTime, nullable=False)

    product = db.relationship('Product', backref='orders')


