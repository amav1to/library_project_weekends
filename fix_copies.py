# fix_copies.py
from app import app, db
from models import BookCopy, BookRequest

with app.app_context():
    print("Очищаем некорректные привязки экземпляров...")
    
    # Находим все экземпляры, которые "заняты", но запроса нет или он не "выдано"
    copies = BookCopy.query.filter(BookCopy.current_request_id.isnot(None)).all()
    
    cleaned = 0
    for copy in copies:
        request = BookRequest.query.get(copy.current_request_id)
        if not request or request.status != 'выдано':
            print(f"Очищаем {copy.copy_code}: был привязан к запросу #{copy.current_request_id} (статус: {request.status if request else 'удалён'})")
            copy.current_request_id = None
            copy.is_available = True
            cleaned += 1
    
    db.session.commit()
    print(f"Готово! Очищено {cleaned} экземпляров.")