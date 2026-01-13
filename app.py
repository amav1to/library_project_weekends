from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from config import Config
from models import db, Group, Book, Student, BookRequest, BookCopy
from datetime import datetime, timedelta
from functools import wraps
from sqlalchemy import or_, func
import string

# Пароль админа
ADMIN_PASSWORD = "KitRulit"

def contains_full_word(text, search_word):
    """
    Проверяет, начинается ли какое-то слово в тексте с введенного запроса (префиксный поиск).
    Поиск без учета регистра. Можно вводить начало слова, но нельзя пропускать буквы в начале.
    
    Примеры:
    - contains_full_word("Алгебра и геометрия", "а") -> True (слово начинается с "а")
    - contains_full_word("Алгебра и геометрия", "ал") -> True
    - contains_full_word("Алгебра и геометрия", "алгебра") -> True
    - contains_full_word("Алгебра и геометрия", "лгебра") -> False (пропущена первая буква)
    - contains_full_word("әскери және технологиялық", "ә") -> True
    - contains_full_word("әскери және технологиялық", "әскери") -> True
    - contains_full_word("әскери және технологиялық", "лғашқы") -> False (пропущены буквы в начале)
    """
    if not text or not search_word:
        return False
    
    text_str = str(text)
    search_str = str(search_word)
    
    # Приводим к нижнему регистру для сравнения
    text_lower = text_str.lower()
    search_lower = search_str.lower()
    
    # Разбиваем текст на слова
    # Заменяем знаки препинания и специальные символы на пробелы
    punctuation_chars = string.punctuation + '.,;:!?()[]{}'
    # Добавляем специальные кавычки отдельно
    special_chars = ['«', '»', '"', '"', "'", "'", '„', '"', '‚', "'"]
    for punct in punctuation_chars:
        text_lower = text_lower.replace(punct, ' ')
    for char in special_chars:
        text_lower = text_lower.replace(char, ' ')
    
    # Разбиваем на слова по пробелам
    words = text_lower.split()
    
    # Проверяем, начинается ли какое-то слово с введенного запроса (префиксный поиск)
    return any(word.startswith(search_lower) for word in words)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'ваш-секретный-ключ-для-сессий-12345'

db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get-groups')
def get_groups():
    groups = Group.query.all()
    groups_list = [{'id': g.id, 'name': g.name} for g in groups]
    return jsonify(groups_list)

@app.route('/get-books/<int:group_id>')
def get_books(group_id):
    group = Group.query.get_or_404(group_id)
    
    # Включаем книги для языка группы и книги для обеих языков ("both")
    books = Book.query.filter(
        or_(
            Book.language == group.language,
            Book.language == 'both'
        ),
        Book.course == group.course
    ).all()
    
    books_list = []
    for book in books:
        available = book.available_quantity
        if available > 0:
            books_list.append({
                'id': book.id,
                'name': f"{book.name} ({book.author}, {book.year})",
                'available': available
            })
    
    return jsonify(books_list)

@app.route('/search-students')
def search_students():
    query = request.args.get('q', '').strip()
    group_id = request.args.get('group_id', '')
    
    if not query:
        return jsonify([])
    
    students_query = Student.query
    if group_id and group_id != 'null' and group_id != '':
        students_query = students_query.filter_by(group_id=int(group_id))
    
    # Поиск по полным словам, нечувствительный к регистру
    # Используем регулярное выражение для поиска целых слов
    # Экранируем специальные символы в запросе
    import re
    escaped_query = re.escape(query.lower())
    # Создаем паттерн для поиска целого слова (с границами слов)
    # Используем \b для границ слов, но в SQLite нужно использовать другой подход
    # Для SQLite используем проверку на наличие слова с пробелами/знаками препинания вокруг
    
    # Получаем всех студентов и фильтруем в Python для более точного поиска
    all_students = students_query.all()
    
    # Фильтруем по полным словам
    filtered_students = [s for s in all_students if contains_full_word(s.full_name, query)]
    
    students_list = [{'id': s.id, 'name': s.full_name} for s in filtered_students[:20]]
    return jsonify(students_list)

@app.route('/get-students/<int:group_id>')
def get_students(group_id):
    students = Student.query.filter_by(group_id=group_id).all()
    students_list = [{'id': s.id, 'name': s.full_name} for s in students]
    return jsonify(students_list)

