import sys
import os
import pandas as pd
import re
from app import app, db
from models import Book, BookCopy, Group, Student  # ← добавлен импорт Student

def detect_language(title):
    """
    Определяет язык обучения по названию книги.
    Возвращает 'kz', 'ru', или 'both'
    """
    title_lower = title.lower()
    
    # Казахские символы
    kazakh_chars = 'әғқңөүұһі'
    has_kazakh = any(char in title for char in kazakh_chars)
    
    # Русские символы
    russian_chars = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
    has_russian = any(char in title_lower for char in russian_chars)
    
    # Английские символы
    has_english = bool(re.search(r'[a-z]', title_lower))
    
    # Ключевые слова
    keywords_russian_groups = ['русск', 'для русск', 'русские группы', 'русс', 'рус. группа']
    keywords_kazakh_groups = ['қазақ', 'казах', 'қазақ тілі', 'казахский язык', 'қазақша']
    
    has_russian_indication = any(keyword in title_lower for keyword in keywords_russian_groups)
    has_kazakh_indication = any(keyword in title_lower for keyword in keywords_kazakh_groups)
    
    has_okulyk = 'оқулық' in title_lower or 'okulyk' in title_lower
    has_uchebnik = 'учебник' in title_lower or 'uchebnik' in title_lower
    has_emn = 'емн' in title_lower or 'emn' in title_lower
    
    if has_english and has_okulyk and has_uchebnik and not has_russian_indication and not has_kazakh_indication:
        return 'both'
    
    if has_english and has_emn and has_kazakh and has_russian and not has_russian_indication and not has_kazakh_indication:
        return 'both'
    
    if has_russian_indication and not has_kazakh_indication:
        return 'ru'
    
    if has_kazakh_indication and not has_russian_indication:
        return 'kz'
    
    if has_kazakh and not has_russian_indication:
        return 'kz'
    
    if has_kazakh and has_russian and has_english:
        return 'both'
    
    if has_kazakh and has_russian and not has_english:
        return 'kz'
    
    if has_russian and not has_kazakh:
        return 'ru'
    
    return 'ru'  # По умолчанию

def parse_author_and_title(full_text):
    """
    Парсит строку "Автор. Название" и разделяет на автора и название.
    """
    if pd.isna(full_text) or not full_text:
        return "", ""
    
    full_text = str(full_text).strip()
    
    match = re.search(r'^(.+?)\s*\.\s+(.+)$', full_text)
    if match:
        author = match.group(1).strip()
        title = match.group(2).strip()
        return author, title
    
    return "", full_text

def read_excel_file():
    """Читает Excel файл и возвращает DataFrame"""
    excel_file = None
    for file in os.listdir('.'):
        if file.endswith('.xlsx'):
            excel_file = file
            break
    
    if not excel_file:
        raise FileNotFoundError("Excel файл не найден в текущей директории")
    
    print(f"Читаю файл: {excel_file}")
    
    df = pd.read_excel(excel_file, header=1, skiprows=[0])
    
    df.columns = ['№п/п', '№_регистрационный', 'Автор_и_название', 'Издательство', 'Год_издания']
    
    df = df.dropna(subset=['Автор_и_название', '№_регистрационный'])
    
    df['№_регистрационный'] = df['№_регистрационный'].astype(str).str.strip()
    df['Автор_и_название'] = df['Автор_и_название'].astype(str).str.strip()
    df['Издательство'] = df['Издательство'].astype(str).str.strip()
    df['Год_издания'] = pd.to_numeric(df['Год_издания'], errors='coerce')
    
    return df

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

