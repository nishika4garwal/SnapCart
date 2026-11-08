from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_dance.contrib.google import make_google_blueprint
import flask_sqlalchemy 
from flask_migrate import Migrate 
from extensions import limiter
from models import db, User, Product, Category, Cart, Order  
from flask_mail import Mail
import config
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)

# Load config values
app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['SECRET_KEY'] = config.SECRET_KEY

# Initialize SQLAlchemy with app
db.init_app(app)

migrate = Migrate(app, db)
limiter.init_app(app)

# LOCAL DEVELOPMENT ONLY — permits OAuth over HTTP
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_url="/google-login",
)

app.register_blueprint(google_bp, url_prefix="/login")


app.config["MAIL_SERVER"] = os.getenv("MAIL_SERVER", "smtp.gmail.com")
app.config["MAIL_PORT"] = int(os.getenv("MAIL_PORT", 587))
app.config["MAIL_USE_TLS"] = (
    os.getenv("MAIL_USE_TLS", "True").lower() == "true"
)
app.config["MAIL_USERNAME"] = os.getenv("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.getenv("MAIL_DEFAULT_SENDER")

mail = Mail(app)

from routes import *

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Render provides this
    app.run(host='0.0.0.0', port=port)