from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv

load_dotenv()
fernet = Fernet(os.environ['FERNET_KEY'])

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    totp_secret_encrypted = db.Column(db.LargeBinary, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def set_totp_secret(self, secret):
        self.totp_secret_encrypted = fernet.encrypt(secret.encode())

    def get_totp_secret(self):
        if self.totp_secret_encrypted:
            return fernet.decrypt(self.totp_secret_encrypted).decode()
        return None
