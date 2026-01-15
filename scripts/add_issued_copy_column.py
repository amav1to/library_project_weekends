from app import app
from models import db
from sqlalchemy import text

with app.app_context():
    try:
        db.session.execute(text("ALTER TABLE book_requests ADD COLUMN issued_copy_codes VARCHAR(500)"))
        db.session.commit()
        print('Column added successfully')
    except Exception as e:
        print('Error:', e)
