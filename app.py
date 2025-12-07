from flask import Flask, render_template, request, jsonify, redirect, url_for
from config import Config
from models import db, Group, Book, Student, BookRequest
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from datetime import datetime, timedelta

# Простой пароль для библиотекаря (позже можно сделать базу пользователей)
ADMIN_PASSWORD = "library123"

def admin_required(f):
    """Декоратор для проверки пароля админа"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Проверяем пароль из сессии или формы
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Создаем приложение Flask
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = 'ваш-секретный-ключ-для-сессий-12345'  # Любая строка

# Инициализируем базу данных с приложением
db.init_app(app)

ADMIN_PASSWORD = "library123"

# Создаем все таблицы в базе данных (если их еще нет)
with app.app_context():
    db.create_all()
    print("База данных создана!")

@app.route('/')
def index():
    """Главная страница - форма для студентов"""
    return render_template('index.html')

@app.route('/get-groups')
def get_groups():
    """Возвращает список групп для выпадающего меню"""
    groups = Group.query.all()
    groups_list = [{'id': g.id, 'name': g.name} for g in groups]
    return jsonify(groups_list)

@app.route('/get-books/<int:group_id>')
def get_books(group_id):
    """Возвращает книги для выбранной группы (по языку и курсу)"""
    group = Group.query.get_or_404(group_id)
    
    # Фильтруем книги по языку группы и курсу
    books = Book.query.filter_by(
        language=group.language,
        course=group.course
    ).all()
    
    books_list = []
    for book in books:
        # Показываем только книги, которые доступны
        if book.available_quantity > 0:
            books_list.append({
                'id': book.id,
                'name': f"{book.name} ({book.author}, {book.year})",
                'available': book.available_quantity
            })
    
    return jsonify(books_list)

@app.route('/search-students')
def search_students():
    """Поиск студентов по ФИО с фильтрацией по группе"""
    query = request.args.get('q', '').strip()
    group_id = request.args.get('group_id', '')
    
    # Если пустой запрос - возвращаем пустой список
    if not query:
        return jsonify([])
    
    # Базовый запрос
    students_query = Student.query
    
    # Фильтр по группе, если указана
    if group_id and group_id != 'null' and group_id != '':
        students_query = students_query.filter_by(group_id=int(group_id))
    
    # ПРОСТОЙ поиск: ищем подстроку в любом месте ФИО (регистронезависимый)
    students = students_query.filter(
        Student.full_name.ilike(f'%{query}%')
    ).limit(20).all()
    
    students_list = []
    for student in students:
        students_list.append({
            'id': student.id,
            'name': student.full_name,
            'group': student.group.name if student.group else 'Нет группы'
        })
    
    return jsonify(students_list)

@app.route('/get-students/<int:group_id>')
def get_students(group_id):
    """Получить всех студентов группы (без поиска)"""
    students = Student.query.filter_by(group_id=group_id).all()
    
    students_list = []
    for student in students:
        students_list.append({
            'id': student.id,
            'name': student.full_name
        })
    
    return jsonify(students_list)

@app.route('/request-book', methods=['POST'])
def request_book():
    """Обработка формы заявки"""
    try:
        # Получаем данные из формы
        student_id = request.form.get('student_id')
        book_id = request.form.get('book_id')
        quantity = int(request.form.get('quantity', 1))
        
        # 1. Проверяем, что студент существует
        student = Student.query.get(student_id)
        if not student:
            return "Ошибка: Студент не найден", 400
        
        # 2. Проверяем, что книга существует
        book = Book.query.get(book_id)
        if not book:
            return "Ошибка: Книга не найдена", 400
        
        # 3. Проверяем количество
        if quantity <= 0:
            return "Ошибка: Количество должно быть больше 0", 400
        
        if quantity > book.available_quantity:
            return f"Ошибка: Доступно только {book.available_quantity} экземпляров", 400
        
        # 4. Проверяем, что книга подходит для группы студента
        student_group = student.group
        if not student_group:
            return "Ошибка: У студента нет группы", 400
        
        if book.language != student_group.language or book.course != student_group.course:
            return "Ошибка: Эта книга не предназначена для вашей группы", 400
        
        # 5. Создаем запись в журнале
        new_request = BookRequest(
            student_id=student_id,
            book_id=book_id,
            quantity=quantity,
            status='ожидание',
            request_date=datetime.now()
        )
        
        db.session.add(new_request)
        db.session.commit()
        
        return "✅ Запрос отправлен! Ожидайте подтверждения библиотекаря."
        
    except ValueError:
        return "Ошибка: Неверное количество", 400
    except Exception as e:
        db.session.rollback()
        return f"Ошибка сервера: {str(e)}", 500

@app.route('/find-student-by-name', methods=['POST'])
def find_student_by_name():
    """Найти студента по точному ФИО и группе"""
    data = request.get_json()
    full_name = data.get('full_name', '').strip()
    group_id = data.get('group_id')
    
    if not full_name or not group_id:
        return jsonify({'error': 'Не указано ФИО или группа'}), 400
    
    student = Student.query.filter_by(
        full_name=full_name,
        group_id=int(group_id)
    ).first()
    
    if student:
        return jsonify({
            'id': student.id,
            'name': student.full_name
        })
    else:
        return jsonify({'error': 'Студент не найден'}), 404
    
# Добавляем секретный ключ для сессий в Config (config.py)
# Или прямо в app.py:
app.secret_key = 'ваш-секретный-ключ-для-сессий'

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Страница входа для библиотекаря"""
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        # Простая проверка пароля
        if password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Неверный пароль')
            return redirect(url_for('admin_login'))
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Выход из админки"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    """Главная страница админ-панели"""
    # Получаем все запросы из БД
    requests = BookRequest.query.order_by(BookRequest.request_date.desc()).all()
    
    # Передаем данные в шаблон
    return render_template('admin.html', requests=requests)

@app.route('/admin/confirm-issue/<int:request_id>', methods=['POST'])
@admin_required
def confirm_issue(request_id):
    """Подтвердить выдачу книги"""
    try:
        book_request = BookRequest.query.get_or_404(request_id)
        
        # Проверяем, что статус "ожидание"
        if book_request.status != 'ожидание':
            return jsonify({'success': False, 'error': 'Запрос уже обработан'}), 400
        
        # Проверяем, что книга еще доступна
        book = Book.query.get(book_request.book_id)
        if not book:
            return jsonify({'success': False, 'error': 'Книга не найдена'}), 404
            
        if book_request.quantity > book.available_quantity:
            return jsonify({'success': False, 'error': f'Недостаточно книг. Доступно: {book.available_quantity}'}), 400
        
        # Обновляем статус и дату выдачи
        book_request.status = 'выдано'
        book_request.issue_date = datetime.now()
        book_request.planned_return_date = datetime.now() + timedelta(minutes=90)
        
        # Уменьшаем количество доступных книг
        book.available_quantity -= book_request.quantity
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Выдача подтверждена'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/mark-returned/<int:request_id>', methods=['POST'])
@admin_required
def mark_returned(request_id):
    """Отметить книгу как возвращенную"""
    try:
        book_request = BookRequest.query.get_or_404(request_id)
        
        # Проверяем, что статус "выдано"
        if book_request.status != 'выдано':
            return jsonify({'success': False, 'error': 'Книга не была выдана'}), 400
        
        # Обновляем статус и дату возврата
        book_request.status = 'возвращено'
        book_request.actual_return_date = datetime.now()
        
        # Возвращаем книги в доступные
        book = Book.query.get(book_request.book_id)
        if book:
            book.available_quantity += book_request.quantity
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Книга отмечена как возвращенная'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/reject-request/<int:request_id>', methods=['POST'])
@admin_required
def reject_request(request_id):
    """Отклонить запрос"""
    try:
        book_request = BookRequest.query.get_or_404(request_id)
        
        # Проверяем, что статус "ожидание"
        if book_request.status != 'ожидание':
            return jsonify({'success': False, 'error': 'Запрос уже обработан'}), 400
        
        # Удаляем запрос (или можно изменить статус на "отклонено")
        db.session.delete(book_request)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Запрос отклонен'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)