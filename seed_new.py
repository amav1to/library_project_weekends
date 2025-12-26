# seed.py
from app import app, db
from models import Group, Student, Book, BookCopy, BookRequest
from datetime import datetime, timedelta
import random

def create_groups():
    """Создаем 5 групп"""
    groups_data = [
        ("АКЖ-214", "kz", 1),
        ("АКЖ-215", "kz", 2),
        ("РУД-101", "ru", 1),
        ("РУД-102", "ru", 2),
        ("АКЖ-216", "kz", 1)
    ]
    
    groups = []
    for name, language, course in groups_data:
        group = Group(name=name, language=language, course=course)
        db.session.add(group)
        groups.append(group)
    
    db.session.commit()
    print(f"✅ Создано {len(groups)} групп")
    return groups

def create_students(groups):
    """Создаем по 2 студента в каждую группу"""
    kz_names = [
        "Алиев Асылбек Талгатович",
        "Нургалиева Айгуль Саматовна", 
        "Жаныбеков Дамир Канатович",
        "Омарова Гульназ Рахмановна",
        "Сатпаев Ербол Нурланович",
        "Ташметова Айнур Бауржановна"
    ]
    
    ru_names = [
        "Иванов Иван Иванович",
        "Петрова Мария Сергеевна",
        "Сидоров Алексей Владимирович",
        "Кузнецова Екатерина Андреевна",
        "Смирнов Дмитрий Петрович",
        "Васильева Анна Николаевна"
    ]
    
    students = []
    for group in groups:
        names = kz_names if group.language == "kz" else ru_names
        
        for i in range(2):
            if names:
                full_name = names.pop(0)
                student = Student(full_name=full_name, group_id=group.id)
                db.session.add(student)
                students.append(student)
    
    db.session.commit()
    print(f"✅ Создано {len(students)} студентов")
    return students

def create_books_with_copies():
    """Создаем 5 учебников по 50 экземпляров каждый"""
    books_data = [
        ("Қазақ тілі", "Ахметов Б.Т.", 2020, "kz", 1),
        ("Казахский язык", "Петров В.Г.", 2021, "ru", 1),
        ("Математикалық талдау", "Смагулов К.К.", 2019, "kz", 2),
        ("Математический анализ", "Иванов А.А.", 2020, "ru", 2),
        ("Ағылшын тілі", "Johnson M.", 2022, "kz", 1)
    ]
    
    books = []
    
    # 1. Создаем книги
    print("📚 Создаю книги...")
    for name, author, year, language, course in books_data:
        book = Book(
            name=name,
            author=author,
            year=year,
            total_quantity=50,
            language=language,
            course=course
        )
        db.session.add(book)
        books.append(book)
    
    db.session.commit()  # Получаем ID для книг
    
    # 2. Создаем экземпляры для каждой книги
    print("🔢 Создаю экземпляры книг...")
    all_copies = []
    
    for book in books:
        copies_for_book = []
        
        for i in range(1, 51):
            copy_code = f"{book.id}-{i:02d}"  # Формат: 1-01, 1-02, ..., 1-50
            
            copy = BookCopy(
                copy_code=copy_code,
                book_id=book.id,
                is_available=True,
                current_request_id=None
            )
            copies_for_book.append(copy)
            all_copies.append(copy)
            db.session.add(copy)
        
        # Показываем примеры кодов
        if copies_for_book:
            print(f"   Книга '{book.name}' (ID:{book.id}): {copies_for_book[0].copy_code} ... {copies_for_book[-1].copy_code}")
    
    db.session.commit()
    print(f"✅ Создано {len(books)} книг и {len(all_copies)} экземпляров")
    return books

