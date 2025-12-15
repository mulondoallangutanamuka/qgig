import sys
sys.path.insert(0, '.')
from app.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
print("Dropping notifications table...")
db.execute(text("DROP TABLE IF EXISTS notifications"))
db.commit()
print("Done!")
db.close()
