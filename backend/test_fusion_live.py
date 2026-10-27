"""Direct test: does fusion match semantically similar queries?"""
from app.database import SessionLocal, KnowledgeBase
from app.feature_fusion import get_fusion
from app.main import _init_feature_fusion

_init_feature_fusion()
fusion = get_fusion()

db = SessionLocal()
entries = db.query(KnowledgeBase).all()

print("=" * 70)
print("FEATURE FUSION TEST")
print("=" * 70)

test_queries = [
    "define artificial intelligence",
    "explain machine learning",
    "what is AI",
    "tell me about machine learning",
]

for q in test_queries:
    print(f"\nQuery: '{q}'")
    print("-" * 70)

    scores = []
    for e in entries:
        if not e.question:
            continue
        s = fusion.similarity(q, e.question, use_sbert=True)
        scores.append((s, e.question))

    scores.sort(reverse=True, key=lambda x: x[0])
    for score, question in scores[:3]:
        flag = "  ⭐ MATCH" if score >= 0.55 else ""
        print(f"  {score:.3f}  →  '{question}'{flag}")

db.close()
print("\n" + "=" * 70)