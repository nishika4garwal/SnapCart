from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy # type: ignore
from flask_migrate import Migrate # type: ignore
from models import db, User, Product, Category, Cart, Order  # Import models
import config

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

import routes  # Import routes after app and db are initialized
