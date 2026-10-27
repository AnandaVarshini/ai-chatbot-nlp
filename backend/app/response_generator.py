from fuzzywuzzy import fuzz
from sqlalchemy.orm import Session
from .database import KnowledgeBase, Conversation
from .nlp_processor import NLPProcessor
from .intent_recognition import IntentRecognizer
from .external_search import ExternalSearch
from .math_handler import MathHandler
from .feature_fusion import get_fusion

STOPWORDS = {
    "what", "which", "who", "whom", "whose", "when", "where", "why", "how",
    "is", "are", "was", "were", "be", "been", "being", "am",
    "the", "a", "an", "of", "in", "on", "at", "to", "for", "with", "by",
    "and", "or", "but", "not", "no", "yes",
    "do", "does", "did", "done", "doing",
    "have", "has", "had", "having",
    "will", "would", "shall", "should", "can", "could", "may", "might", "must",
    "tell", "about", "give", "show", "explain", "define", "meaning",
    "please", "kindly", "some", "any", "all", "this", "that", "these", "those",
    "it", "its", "me", "my", "you", "your", "we", "our", "they", "their",
    "there", "here", "also", "very", "just", "only", "so", "than", "then",
    "into", "from", "out", "up", "down", "over", "under", "again",
    "more", "most", "much", "many", "few", "little", "own", "same",
    "other", "another", "such", "nor", "too", "as", "if", "while", "because",
    "get", "got", "getting", "use", "used", "using", "make", "made", "making"
}


class ResponseGenerator:
    def __init__(self):
        self.nlp_processor = NLPProcessor()
        self.intent_recognizer = IntentRecognizer()
        self.external_search = ExternalSearch()
        self.math_handler = MathHandler()

    def _get_topic_words(self, text: str) -> set:
        words = set()
        for w in text.lower().split():
            w = w.strip(".,!?;:'\"()[]{}")
            if len(w) >= 2 and w not in STOPWORDS:
                words.add(w)
        return words

    def search_knowledge_base(self, db: Session, query: str, normalized_query: str):
        all_entries = db.query(KnowledgeBase).all()
        
        if not all_entries:
            return None, 0

        best_match = None
        best_score = 0
        query_lower = query.lower()

        for entry in all_entries:
            # 1. Check if the user query explicitly contains any of the entry's keywords
            keyword_match = False
            if entry.keywords:
                for kw in entry.keywords.lower().split(','):
                    kw = kw.strip()
                    if len(kw) > 2 and kw in query_lower:
                        keyword_match = True
                        break
            
            # 2. If no keywords match, SKIP this entry completely. 
            if not keyword_match:
                continue

            # 3. If keywords DO match, calculate the final score
            entry_normalized = self.nlp_processor.normalize_text(entry.question)
            fuzzy_score = fuzz.ratio(normalized_query, entry_normalized)
            
            # Combine score (keyword match gives it a huge boost)
            score = 70 + (fuzzy_score * 0.3) 

            if score > best_score:
                best_score = score
                best_match = entry

        # Only return if a keyword match was found
        if best_score >= 70:
            return best_match, best_score

        return None, best_score

    def semantic_search(self, db: Session, query: str, threshold: float = 0.55):
        """
        Uses feature fusion (BOW + TF-IDF + Word2Vec + SBERT) to find
        the best-matching KB entry when keyword search fails.
        """
        fusion = get_fusion()
        if fusion is None or not getattr(fusion, "fitted", False):
            return None, 0.0

        all_entries = db.query(KnowledgeBase).all()
        if not all_entries:
            return None, 0.0

        best_entry = None
        best_score = 0.0

        for entry in all_entries:
            if not entry.question:
                continue
            try:
                score = fusion.similarity(query, entry.question, use_sbert=True)
            except Exception as e:
                print(f"[semantic_search] similarity error: {e}")
                continue
            if score > best_score:
                best_score = score
                best_entry = entry

        if best_score >= threshold:
            print(f"[semantic_search] matched '{best_entry.question}' (score: {best_score:.3f})")
            return best_entry, best_score

        return None, best_score

    def generate_response(self, db: Session, query: str, user_id: int = None, is_online: bool = True, session_id: str = None):
        normalized_query = self.nlp_processor.normalize_text(query)
        intent, confidence = self.intent_recognizer.recognize_intent(query)

        # 🆕 BYPASS: Force general questions to skip local DB and go to Web or Fusion
        force_external = query.lower().startswith((
            "how does", "how do", "what is", "what are", "who is", "tell me"
        ))

        source = "local"
        response = ""
        is_answered = False

        # STEP 0: Try math handler FIRST
        math_result = self.math_handler.solve(query)

        if math_result:
            response = math_result["answer"]
            is_answered = True
            source = "math"
            print(f"Math solved: '{query}'")

        else:
            # STEP 1: Try local knowledge base (keyword-based)
            knowledge_entry, local_score = self.search_knowledge_base(db, query, normalized_query)

            # 🆕 Bypass DB for general questions to prevent false matches
            if knowledge_entry and not force_external:
                response = knowledge_entry.answer
                is_answered = True
                source = "local"
                print(f"Local match: '{query}' -> '{knowledge_entry.question}' (score: {local_score:.1f})")

            else:
                # STEP 1.5: Semantic search via Feature Fusion
                semantic_entry, semantic_score = self.semantic_search(db, query)

                # 🆕 Also bypass Fusion for general questions
                if semantic_entry and not force_external:
                    response = semantic_entry.answer
                    is_answered = True
                    source = "semantic"
                    print(f"Semantic match: '{query}' -> '{semantic_entry.question}' (score: {semantic_score:.3f})")

                # STEP 2: External search if online
                elif is_online:
                    print(f"Local miss for '{query}' (best score: {local_score:.1f}) -- searching web...")

                    if intent == "Greeting":
                        response = "Hello! How can I help you today? Ask me anything!"
                        is_answered = True
                        source = "local"
                    elif intent == "Help":
                        response = "I can help with definitions, examples, and general knowledge.\nTry asking 'What is AI?' or 'What is quantum physics?'"
                        is_answered = True
                        source = "local"
                    else:
                        external_result = self.external_search.search(query)

                        if external_result:
                            answer = external_result.get("answer", "")
                            source_name = external_result.get("source", "Web")
                            url = external_result.get("url", "")

                            response = f"**{source_name}**\n\n{answer}"
                            if url:
                                response += f"\n\n{url}"

                            is_answered = True
                            source = "external"
                        else:
                            response = "I couldn't find an answer. Please try rephrasing your question."
                            is_answered = False
                            source = "none"

                # STEP 3: Offline
                else:
                    response = (
                        "You're offline and this question isn't in my local knowledge base.\n\n"
                        "Connect to the internet to search the web for this topic."
                    )
                    is_answered = False
                    source = "offline"

        # STEP 4: Save conversation
        try:
            saved_response = response[:1000] if len(response) > 1000 else response
            conversation = Conversation(
                user_id=user_id,
                query=query,
                intent=intent,
                response=saved_response,
                is_answered=1 if is_answered else 0,
                session_id=session_id,
            )
            db.add(conversation)
            db.commit()
        except Exception as e:
            print(f"DB save error: {e}")
            db.rollback()

        return {
            "query": query,
            "intent": intent,
            "response": response,
            "is_answered": is_answered,
            "source": source
        }