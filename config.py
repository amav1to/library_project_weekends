import os

class Config:
    # Секретный ключ — можно оставить или сгенерировать новый
    SECRET_KEY = os.getenv('SECRET_KEY', 'супер-секретный-ключ-12345-очень-длинный')

    # Строка подключения к базе — берём из переменных окружения
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')

    # Если переменной нет (т.е. запускаем локально) — используем локальную SQLite
    if not SQLALCHEMY_DATABASE_URI:
        basedir = os.path.abspath(os.path.dirname(__file__))
        SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(basedir, "database.db")}'

    SQLALCHEMY_TRACK_MODIFICATIONS = False