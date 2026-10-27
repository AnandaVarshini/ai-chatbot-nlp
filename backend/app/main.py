from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
import os
import uuid
from sqlalchemy import func as sql_func

from .database import SessionLocal, init_knowledge_base, User, Conversation
from .models import (
    UserCreate, UserLogin, UserResponse, QueryRequest,
    QueryResponse, AnalyticsResponse, TokenResponse, ConversationHistory
)
from .auth import (
    authenticate_user, create_access_token, create_user,
    get_user_by_username, get_user_by_email, get_user_by_id
)
from .response_generator import ResponseGenerator
from .analytics import Analytics
from .feature_fusion import init_fusion, get_fusion

app = FastAPI(title="AI Chatbot using NLP", version="2.0.0")


def _init_feature_fusion():
    """Load KB questions and initialize feature fusion at startup."""
    db = SessionLocal()
    try:
        from .database import KnowledgeBase
        entries = db.query(KnowledgeBase).all()
        questions = [
            getattr(e, "question", None)
            for e in entries
            if getattr(e, "question", None)
        ]
    except Exception as e:
        print(f"[main] Fusion init failed: {e}")
        questions = []
    finally:
        db.close()

    if questions:
        init_fusion(questions)
        print(f"[main] Feature fusion initialized on {len(questions)} entries.")
    else:
        print("[main] No KB entries found — fusion skipped.")


@app.on_event("startup")
async def _startup_event():
    _init_feature_fusion()


FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

# CORS - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize knowledge base
init_knowledge_base()

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

response_generator = ResponseGenerator()
analytics = Analytics()

# ============================================================
# AUTH ROUTES
# ============================================================

@app.post("/api/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    print(f"📝 Registration attempt: {user.username}")

    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already registered")

    if get_user_by_email(db, user.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        new_user = create_user(db, user.username, user.email, user.password)
        print(f"✅ User created: {new_user.username}")

        access_token = create_access_token(data={"sub": new_user.username})

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_id": new_user.id,
            "username": new_user.username,
            "email": new_user.email
        }
    except Exception as e:
        print(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    print(f"🔐 Login attempt: {user.username}")

    db_user = authenticate_user(db, user.username, user.password)
    if not db_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token(data={"sub": db_user.username})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": db_user.id,
        "username": db_user.username,
        "email": db_user.email
    }


@app.get("/api/user/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get user details"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    total = db.query(Conversation).filter(Conversation.user_id == user_id).count()
    answered = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.is_answered == 1
    ).count()

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "created_at": user.created_at,
        "total_queries": total,
        "answered_queries": answered
    }

# ============================================================
# CHAT ROUTES
# ============================================================

@app.post("/api/chat")
def chat(request: QueryRequest, db: Session = Depends(get_db)):
    """Send a query to the chatbot (without authentication)"""
    result = response_generator.generate_response(
        db,
        request.query,
        is_online=True
    )
    return result


@app.post("/api/chat/{user_id}")
def chat_with_user(user_id: int, request: QueryRequest, db: Session = Depends(get_db)):
    """Send a query with user authentication"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    result = response_generator.generate_response(
        db,
        request.query,
        user_id,
        is_online=True,
        session_id=request.session_id,        # ← NEW
    )
    return result
# ============================================================
# HISTORY ROUTES
# ============================================================

@app.get("/api/history/{user_id}")
def get_user_history(user_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """Get user's chat history"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    conversations = db.query(Conversation).filter(
        Conversation.user_id == user_id
    ).order_by(Conversation.timestamp.desc()).limit(limit).all()

    return [
        {
            "id": c.id,
            "query": c.query,
            "intent": c.intent,
            "response": c.response,
            "is_answered": bool(c.is_answered),
            "timestamp": c.timestamp
        }
        for c in conversations
    ]


@app.delete("/api/history/{user_id}/{conversation_id}")
def delete_conversation(user_id: int, conversation_id: int, db: Session = Depends(get_db)):
    """Delete a specific conversation"""
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    ).first()

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db.delete(conversation)
    db.commit()
    return {"message": "Conversation deleted successfully"}


