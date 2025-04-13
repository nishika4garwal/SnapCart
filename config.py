from dotenv import load_dotenv # type: ignore
import os

load_dotenv()  # Load environment variables

SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS')
SECRET_KEY = os.getenv('SECRET_KEY')
