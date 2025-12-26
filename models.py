from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Group(db.Model):
    """Таблица Группы"""
    __tablename__ = 'groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    language = db.Column(db.String(10), nullable=False)
    course = db.Column(db.Integer, nullable=False)
    
    students = db.relationship('Student', backref='group', lazy=True)
    
    def __repr__(self):
        return f'<Group {self.name}>'


class Book(db.Model):
    """Таблица Книги"""
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    total_quantity = db.Column(db.Integer, nullable=False)  # Общее количество экземпляров
    language = db.Column(db.String(10), nullable=False)
    course = db.Column(db.Integer, nullable=False)
    
    # Связь с экземплярами
    copies = db.relationship('BookCopy', backref='book', lazy=True, cascade="all, delete-orphan")
    
    @property
    def available_quantity(self):
        """Доступное количество = количество свободных экземпляров"""
        return len([copy for copy in self.copies if copy.is_available])

    def __repr__(self):
        return f'<Book {self.name} ({self.language})>'


class Student(db.Model):
    """Таблица Студенты"""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    
    book_requests = db.relationship('BookRequest', backref='student', lazy=True)
    
    def __repr__(self):
        return f'<Student {self.full_name}>'


class BookCopy(db.Model):
    """Таблица физических экземпляров книг (по одному на каждый QR-код)"""
    __tablename__ = 'book_copies'
    
    id = db.Column(db.Integer, primary_key=True)  # Автоинкрементный ID в БД
    copy_code = db.Column(db.String(50), unique=True, nullable=False)  # Уникальный код экземпляра, например "10501" — это то, что в QR-коде
    
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    
    # Состояние экземпляра
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    current_request_id = db.Column(db.Integer, db.ForeignKey('book_requests.id'), nullable=True)
    
    # Связь с текущим запросом (если выдан)
    current_request = db.relationship('BookRequest', backref='assigned_copies', foreign_keys=[current_request_id])
    
    def __repr__(self):
        status = "свободен" if self.is_available else "выдан"
        return f'<BookCopy {self.copy_code} — {status}>'


class BookRequest(db.Model):
    """Журнал запросов и выдачи книг"""
    __tablename__ = 'book_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    request_number = db.Column(db.String(20), unique=True, nullable=True)
    
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    
    request_date = db.Column(db.DateTime, nullable=False, default=db.func.now())
    issue_date = db.Column(db.DateTime)
    planned_return_date = db.Column(db.DateTime)
    actual_return_date = db.Column(db.DateTime)
    
    quantity = db.Column(db.Integer, nullable=False, default=1)
    status = db.Column(db.String(20), nullable=False, default='ожидание')  # ожидание, выдано, возвращено
    
    # Связь с книгой
    book = db.relationship('Book', backref='requests')
    
    @property
    def assigned_copy_codes(self):
        """Возвращает список кодов выданных экземпляров для этого запроса"""
        copies = BookCopy.query.filter_by(current_request_id=self.id).all()
        return ', '.join([copy.copy_code for copy in copies]) if copies else "-"
    
    def __repr__(self):
        return f'<BookRequest {self.id}: {self.status}>'