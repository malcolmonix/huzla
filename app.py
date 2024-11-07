import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or "dev_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///services.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Firebase configuration
app.config["FIREBASE_API_KEY"] = os.environ.get("FIREBASE_API_KEY")
app.config["FIREBASE_AUTH_DOMAIN"] = os.environ.get("FIREBASE_AUTH_DOMAIN")
app.config["FIREBASE_PROJECT_ID"] = os.environ.get("FIREBASE_PROJECT_ID")
app.config["FIREBASE_STORAGE_BUCKET"] = os.environ.get("FIREBASE_STORAGE_BUCKET")
app.config["FIREBASE_MESSAGING_SENDER_ID"] = os.environ.get("FIREBASE_MESSAGING_SENDER_ID")
app.config["FIREBASE_APP_ID"] = os.environ.get("FIREBASE_APP_ID")

db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

with app.app_context():
    import models
    import routes
    db.create_all()
