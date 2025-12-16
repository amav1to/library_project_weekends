from flask_sqlalchemy import SQLAlchemy

# Создаем объект базы данных, который потом подключим в app.py
db = SQLAlchemy()

# Теперь создаем классы (таблицы) для базы данных

class Group(db.Model):
    """Таблица Группы"""
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)  # Например: "АҚЖ-214"
    language = db.Column(db.String(10), nullable=False)  # "kz" или "ru"
    course = db.Column(db.Integer, nullable=False)  # 1 или 2
    
    # Связь: одна группа имеет много студентов
    students = db.relationship('Student', backref='group', lazy=True)
    
    def __repr__(self):
        return f'<Group {self.name}>'

# ВАШ ХОД: Давайте создадим следующую таблицу вместе.
# Как вы думаете, какой должна быть таблица Book (Книга)?
# Вспомните поля из вашего Excel: ID, Название, Автор, Год, Кол-во экземпляров, Доступное кол-во, Язык, Курс

# 1. Как назовем таблицу? (по аналогии с Group)
# 2. Какие поля будут обязательными (nullable=False)?
# 3. Какие типы данных:
#    - id: Integer
#    - Название: String(200)
#    - Автор: String(100)
#    - Год: Integer
#    - total_quantity: Integer (всего экземпляров)
#    - available_quantity: Integer (доступно сейчас)
#    - language: String(10)
#    - course: Integer

# Попробуйте написать код для класса Book ниже, а я проверю:

class Book(db.Model):
    """Книги"""
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)  # Название книги
    author = db.Column(db.String(100), nullable=False)  # Автор книги
    year = db.Column(db.Integer, nullable=False)  # Год издания
    total_quantity = db.Column(db.Integer, nullable=False)  # Всего экземпляров
    available_quantity = db.Column(db.Integer, nullable=False)  # Доступно сейчас
    language = db.Column(db.String(10), nullable=False)  # Язык книги
    course = db.Column(db.Integer, nullable=False)  # Курс
    
    def __repr__(self):
        return f'<Book {self.name} ({self.language})>'
    
class Student(db.Model):
    """Таблица Студенты"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)  # ФИО
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    # group_id ссылается на id в таблице groups
    
    # Связь: один студент может иметь много записей в журнале
    book_requests = db.relationship('BookRequest', backref='student', lazy=True)
    
    def __repr__(self):
        return f'<Student {self.full_name}>'


class BookRequest(db.Model):
    """Журнал выдачи книг (запросы)"""
    __tablename__ = 'book_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(20), unique=True, nullable=True)
    # Ссылки на студента и книгу
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    
    # Даты и время
    request_date = db.Column(db.DateTime, nullable=False, default=db.func.now())  # Дата создания запроса
    issue_date = db.Column(db.DateTime)  # Дата выдачи (когда библиотекарь подтвердил)
    planned_return_date = db.Column(db.DateTime)  # Планируемая дата возврата (+90 минут)
    actual_return_date = db.Column(db.DateTime)  # Фактическая дата возврата
    
    # Основные данные
    quantity = db.Column(db.Integer, nullable=False, default=1)  # Количество взятых экземпляров
    status = db.Column(db.String(20), nullable=False, default='ожидание')  # статусы: ожидание, выдано, возвращено
    
    # Связь с книгой
    book = db.relationship('Book', backref='requests')

    # Диапазон экземпляров книги, закреплённых за этим запросом.
    # Например, для книги с id=105 и 3 экземпляров: 105(01-03)
    copy_start_index = db.Column(db.Integer, nullable=True)
    copy_end_index = db.Column(db.Integer, nullable=True)

    @property
    def copy_range_display(self):
        """
        Возвращает человеко‑читаемую строку с диапазоном экземпляров.
        Примеры:
        - "105(01)"       если один экземпляр
        - "105(01-25)"    если несколько экземпляров
        Если диапазон не назначен, возвращает "-".
        """
        if not self.book or self.copy_start_index is None:
            return "-"

        book_code = self.book.id  # Можно заменить на отдельное поле-код, если нужно

        start_str = f"{self.copy_start_index:02d}"
        if self.copy_end_index and self.copy_end_index != self.copy_start_index:
            end_str = f"{self.copy_end_index:02d}"
            return f"{book_code}({start_str}-{end_str})"
        else:
            return f"{book_code}({start_str})"
    
    def __repr__(self):
        return f'<BookRequest {self.id}: {self.status}>'