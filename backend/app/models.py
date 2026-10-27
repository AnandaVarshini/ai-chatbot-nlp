from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime
    total_queries: int = 0
    answered_queries: int = 0

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    query: str
    intent: str
    response: str
    is_answered: bool

class AnalyticsResponse(BaseModel):
    total_queries: int
    answered_queries: int
    unanswered_queries: int
    top_intents: dict
    recent_conversations: list

# 🆕 ADD THESE TWO MODELS
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str
    email: str

class ConversationHistory(BaseModel):
    id: int
    query: str
    intent: str
    response: str
    is_answered: bool
    timestamp: datetime