@app.delete("/api/history/{user_id}")
def clear_history(user_id: int, db: Session = Depends(get_db)):
    """Clear all history for a user"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.query(Conversation).filter(Conversation.user_id == user_id).delete()
    db.commit()
    return {"message": "History cleared successfully"}

# ============================================================
# ANALYTICS ROUTES
# ============================================================

@app.get("/api/analytics")
def get_analytics(db: Session = Depends(get_db)):
    """Get overall chat analytics"""
    return analytics.get_stats(db)


@app.get("/api/analytics/{user_id}")
def get_user_analytics(user_id: int, db: Session = Depends(get_db)):
    """Get user-specific analytics"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return analytics.get_user_stats(db, user_id)

# ============================================================
# KNOWLEDGE BASE ROUTES
# ============================================================

@app.get("/api/knowledge-base")
def get_knowledge_base(db: Session = Depends(get_db)):
    """Get all knowledge base entries"""
    from .database import KnowledgeBase
    entries = db.query(KnowledgeBase).all()
    return [
        {
            "id": e.id,
            "question": e.question,
            "answer": e.answer,
            "category": e.category
        }
        for e in entries
    ]

# ============================================================
# OFFLINE MODE ROUTES
# ============================================================

@app.get("/api/offline/data")
def get_offline_data(db: Session = Depends(get_db)):
    """Get all data needed for offline mode"""
    from .database import KnowledgeBase
    entries = db.query(KnowledgeBase).all()
    return {
        "knowledge_base": [
            {
                "question": e.question,
                "answer": e.answer,
                "category": e.category,
                "keywords": e.keywords
            }
            for e in entries
        ],
        "version": "2.0.0",
        "last_updated": datetime.utcnow().isoformat()
    }
# ============================================================
# SESSION / CHAT HISTORY ROUTES
# ============================================================

@app.post("/api/sessions/new")
def create_new_session():
    """Generate a new session ID for a chat."""
    return {"session_id": str(uuid.uuid4())}


@app.get("/api/sessions/{user_id}")
def get_sessions(user_id: int, db: Session = Depends(get_db)):
    """List all chat sessions for a user (grouped by session_id)."""
    rows = db.query(
        Conversation.session_id,
        sql_func.min(Conversation.query).label("first_query"),
        sql_func.min(Conversation.timestamp).label("started_at"),
        sql_func.max(Conversation.timestamp).label("last_at"),
        sql_func.count(Conversation.id).label("count"),
    ).filter(
        Conversation.user_id == user_id,
        Conversation.session_id.isnot(None),
    ).group_by(Conversation.session_id).order_by(
        sql_func.max(Conversation.timestamp).desc()
    ).all()

    return [
        {
            "session_id": r.session_id,
            "title": (r.first_query or "New chat")[:40],
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "last_at": r.last_at.isoformat() if r.last_at else None,
            "message_count": r.count,
        }
        for r in rows
    ]


@app.get("/api/sessions/{user_id}/{session_id}")
def get_session_messages(user_id: int, session_id: str, db: Session = Depends(get_db)):
    """Get all messages in a session, ordered oldest → newest."""
    convs = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.session_id == session_id,
    ).order_by(Conversation.timestamp.asc()).all()

    return [
        {
            "id": c.id,
            "query": c.query,
            "response": c.response,
            "intent": c.intent,
            "is_answered": bool(c.is_answered),
            "timestamp": c.timestamp,
        }
        for c in convs
    ]


@app.delete("/api/sessions/{user_id}/{session_id}")
def delete_session(user_id: int, session_id: str, db: Session = Depends(get_db)):
    """Delete an entire session."""
    count = db.query(Conversation).filter(
        Conversation.user_id == user_id,
        Conversation.session_id == session_id,
    ).delete()
    db.commit()
    return {"message": "Session deleted", "deleted_messages": count}
# ============================================================
# ROOT
# ============================================================

@app.get("/api/health")
def health_check():
    return {"message": "AI Chatbot using NLP API is running!", "version": "2.0.0"}


# Serve frontend (must be the LAST mount)
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")