# check_data.py
from app import app, db
from models import Group, Student, Book, BookRequest

with app.app_context():
    print("📊 Проверка данных в базе:")
    print("=" * 50)
    
    # Группы
    groups = Group.query.all()
    print(f"Группы ({len(groups)}):")
    for g in groups:
        print(f"  {g.id}. {g.name} ({g.language}) - курс {g.course}")
    
    print("\n" + "=" * 50)
    
    # Студенты с группами
    students = Student.query.all()
    print(f"Студенты ({len(students)}):")
    for s in students:
        print(f"  {s.id}. {s.full_name} -> {s.group.name}")
    
    print("\n" + "=" * 50)
    
    # Книги
    books = Book.query.all()
    print(f"Книги ({len(books)}):")
    for b in books:
        print(f"  {b.id}. '{b.name}' - {b.author} ({b.year})")
        print(f"     Кол-во: {b.available_quantity}/{b.total_quantity}, Язык: {b.language}, Курс: {b.course}")
    
    print("\n" + "=" * 50)
    
    # Запросы
    requests = BookRequest.query.all()
    print(f"Запросы ({len(requests)}):")
    for r in requests:
        print(f"  №{r.request_number}: {r.student.full_name}")
        print(f"     Книга: '{r.book.name}', Кол-во: {r.quantity}, Статус: {r.status}")
        print(f"     ID экземпляров: {r.copy_range_display}")
        print()