# reset_db.py
from app import app, db
from models import *

with app.app_context():
    print("Удаляю старую базу данных...")
    db.drop_all()
    
    print("Создаю новую базу данных с полем request_number...")
    db.create_all()
    
    print("✅ База данных пересоздана с новым полем!")