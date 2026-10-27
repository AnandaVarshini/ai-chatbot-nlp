from app.database import SessionLocal, Conversation

db = SessionLocal()
deleted = db.query(Conversation).delete()
db.commit()

print(f"✅ Deleted {deleted} conversations")

db.close()