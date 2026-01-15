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
    total_quantity = db.Column(db.Integer, nullable=False)
    language = db.Column(db.String(10), nullable=False)
    course = db.Column(db.Integer, nullable=False)
    publisher = db.Column(db.String(100), nullable=True)  # Издательство
    
    copies = db.relationship('BookCopy', backref='book', lazy=True, cascade="all, delete-orphan")
    
    @property
    def available_quantity(self):
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
    """Таблица экземпляров книг"""
    __tablename__ = 'book_copies'
    
    id = db.Column(db.Integer, primary_key=True)
    copy_code = db.Column(db.String(50), unique=True, nullable=False)
    
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    current_request_id = db.Column(db.Integer, db.ForeignKey('book_requests.id'), nullable=True)
    
    current_request = db.relationship('BookRequest', backref='assigned_copies', foreign_keys=[current_request_id])
    
    def __repr__(self):
        status = "свободен" if self.is_available else "выдан"
        return f'<BookCopy {self.copy_code} — {status}>'

class BookRequest(db.Model):
    """Журнал запросов"""
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
    status = db.Column(db.String(20), nullable=False, default='ожидание')
    
    # Новое поле: коды, запрошенные студентом (строка через запятую)
    requested_copy_codes = db.Column(db.String(500), nullable=True)
    # Сохраняет коды, которые были фактически выданы (чтобы оставлять их видимыми после возврата)
    issued_copy_codes = db.Column(db.String(500), nullable=True)
    
    book = db.relationship('Book', backref='requests')
    
    @property
    def assigned_copy_codes(self):
        # Для ожидания — показываем запрошенные студентом
        if self.status == 'ожидание' and self.requested_copy_codes:
            return self.requested_copy_codes.replace(',', ', ')
        # Для выданных/возвращённых — показываем сохранённые выданные коды, если они есть
        if self.issued_copy_codes:
            return self.issued_copy_codes.replace(',', ', ')
        # В крайнем случае — проверяем текущие привязанные копии
        copies = BookCopy.query.filter_by(current_request_id=self.id).all()
        return ', '.join([copy.copy_code for copy in copies]) if copies else "-"
    
    def __repr__(self):
        return f'<BookRequest {self.id}: {self.status}>'