@app.route('/request-book', methods=['POST'])
def request_book():
    try:
        student_id = request.form.get('student_id')
        book_id = request.form.get('book_id')
        quantity = int(request.form.get('quantity', 1))
        copy_codes_str = request.form.get('copy_codes', '').strip()
        
        # Базовые проверки (как было)
        student = Student.query.get(student_id)
        if not student:
            return "Ошибка: Студент не найден", 400
        
        book = Book.query.get(book_id)
        if not book:
            return "Ошибка: Книга не найдена", 400
        
        # Проверяем язык: книга должна быть для языка группы или для обеих языков
        if book.language not in [student.group.language, 'both'] or book.course != student.group.course:
            return "Ошибка: Эта книга не для вашей группы", 400
        
        # Проверка кодов экземпляров
        if not copy_codes_str:
            return "Ошибка: Не прикреплены экземпляры", 400
        
        codes_list = [c.strip() for c in copy_codes_str.split(',') if c.strip()]
        if len(codes_list) != quantity:
            return f"Ошибка: Прикреплено {len(codes_list)} экземпляров, ожидалось {quantity}", 400
        
        # === НОВАЯ ПРОВЕРКА: все экземпляры должны быть свободны ===
        conflicts = []
        for code in codes_list:
            copy = BookCopy.query.filter_by(copy_code=code, book_id=book.id).first()
            if not copy:
                conflicts.append(f"{code} (не найден)")
                continue
            if not copy.is_available:
                # Находим, кому выдан (если есть запрос)
                if not copy.is_available:
                    conflicts.append(f"{code} (экземпляр уже выдан)")
                    continue
        
        if conflicts:
            conflict_msg = "; ".join(conflicts)
            return f"Ошибка: Невозможно прикрепить: {conflict_msg}", 400
        
        # Генерация номера запроса (как было)
        today = datetime.now().strftime('%d%m%y')
        last_request = BookRequest.query.filter(
            BookRequest.request_number.like(f'{today}-%')
        ).order_by(BookRequest.id.desc()).first()
        
        next_number = 1
        if last_request and last_request.request_number:
            last_number = int(last_request.request_number.split('-')[1])
            next_number = last_number + 1
        
        request_number = f'{today}-{next_number:03d}'
        
        # Создаём запрос
        new_request = BookRequest(
            student_id=student_id,
            book_id=book_id,
            quantity=quantity,
            status='ожидание',
            request_date=datetime.now(),
            request_number=request_number,
            requested_copy_codes=','.join(codes_list)  # сохраняем коды
        )
        db.session.add(new_request)
        db.session.commit()
        
        return f"✅ Запрос #{new_request.id} отправлен! Ожидайте подтверждения библиотекаря."
        
    except Exception as e:
        db.session.rollback()
        return f"Ошибка: {str(e)}", 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password', '')
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверный пароль')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    requests = BookRequest.query.order_by(BookRequest.request_date.desc()).all()
    return render_template('admin.html',
                         requests=requests,
                         current_status='all',
                         current_date='all',
                         search_query='',
                         custom_date='')

