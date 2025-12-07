# check_db.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from models import db, Group, Book, Student

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print("=== ПРОВЕРКА БАЗЫ ДАННЫХ ===")
    print(f"Группы: {Group.query.count()} шт.")
    for g in Group.query.all():
        print(f"  - {g.id}: {g.name} ({g.language}, курс {g.course})")
    
    print(f"\nКниги: {Book.query.count()} шт.")
    for b in Book.query.limit(3).all():
        print(f"  - {b.id}: {b.name} ({b.language}, доступно: {b.available_quantity})")
    
    print(f"\nСтуденты: {Student.query.count()} шт.")
    for s in Student.query.all():
        group_name = s.group.name if s.group else 'Нет группы'
        print(f"  - {s.id}: {s.full_name} (группа: {group_name})")