def seed_database():
    """Основная функция для заполнения базы данных"""
    with app.app_context():
        print("Начинаю заполнение базы данных...")
        print("=" * 60)
        print("ВНИМАНИЕ: Убедитесь, что база данных обновлена с новой колонкой 'publisher'")
        print("   Если нужно, запустите reset_db.py для пересоздания базы данных")
        print("=" * 60)
        
        # Очищаем существующие данные (опционально, можно закомментировать)
        print("\nОчищаю существующие данные...")
        BookCopy.query.delete()
        Book.query.delete()
        Student.query.delete()
        Group.query.delete()
        db.session.commit()
        print("Существующие данные удалены")
        
        # Создаем группы
        print("\nСоздаю группы...")
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
        print(f"Создано {len(groups)} групп")
        
        # Создаем студентов
        create_students(groups)
        
        # Читаем Excel файл
        df = read_excel_file()
        print(f"Прочитано {len(df)} записей из Excel")
        
        # Группируем по книгам
        print("\nГруппирую книги...")
        books_dict = {}
        
        for idx, row in df.iterrows():
            reg_number = str(row['№_регистрационный']).strip()
            author_title = str(row['Автор_и_название']).strip()
            publisher = str(row['Издательство']).strip() if pd.notna(row['Издательство']) else ""
            year = int(row['Год_издания']) if pd.notna(row['Год_издания']) else 2020
            
            if not author_title or not reg_number:
                continue
            
            author, title = parse_author_and_title(author_title)
            
            book_key = author_title
            
            if book_key not in books_dict:
                language = detect_language(author_title)
                
                books_dict[book_key] = {
                    'author': author,
                    'title': title if title else author_title,
                    'full_name': author_title,
                    'publisher': publisher,
                    'year': year,
                    'language': language,
                    'copy_codes': []
                }
            
            books_dict[book_key]['copy_codes'].append(reg_number)
        
        print(f"Найдено {len(books_dict)} уникальных книг")
        
        # Создаем книги и экземпляры
        print("\nСоздаю записи в базе данных...")
        created_books = 0
        created_copies = 0
        
        for book_key, book_data in books_dict.items():
            total_quantity = len(book_data['copy_codes'])
            
            book = Book(
                name=book_data['full_name'],
                author=book_data['author'] if book_data['author'] else "Не указан",
                year=book_data['year'],
                total_quantity=total_quantity,
                language=book_data['language'],
                course=1,
                publisher=book_data['publisher'] if book_data['publisher'] else None
            )
            
            db.session.add(book)
            db.session.flush()  # Получаем ID книги
            
            unique_copy_codes = list(set(book_data['copy_codes']))
            
            def extract_number(code):
                code_str = str(code).strip()
                match = re.search(r'(\d+)\s*[\(]?\s*(\d+)', code_str)
                if match:
                    main_num = int(match.group(1))
                    sub_num = int(match.group(2))
                    return (main_num, sub_num)
                match = re.search(r'(\d+)', code_str)
                if match:
                    return (int(match.group(1)), 0)
                return (0, 0)
            
            unique_copy_codes = sorted(unique_copy_codes, key=extract_number)
            
            for copy_code in unique_copy_codes:
                existing_copy = BookCopy.query.filter_by(copy_code=copy_code).first()
                if existing_copy:
                    print(f"  Пропущен дубликат copy_code: {copy_code}")
                    continue
                
                copy = BookCopy(
                    copy_code=copy_code,
                    book_id=book.id,
                    is_available=True,
                    current_request_id=None
                )
                db.session.add(copy)
                created_copies += 1
            
            created_books += 1
            
            if created_books % 100 == 0:
                print(f"  Обработано {created_books} книг...")
        
        db.session.commit()
        
        print("\n" + "=" * 60)
        print("Заполнение завершено!")
        print(f"Создано книг: {created_books}")
        print(f"Создано экземпляров: {created_copies}")
        print(f"Создано студентов: {Student.query.count()}")
        
        lang_stats = db.session.query(Book.language, db.func.count(Book.id)).group_by(Book.language).all()
        print("\nСтатистика по языкам обучения:")
        for lang, count in lang_stats:
            print(f"  {lang}: {count} книг")
        
        print("\nПримеры созданных книг (первые 5):")
        sample_books = Book.query.limit(5).all()
        for i, book in enumerate(sample_books, 1):
            copies_count = BookCopy.query.filter_by(book_id=book.id).count()
            print(f"  {i}. ID: {book.id}, Язык: {book.language}, Экземпляров: {copies_count}")

if __name__ == '__main__':
    seed_database()