@app.route('/admin/assign-copy-ids/<int:request_id>', methods=['POST'])
@admin_required
def assign_copy_ids(request_id):
    """Привязка конкретных экземпляров (по QR-кодам) к запросу"""
    try:
        data = request.get_json()
        copy_codes_str = data.get('copy_codes', '').strip()
        
        book_request = BookRequest.query.get_or_404(request_id)
        
        if book_request.status != 'ожидание':
            return jsonify({'success': False, 'error': 'Запрос уже обработан'}), 400
        
        if not copy_codes_str:
            return jsonify({'success': False, 'error': 'Не указаны коды экземпляров'}), 400
        
        codes_list = [code.strip() for code in copy_codes_str.split(',') if code.strip()]
        
        if len(codes_list) != book_request.quantity:
            return jsonify({'success': False, 'error': f'Количество кодов ({len(codes_list)}) не совпадает с запрошенным ({book_request.quantity})'}), 400
        
        # Проверяем каждый код
        copies_to_assign = []
        for code in codes_list:
            copy = BookCopy.query.filter_by(copy_code=code, book_id=book_request.book_id).first()
            if not copy:
                return jsonify({'success': False, 'error': f'Экземпляр {code} не принадлежит этой книге'}), 400
            if not copy.is_available:
                return jsonify({'success': False, 'error': f'Экземпляр {code} уже выдан'}), 400
            copies_to_assign.append(copy)
        
        # Временно привязываем (но ещё не выдаём)
        for copy in copies_to_assign:
            copy.current_request_id = book_request.id
            copy.is_available = False
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Экземпляры успешно привязаны'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/confirm-issue/<int:request_id>', methods=['POST'])
@admin_required
def confirm_issue(request_id):
    try:
        book_request = BookRequest.query.get_or_404(request_id)
        
        if book_request.status != 'ожидание':
            return jsonify({'success': False, 'error': 'Запрос уже обработан'}), 400
        
        # Получаем запрошенные студентом коды
        codes_str = book_request.requested_copy_codes or ''
        if not codes_str:
            return jsonify({'success': False, 'error': 'У запроса нет прикреплённых экземпляров. Отсканируйте QR-коды заново.'}), 400
        
        codes_list = [c.strip() for c in codes_str.split(',') if c.strip()]
        if len(codes_list) != book_request.quantity:
            return jsonify({'success': False, 'error': f'Количество кодов ({len(codes_list)}) не совпадает с запросом ({book_request.quantity})'}), 400
        
        # Пытаемся зарезервировать каждый экземпляр
        reserved_copies = []
        conflicts = []
        for code in codes_list:
            copy = BookCopy.query.filter_by(copy_code=code, book_id=book_request.book_id).first()
            if not copy:
                conflicts.append(f"{code} (не найден)")
                continue
            if not copy.is_available:
                # Находим, кому выдан
                if copy.current_request_id:
                    conflict_request = BookRequest.query.get(copy.current_request_id)
                    student_name = conflict_request.student.full_name if conflict_request and conflict_request.student else "Неизвестно"
                    conflicts.append(f"{code} (выдан студенту {student_name})")
                else:
                    conflicts.append(f"{code} (уже занят)")
                continue
            reserved_copies.append(copy)
        
        # Если есть конфликты — не подтверждаем
        if conflicts:
            conflict_msg = "; ".join(conflicts)
            return jsonify({'success': False, 'error': f'Невозможно выдать: {conflict_msg}'}), 400
        
        # Всё ок — резервируем
        for copy in reserved_copies:
            copy.current_request_id = book_request.id
            copy.is_available = False
        
        book_request.status = 'выдано'
        book_request.issue_date = datetime.now()
        book_request.planned_return_date = datetime.now() + timedelta(days=14)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Выдача подтверждена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/mark-returned/<int:request_id>', methods=['POST'])
@admin_required
def mark_returned(request_id):
    try:
        book_request = BookRequest.query.get_or_404(request_id)
        
        if book_request.status != 'выдано':
            return jsonify({'success': False, 'error': 'Книга не была выдана'}), 400
        
        # Освобождаем все экземпляры
        copies = BookCopy.query.filter_by(current_request_id=book_request.id).all()
        for copy in copies:
            copy.is_available = True
            copy.current_request_id = None
        
        book_request.status = 'возвращено'
        book_request.actual_return_date = datetime.now()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Книга отмечена как возвращенная'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/reject-request/<int:request_id>', methods=['POST'])
@admin_required
def reject_request(request_id):
    try:
        book_request = BookRequest.query.get_or_404(request_id)
        
        if book_request.status != 'ожидание':
            return jsonify({'success': False, 'error': 'Запрос уже обработан'}), 400
        
        # Очищаем привязанные экземпляры (если были)
        BookCopy.query.filter_by(current_request_id=book_request.id).update({
            'current_request_id': None,
            'is_available': True
        })
        
        db.session.delete(book_request)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Запрос отклонён'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/check-status', methods=['GET', 'POST'])
def check_status():
    request_input = None
    if request.method == 'POST':
        request_input = request.form.get('request_id', '').strip()
    else:
        request_input = request.args.get('request_id', '').strip()
    
    if request_input:
        if request_input.startswith('#'):
            request_input = request_input[1:]
        
        book_request = BookRequest.query.filter_by(request_number=request_input).first()
        if not book_request:
            try:
                request_id_int = int(request_input)
                book_request = BookRequest.query.get(request_id_int)
            except ValueError:
                pass
        
        if book_request:
            return render_template('status_result.html', book_request=book_request)
        else:
            flash('Запрос не найден')
    
    return render_template('check_status.html')

