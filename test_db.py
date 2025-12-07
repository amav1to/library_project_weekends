# test_db.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from models import db, BookRequest

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print("=== ПРОВЕРКА ЗАПРОСОВ В БАЗЕ ===")
    
    # Все запросы
    all_requests = BookRequest.query.all()
    print(f"Всего запросов в БД: {len(all_requests)}")
    
    for req in all_requests:
        print(f"  ID: {req.id}, Номер: {req.request_number}, Статус: {req.status}")
    
    # Тестовый запрос из seed.py
    test_req = BookRequest.query.filter_by(request_number='150324-001').first()
    if test_req:
        print(f"\n✅ Тестовый запрос '150324-001' НАЙДЕН!")
        print(f"   ID: {test_req.id}, Статус: {test_req.status}")
    else:
        print("\n❌ Тестовый запрос '150324-001' НЕ НАЙДЕН!")
        
    # Поиск по ID
    test_req_by_id = BookRequest.query.get(1)
    if test_req_by_id:
        print(f"\n✅ Запрос с ID=1 НАЙДЕН!")
        print(f"   Номер: {test_req_by_id.request_number}")