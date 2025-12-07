import os

class Config:
    # Секретный ключ для защиты форм (сгенерируйте свой или оставьте так)
    SECRET_KEY = 'ваш-секретный-ключ-сюда-12345'
    
    # Путь к базе данных SQLite (файл database.db будет создан в папке проекта)
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "database.db")}'
    
    # Отключаем систему уведомлений Flask-SQLAlchemy (не обязательно, но удобно)
    SQLALCHEMY_TRACK_MODIFICATIONS = False