@app.route('/admin/filter', methods=['GET'])
@admin_required
def admin_filter():
    date_filter = request.args.get('date', 'all')
    status_filter = request.args.get('status', 'all')
    search_query = request.args.get('search', '').strip()
    custom_date = request.args.get('custom_date', '')
    
    query = BookRequest.query
    
    if status_filter != 'all':
        query = query.filter(BookRequest.status == status_filter)
    
    today_date = datetime.now().date()
    if date_filter == 'today':
        query = query.filter(db.func.date(BookRequest.request_date) == today_date)
    elif date_filter == 'yesterday':
        yesterday_date = (datetime.now() - timedelta(days=1)).date()
        query = query.filter(db.func.date(BookRequest.request_date) == yesterday_date)
    elif date_filter == 'custom' and custom_date:
        try:
            custom_date_obj = datetime.strptime(custom_date, '%Y-%m-%d').date()
            query = query.filter(db.func.date(BookRequest.request_date) == custom_date_obj)
        except ValueError:
            pass
    
    if search_query:
        # Поиск по полным словам в ФИО студента
        all_requests = query.join(Student).all()
        
        # Фильтруем по полным словам
        filtered_requests = [r for r in all_requests if contains_full_word(r.student.full_name, search_query)]
        # Создаем новый запрос с отфильтрованными результатами
        request_ids = [r.id for r in filtered_requests]
        if request_ids:
            query = BookRequest.query.filter(BookRequest.id.in_(request_ids))
        else:
            query = BookRequest.query.filter(BookRequest.id == -1)  # Нет результатов
    
    requests = query.order_by(BookRequest.request_date.desc()).all()
    
    return render_template('admin.html',
                         requests=requests,
                         current_status=status_filter,
                         current_date=date_filter,
                         search_query=search_query,
                         custom_date=custom_date)

@app.route('/get-book-by-copy-code/<copy_code>')
def get_book_by_copy_code(copy_code):
    copy = BookCopy.query.filter_by(copy_code=copy_code).first()
    if copy and copy.book:
        return jsonify({'book_id': copy.book.id})
    return jsonify({'error': 'Not found'}), 404

@app.route('/admin/scan-return/<int:request_id>', methods=['POST'])
@admin_required
def scan_return(request_id):
    try:
        data = request.get_json()
        scanned_codes_str = data.get('copy_codes', '').strip()
        if not scanned_codes_str:
            return jsonify({'success': False, 'error': 'Не отсканированы коды экземпляров'}), 400
        
        scanned_codes = [c.strip() for c in scanned_codes_str.split(',') if c.strip()]
        
        book_request = BookRequest.query.get_or_404(request_id)
        
        if book_request.status != 'выдано':
            return jsonify({'success': False, 'error': 'Запрос не в статусе "выдано"'}), 400
        
        # Получаем коды, которые были выданы по этому запросу
        issued_codes_str = book_request.requested_copy_codes or book_request.attached_copy_codes or ''
        if not issued_codes_str:
            return jsonify({'success': False, 'error': 'У запроса нет записанных кодов экземпляров'}), 400
        
        issued_codes = [c.strip() for c in issued_codes_str.split(',') if c.strip()]
        
        # Сравниваем множества: количество и сами коды должны совпадать
        if set(scanned_codes) != set(issued_codes):
            return jsonify({
                'success': False, 
                'error': 'Отсканированные коды не совпадают с выданными по этому запросу'
            }), 400
        
        # Всё совпадает — отмечаем возврат
        book_request.status = 'возвращено'
        book_request.actual_return_date = datetime.now()
        
        # Освобождаем экземпляры
        BookCopy.query.filter(BookCopy.current_request_id == book_request.id).update({
            'current_request_id': None,
            'is_available': True
        })
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Возврат подтверждён'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/search-books')
def search_books():
    query = request.args.get('q', '').strip()
    group_id = request.args.get('group_id', type=int)
    
    if not group_id:
        return jsonify([])
    
    group = Group.query.get(group_id)
    if not group:
        return jsonify([])
    
    # Выбираем книги только по языку и курсу (без фильтра по доступности)
    # Включаем книги для языка группы и книги для обеих языков ("both")
    books_query = Book.query.filter(
        or_(
            Book.language == group.language,
            Book.language == 'both'
        ),
        Book.course == group.course
    )
    
    # Загружаем все подходящие книги (без фильтра по запросу пока)
    books = books_query.all()
    
    # Фильтруем книги по запросу (если есть) и по доступности
    available_books = []
    for book in books:
        # Если есть запрос, проверяем наличие полного слова в названии или авторе
        if query:
            name_match = contains_full_word(book.name, query)
            author_match = contains_full_word(book.author, query)
            if not (name_match or author_match):
                continue
        
        # Проверяем доступность
        if book.available_quantity > 0:
            available_books.append({
                'id': book.id,
                'name': book.name,
                'author': book.author,
                'available': book.available_quantity
            })
    
    return jsonify(available_books)

if __name__ == '__main__':
    app.run(debug=True)