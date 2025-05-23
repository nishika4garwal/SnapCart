from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask_migrate import Migrate # type: ignore
from models import db, User, Product, Category, Cart, Order  # Import models
import config
import os

app = Flask(__name__)

# Load config values
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = config.SECRET_KEY

# Initialize SQLAlchemy with app
db.init_app(app)

migrate = Migrate(app, db)

# Create tables (run this once)
# with app.app_context():
#     db.create_all()

from routes import * # Import routes after app and db are initialized

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render provides this
    app.run(host='0.0.0.0', port=port)