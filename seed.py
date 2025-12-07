# seed.py - заполнение базы данных тестовыми данными
import sys
import os
from datetime import datetime

# Добавляем текущую папку в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Теперь импортируем
from flask import Flask
from config import Config
from models import db, Group, Book, Student, BookRequest

# Создаем временное приложение для seed
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    print("Начинаем заполнение базы данных...")
    
    # 1. Добавляем группы (из Листа2)
    groups_data = [
        {'name': 'АҚЖ-214', 'language': 'kz', 'course': 2},
        {'name': 'АҚЖ-115', 'language': 'kz', 'course': 1},
        {'name': 'ПО-155', 'language': 'ru', 'course': 1},
        {'name': 'СИБ-125', 'language': 'ru', 'course': 1},
        {'name': 'СИБ-224', 'language': 'ru', 'course': 2},
    ]
    
    print("Добавляем группы...")
    groups = []
    for data in groups_data:
        group = Group(**data)
        db.session.add(group)
        groups.append(group)
        print(f"  - {group.name}")
    
    db.session.commit()
    print(f"✓ Добавлено {len(groups)} групп")
    
    # 2. Добавляем книги (из Листа1)
    books_data = [
        {'name': 'Алгебра 10 класс', 'author': 'Абылкасымова А.Е', 'year': 2019,
         'total_quantity': 100, 'available_quantity': 100, 'language': 'ru', 'course': 1},
        {'name': 'Алгебра 10 класс', 'author': 'Абылкасымова А.Е', 'year': 2019,
         'total_quantity': 100, 'available_quantity': 100, 'language': 'kz', 'course': 1},
        {'name': 'Химия 11 класс', 'author': 'Оспанова М.К', 'year': 2019,
         'total_quantity': 100, 'available_quantity': 100, 'language': 'ru', 'course': 1},
        {'name': 'Химия 11 класс', 'author': 'Оспанова М.К', 'year': 2019,
         'total_quantity': 100, 'available_quantity': 100, 'language': 'kz', 'course': 1},
        {'name': 'Экономика негіздері', 'author': 'Оспанова М.К', 'year': 2019,
         'total_quantity': 50, 'available_quantity': 50, 'language': 'kz', 'course': 2},
        {'name': 'Основы Экономики', 'author': 'Оспанова М.К', 'year': 2019,
         'total_quantity': 50, 'available_quantity': 50, 'language': 'ru', 'course': 2},
    ]
    
    print("Добавляем книги...")
    for data in books_data:
        book = Book(**data)
        db.session.add(book)
        print(f"  - {book.name} ({book.language})")
    
    db.session.commit()
    print(f"✓ Добавлено {len(books_data)} книг")
    
    # 3. Добавляем студентов (из Листа3)
    students_data = [
        {'full_name': 'Майданов Рауан', 'group_id': 1},
        {'full_name': 'Абдраимов Данияр', 'group_id': 1},
        {'full_name': 'Сасавот', 'group_id': 2},
        {'full_name': 'Бамблби', 'group_id': 3},
        {'full_name': 'Моргенштерн', 'group_id': 5},
    ]
    
    print("Добавляем студентов...")
    for data in students_data:
        student = Student(**data)
        db.session.add(student)
        print(f"  - {student.full_name} (группа ID: {student.group_id})")
    
    db.session.commit()
    print("✓ Добавлены студенты")
    
    # 4. Создаем несколько тестовых запросов (опционально)
    print("\nСоздаем тестовые запросы...")
    
    # Примеры запросов с request_number
    test_date = datetime.now().strftime('%d%m%y')
    
    test_requests = [
        {
            'student_id': 1,
            'book_id': 1,
            'quantity': 2,
            'status': 'ожидание',
            'request_date': datetime.now(),
            'request_number': f'{test_date}-001'
        },
        {
            'student_id': 2,
            'book_id': 2,
            'quantity': 1,
            'status': 'выдано',
            'request_date': datetime.now(),
            'issue_date': datetime.now(),
            'request_number': f'{test_date}-002'
        },
        {
            'student_id': 3,
            'book_id': 3,
            'quantity': 1,
            'status': 'возвращено',
            'request_date': datetime.now(),
            'issue_date': datetime.now(),
            'actual_return_date': datetime.now(),
            'request_number': f'{test_date}-003'
        },
    ]
    
    for i, data in enumerate(test_requests):
        book_request = BookRequest(**data)
        db.session.add(book_request)
        print(f"  - Запрос {data['request_number']}: {data['status']}")
    
    db.session.commit()
    print("✓ Добавлены тестовые запросы")
    
    print("\n✅ База данных успешно заполнена!")
    print(f"   Всего групп: {Group.query.count()}")
    print(f"   Всего книг: {Book.query.count()}")
    print(f"   Всего студентов: {Student.query.count()}")
    print(f"   Всего запросов: {BookRequest.query.count()}")