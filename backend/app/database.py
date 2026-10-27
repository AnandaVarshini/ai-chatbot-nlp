from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import csv
import os

# Get the absolute path to the backend folder
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATA_DIR = os.path.join(BACKEND_DIR, 'data')

# Create data directory
os.makedirs(DATA_DIR, exist_ok=True)

# Database file with absolute path
DB_PATH = os.path.join(DATA_DIR, 'chatbot.db')
DATABASE_URL = f"sqlite:///{DB_PATH.replace(os.sep, '/')}"

print(f"Database path: {DATABASE_URL}")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    conversations = relationship("Conversation", back_populates="user")

class KnowledgeBase(Base):
    __tablename__ = "knowledge_base"
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    category = Column(String, index=True)
    keywords = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    query = Column(Text, nullable=False)
    intent = Column(String)
    response = Column(Text)
    is_answered = Column(Integer, default=0)
    timestamp = Column(DateTime, default=datetime.utcnow)
    session_id = Column(String, nullable=True, index=True)    # ← NEW
    user = relationship("User", back_populates="conversations")

# Create tables
Base.metadata.create_all(bind=engine)


def _candidate_dataset_paths():
    """Return likely dataset locations for the provided CSE QA CSV file."""
    return [
        r"c:\Users\ANANDA VARSHINI\AppData\Local\Packages\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\LocalState\sessions\ED8FD0A3ABA142AE333E7042A6636AB1F924DBF2\transfers\2026-43\CSE_QA_Dataset.csv",
        os.path.join(BACKEND_DIR, "data", "CSE_QA_Dataset.csv"),
        os.path.join(os.path.dirname(BACKEND_DIR), "data", "CSE_QA_Dataset.csv"),
        os.path.join(os.path.dirname(BACKEND_DIR), "CSE_QA_Dataset.csv"),
    ]


