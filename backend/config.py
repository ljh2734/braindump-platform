import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-for-braindump')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///braindump.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False