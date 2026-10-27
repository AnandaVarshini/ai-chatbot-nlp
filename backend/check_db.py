from app.database import SessionLocal, Conversation

db = SessionLocal()
conversations = db.query(Conversation).all()

print(f"Total conversations: {len(conversations)}")
print("-" * 50)

for c in conversations:
    print(f"ID: {c.id}, User: {c.user_id}, Query: {c.query[:30]}")

db.close()