def create_book_requests(students, books):
    """Создаем тестовые запросы на книги"""
    today = datetime.now().strftime("%d%m%y")
    requests = []
    
    request_examples = [
        (0, 0, 2, "выдано"),
        (1, 1, 1, "ожидание"),
        (2, 2, 3, "возвращено"),
        (3, 3, 1, "выдано"),
        (4, 4, 2, "ожидание"),
        (5, 0, 1, "выдано"),
        (6, 1, 2, "возвращено"),
        (7, 2, 1, "ожидание")
    ]
    
    # Собираем доступные экземпляры
    available_copies_by_book = {}
    for book in books:
        available_copies_by_book[book.id] = BookCopy.query.filter_by(
            book_id=book.id, 
            is_available=True
        ).order_by(BookCopy.copy_code).all()
    
    for i, (student_idx, book_idx, quantity, status) in enumerate(request_examples):
        if student_idx < len(students) and book_idx < len(books):
            student = students[student_idx]
            book = books[book_idx]
            
            available_copies = available_copies_by_book.get(book.id, [])
            
            if len(available_copies) < quantity and status in ["выдано", "возвращено"]:
                print(f"⚠️  Недостаточно экземпляров для книги '{book.name}'")
                continue
            
            # Создаем запрос
            request_number = f"{today}-{i+1:03d}"
            request_date = datetime.now() - timedelta(days=random.randint(0, 10))
            
            if status == "выдано":
                issue_date = request_date + timedelta(hours=1)
                planned_return_date = issue_date + timedelta(days=14)
                actual_return_date = None
            elif status == "возвращено":
                issue_date = request_date + timedelta(hours=1)
                planned_return_date = issue_date + timedelta(days=14)
                actual_return_date = planned_return_date - timedelta(days=random.randint(0, 5))
            else:
                issue_date = None
                planned_return_date = None
                actual_return_date = None
            
            request = BookRequest(
                request_number=request_number,
                student_id=student.id,
                book_id=book.id,
                request_date=request_date,
                issue_date=issue_date,
                planned_return_date=planned_return_date,
                actual_return_date=actual_return_date,
                quantity=quantity,
                status=status
            )
            
            db.session.add(request)
            db.session.flush()  # Получаем ID запроса
            
            # Привязываем экземпляры для выданных/возвращенных книг
            if status in ["выдано", "возвращено"]:
                copies_to_assign = available_copies[:quantity]
                assigned_codes = []
                
                for copy in copies_to_assign:
                    copy.is_available = False
                    copy.current_request_id = request.id
                    assigned_codes.append(copy.copy_code)
                    available_copies.remove(copy)
                
                available_copies_by_book[book.id] = available_copies
                
                print(f"   📖 Книга '{book.name}': выданы {assigned_codes}")
            
            requests.append(request)
    
    db.session.commit()
    print(f"✅ Создано {len(requests)} запросов")
    return requests

def main():
    """Основная функция"""
    with app.app_context():
        print("🚀 Заполнение базы данных...")
        print("=" * 50)
        
        db.drop_all()
        db.create_all()
        
        groups = create_groups()
        students = create_students(groups)
        books = create_books_with_copies()
        requests = create_book_requests(students, books)
        
        print("=" * 50)
        print("🎉 Готово!")
        
        # Быстрая проверка
        print("\n📊 Быстрая проверка:")
        
        # Проверяем формат кодов
        sample_copy = BookCopy.query.first()
        if sample_copy:
            print(f"Первый экземпляр: {sample_copy.copy_code}")
            if '-' in sample_copy.copy_code:
                book_id, copy_num = sample_copy.copy_code.split('-')
                print(f"  → ID книги: {book_id}, номер: {copy_num}")
        
        # Статистика
        print(f"\nВсего книг: {Book.query.count()}")
        print(f"Всего экземпляров: {BookCopy.query.count()}")
        
        for book in Book.query.all():
            copies = BookCopy.query.filter_by(book_id=book.id).all()
            available = len([c for c in copies if c.is_available])
            print(f"  {book.name}: {len(copies)} экз., доступно {available}")

if __name__ == '__main__':
    main()