def import_csv_knowledge_base(db, csv_path=None):
    """Import the CSE QA CSV dataset into the knowledge base if it exists."""
    if csv_path is None:
        csv_path = next((p for p in _candidate_dataset_paths() if os.path.exists(p)), None)

    if not csv_path or not os.path.exists(csv_path):
        print(f"[dataset] No CSV knowledge base file found in expected locations.")
        return 0

    added = 0
    existing_questions = {
        (question or "").strip().lower()
        for (question,) in db.query(KnowledgeBase.question).all()
        if question and question.strip()
    }

    with open(csv_path, newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        for row in reader:
            question = (row.get("Question") or row.get("question") or "").strip()
            answer = (row.get("Answer") or row.get("answer") or "").strip()
            if not question or not answer:
                continue
            if question.lower() in existing_questions:
                continue

            category = (row.get("Topic") or row.get("category") or "Dataset").strip()
            keywords = (row.get("Keyword") or row.get("keywords") or "").strip()
            db.add(KnowledgeBase(
                question=question,
                answer=answer,
                category=category,
                keywords=keywords,
            ))
            existing_questions.add(question.lower())
            added += 1

    if added:
        db.commit()
        print(f"✅ Imported {added} rows from dataset: {csv_path}")
    return added


def init_knowledge_base(load_csv_dataset=True):
    db = SessionLocal()
    try:
        if db.query(KnowledgeBase).count() == 0:
            sample_data = [
                # ===== DEFINITIONS =====
                {
                    "question": "What is artificial intelligence?",
                    "answer": "Artificial Intelligence (AI) is the simulation of human intelligence processes by machines, especially computer systems. It includes learning, reasoning, and self-correction.",
                    "category": "Definition",
                    "keywords": "AI, intelligence"
                },
                {
                    "question": "What is AI?",
                    "answer": "AI stands for Artificial Intelligence. It is the simulation of human intelligence processes by machines, especially computer systems.",
                    "category": "Definition",
                    "keywords": "AI, artificial intelligence"
                },
                {
                    "question": "What is machine learning?",
                    "answer": "Machine Learning is a subset of AI that enables systems to learn and improve from experience without explicit programming. It uses algorithms to find patterns in data.",
                    "category": "Definition",
                    "keywords": "ML, learning"
                },
                {
                    "question": "What is ML?",
                    "answer": "ML stands for Machine Learning. It is a subset of AI that enables systems to learn and improve from experience without explicit programming.",
                    "category": "Definition",
                    "keywords": "ML, machine learning"
                },
                {
                    "question": "What is natural language processing?",
                    "answer": "Natural Language Processing (NLP) is a branch of AI that helps computers understand, interpret, and respond to human language in a valuable way.",
                    "category": "Definition",
                    "keywords": "NLP, language"
                },
                {
                    "question": "What is NLP?",
                    "answer": "NLP stands for Natural Language Processing. It is a branch of AI that helps computers understand, interpret, and respond to human language in a valuable way.",
                    "category": "Definition",
                    "keywords": "NLP, natural language processing"
                },
                {
                    "question": "What is Python?",
                    "answer": "Python is a high-level, interpreted programming language known for its simplicity and readability. It's widely used in web development, data science, and AI.",
                    "category": "Definition",
                    "keywords": "Python, programming"
                },
                {
                    "question": "What is a database?",
                    "answer": "A database is an organized collection of structured information or data, typically stored electronically in a computer system.",
                    "category": "Definition",
                    "keywords": "database, SQL"
                },
                {
                    "question": "What is deep learning?",
                    "answer": "Deep Learning is a subset of machine learning using neural networks with multiple layers to learn from data. It powers technologies like self-driving cars and voice assistants.",
                    "category": "Definition",
                    "keywords": "deep learning, neural networks"
                },
                
                # ===== EXAMPLES =====
                {
                    "question": "Give an example of supervised learning",
                    "answer": "Example: Email spam detection. The model is trained on labeled emails (spam/not spam) to classify new incoming emails as spam or legitimate.",
                    "category": "Example",
                    "keywords": "supervised, spam"
                },
                {
                    "question": "Give an example of unsupervised learning",
                    "answer": "Example: Customer segmentation in marketing. The algorithm groups customers with similar purchase patterns without predefined labels.",
                    "category": "Example",
                    "keywords": "unsupervised, clustering"
                },
                
                # ===== REAL-WORLD EXAMPLES =====
                {
                    "question": "Give a real-world example of machine learning",
                    "answer": "🌟 REAL-WORLD ML EXAMPLES:\n\n1. **Netflix Recommendations** - ML analyzes your viewing history to suggest movies you might like.\n\n2. **Google Maps** - Uses ML to predict traffic and suggest fastest routes.\n\n3. **Amazon Product Suggestions** - ML recommends products based on your browsing history.\n\n4. **Fraud Detection** - Banks use ML to detect unusual transactions and prevent fraud.\n\n5. **Email Spam Filter** - Gmail uses ML to automatically sort spam emails.",
                    "category": "Example",
                    "keywords": "real world, machine learning, example, practical"
                },
                {
                    "question": "Give a real-world example of artificial intelligence",
                    "answer": "🌟 REAL-WORLD AI EXAMPLES:\n\n1. **Siri/Alexa/Google Assistant** - Voice assistants use AI to understand and respond to your commands.\n\n2. **Self-driving Cars** - Tesla and Waymo use AI to navigate roads and avoid obstacles.\n\n3. **Face Recognition** - Used in smartphone unlocking and airport security.\n\n4. **ChatGPT** - AI that can write text, answer questions, and solve problems.\n\n5. **Medical Diagnosis** - AI helps doctors detect diseases from X-rays and MRI scans.",
                    "category": "Example",
                    "keywords": "real world, AI, example, practical"
                },
                {
                    "question": "Give a real-world example of NLP",
                    "answer": "🌟 REAL-WORLD NLP EXAMPLES:\n\n1. **Google Translate** - Translates text between 100+ languages.\n\n2. **Grammarly** - Checks grammar and suggests writing improvements.\n\n3. **Chatbots** - Customer service chatbots that understand human queries.\n\n4. **Voice-to-Text** - Convert speech to text used in dictation apps.\n\n5. **Sentiment Analysis** - Companies analyze social media posts to understand customer opinions.",
                    "category": "Example",
                    "keywords": "real world, NLP, example, practical"
                },
                {
                    "question": "Give a real-world example of deep learning",
                    "answer": "🌟 REAL-WORLD DEEP LEARNING EXAMPLES:\n\n1. **Self-driving Cars** - Deep learning processes camera data to detect objects on the road.\n\n2. **Voice Assistants** - Converts speech to text using deep neural networks.\n\n3. **Face Recognition** - Identifies faces in photos using deep learning.\n\n4. **Healthcare** - Deep learning analyzes medical images like X-rays and MRI scans.\n\n5. **AI Art** - DALL-E and Midjourney use deep learning to create images from text.",
                    "category": "Example",
                    "keywords": "real world, deep learning, example"
                },
                
                # ===== IMAGE SEARCH LINKS =====
                {
                    "question": "Show images of neural networks",
                    "answer": "📷 VIEW NEURAL NETWORK IMAGES:\n\n🔗 Google Images: https://www.google.com/search?q=neural+network&tbm=isch\n\n🔗 Wikipedia: https://en.wikipedia.org/wiki/Neural_network\n\n🔗 YouTube: https://www.youtube.com/results?search_query=neural+network+explained",
                    "category": "Resource",
                    "keywords": "images, neural networks, visual"
                },
                {
                    "question": "Show images of artificial intelligence",
                    "answer": "📷 VIEW AI IMAGES:\n\n🔗 Google Images: https://www.google.com/search?q=artificial+intelligence&tbm=isch\n\n🔗 Unsplash: https://unsplash.com/s/photos/artificial-intelligence\n\n🔗 YouTube: https://www.youtube.com/results?search_query=artificial+intelligence+explained",
                    "category": "Resource",
                    "keywords": "images, AI, artificial intelligence"
                },
                {
                    "question": "Show images of machine learning",
                    "answer": "📷 VIEW ML IMAGES:\n\n🔗 Google Images: https://www.google.com/search?q=machine+learning&tbm=isch\n\n🔗 YouTube: https://www.youtube.com/results?search_query=machine+learning+explained",
                    "category": "Resource",
                    "keywords": "images, ML, machine learning"
                },
                
                # ===== RESOURCE LINKS =====
                {
                    "question": "Where can I learn more about AI?",
                    "answer": "📚 LEARN MORE ABOUT AI:\n\n🔗 **Online Courses:**\n• Google AI Education: https://ai.google/education\n• DeepLearning.AI: https://www.deeplearning.ai\n• Stanford CS229: https://stanford.edu/~shervine/teaching/cs-229/\n\n🔗 **YouTube Videos:**\n• 3Blue1Brown Neural Networks: https://youtu.be/aircAruvnKk\n• IBM AI Explained: https://youtu.be/5q87K1W2nF4\n\n🔗 **Articles & Blogs:**\n• Towards Data Science: https://towardsdatascience.com\n• MIT AI News: https://news.mit.edu/topic/artificial-intelligence",
                    "category": "Resource",
                    "keywords": "learn, resource, AI, course"
                },
                {
                    "question": "Where can I learn more about machine learning?",
                    "answer": "📚 LEARN MORE ABOUT ML:\n\n🔗 **Online Courses:**\n• Andrew Ng ML Course: https://www.coursera.org/learn/machine-learning\n• Google ML Crash Course: https://developers.google.com/machine-learning/crash-course\n\n🔗 **YouTube:**\n• StatQuest ML: https://www.youtube.com/@statquest\n• Sentdex ML Tutorials: https://youtube.com/sentdex\n\n🔗 **Practice:**\n• Kaggle: https://www.kaggle.com\n• Google Colab: https://colab.research.google.com",
                    "category": "Resource",
                    "keywords": "learn, resource, ML, course"
                },
                {
                    "question": "Where can I learn more about NLP?",
                    "answer": "📚 LEARN MORE ABOUT NLP:\n\n🔗 **Online Courses:**\n• Hugging Face NLP Course: https://huggingface.co/learn/nlp-course\n• Stanford CS224N: https://web.stanford.edu/class/cs224n/\n\n🔗 **Libraries:**\n• NLTK: https://www.nltk.org\n• spaCy: https://spacy.io\n• Transformers: https://huggingface.co/docs/transformers",
                    "category": "Resource",
                    "keywords": "learn, resource, NLP"
                }
            ]
            for item in sample_data:
                knowledge = KnowledgeBase(question=item["question"], answer=item["answer"], category=item["category"], keywords=item["keywords"])
                db.add(knowledge)
            db.commit()
            print("✅ Knowledge base initialized with ALL new data!")
            print("✅ Added: Definitions (AI, ML, NLP), Examples, Real-World Examples, Image Links, Resources")
        else:
            print("✅ Knowledge base already has data!")

        if load_csv_dataset:
            dataset_count = import_csv_knowledge_base(db)
            if dataset_count:
                print(f"✅ CSV dataset was merged into the knowledge base ({dataset_count} rows).")
            else:
                print("✅ Knowledge base already contains the CSV dataset or no dataset file was found.")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

# Initialize
init_knowledge_base()