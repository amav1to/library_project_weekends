import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'ваш-секретный-ключ-сюда-12345')
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')
    SQLALCHEMY_TRACK_MODIFICATIONS = False