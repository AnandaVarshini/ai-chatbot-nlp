from sqlalchemy.orm import Session
from .database import Conversation
from collections import Counter

class Analytics:
    def __init__(self):
        pass
    
    def get_stats(self, db: Session):
        """Get overall chat statistics"""
        total_queries = db.query(Conversation).count()
        answered_queries = db.query(Conversation).filter(Conversation.is_answered == 1).count()
        unanswered_queries = total_queries - answered_queries
        
        all_intents = db.query(Conversation.intent).all()
        intent_counts = Counter([i[0] for i in all_intents if i[0]])
        top_intents = dict(intent_counts.most_common(5))
        
        recent = db.query(Conversation).order_by(Conversation.timestamp.desc()).limit(10).all()
        recent_conversations = [
            {
                "query": c.query,
                "intent": c.intent,
                "response": c.response[:100] + "..." if len(c.response) > 100 else c.response,
                "timestamp": c.timestamp.strftime("%Y-%m-%d %H:%M")
            }
            for c in recent
        ]
        
        return {
            "total_queries": total_queries,
            "answered_queries": answered_queries,
            "unanswered_queries": unanswered_queries,
            "top_intents": top_intents,
            "recent_conversations": recent_conversations
        }
    
    def get_user_stats(self, db: Session, user_id: int):
        """Get user-specific statistics"""
        total_queries = db.query(Conversation).filter(Conversation.user_id == user_id).count()
        answered_queries = db.query(Conversation).filter(
            Conversation.user_id == user_id,
            Conversation.is_answered == 1
        ).count()
        unanswered_queries = total_queries - answered_queries
        
        all_intents = db.query(Conversation.intent).filter(
            Conversation.user_id == user_id
        ).all()
        intent_counts = Counter([i[0] for i in all_intents if i[0]])
        top_intents = dict(intent_counts.most_common(5))
        
        recent = db.query(Conversation).filter(
            Conversation.user_id == user_id
        ).order_by(Conversation.timestamp.desc()).limit(10).all()
        recent_conversations = [
            {
                "query": c.query,
                "intent": c.intent,
                "response": c.response[:100] + "..." if len(c.response) > 100 else c.response,
                "timestamp": c.timestamp.strftime("%Y-%m-%d %H:%M")
            }
            for c in recent
        ]
        
        return {
            "total_queries": total_queries,
            "answered_queries": answered_queries,
            "unanswered_queries": unanswered_queries,
            "top_intents": top_intents,
            "recent_conversations": recent_conversations
        }