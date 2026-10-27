"""
Review 2 Demo Script
Run from inside backend/:  python test_features.py
"""

import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer


def demo_bow():
    print("\n========== 1. BAG OF WORDS ==========")
    corpus = ["what is machine learning",
              "machine learning is fun",
              "what is deep learning"]
    bow = CountVectorizer()
    X = bow.fit_transform(corpus)
    print("Vocabulary:", list(bow.get_feature_names_out()))
    print("Matrix:\n", X.toarray())


def demo_tfidf():
    print("\n========== 2. TF-IDF ==========")
    corpus = ["what is machine learning",
              "machine learning is fun",
              "what is deep learning"]
    tfidf = TfidfVectorizer()
    X = tfidf.fit_transform(corpus)
    print("Vocabulary:", list(tfidf.get_feature_names_out()))
    print("Matrix:\n", np.round(X.toarray(), 2))


def demo_word2vec():
    print("\n========== 3. WORD2VEC ==========")
    from gensim.models import Word2Vec
    sentences = [
        ["machine", "learning", "is", "fun"],
        ["deep", "learning", "uses", "neural", "networks"],
        ["ai", "is", "artificial", "intelligence"],
        ["machine", "learning", "models", "learn", "from", "data"],
    ]
    model = Word2Vec(sentences, vector_size=100, window=5,
                     min_count=1, epochs=50)
    print("Vector 'learning':", model.wv["learning"][:5])
    print("Similar to 'learning':", model.wv.most_similar("learning", topn=3))


def demo_sbert():
    print("\n========== 4. SENTENCE-BERT ==========")
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    model = SentenceTransformer("all-MiniLM-L6-v2")
    sents = ["What is machine learning?",
             "Define machine learning",
             "How to cook pasta"]
    emb = model.encode(sents, show_progress_bar=False)
    sim = cosine_similarity([emb[0]], emb)[0]
    for i, s in enumerate(sents):
        print(f"  '{s}'  ->  {sim[i]:.3f}")


def demo_fusion():
    print("\n========== 5. FEATURE FUSION ==========")
    from app.feature_fusion import FeatureFusion
    kb = ["what is machine learning", "what is deep learning",
          "who is elon musk", "what is artificial intelligence",
          "give example of supervised learning"]
    ff = FeatureFusion(kb)
    v = ff.extract("define machine learning", use_sbert=True)
    print("Fused shape:", v.shape)
    print("\nSimilarity tests:")
    pairs = [
        ("What is machine learning?", "Define machine learning"),
        ("What is machine learning?", "How to cook pasta"),
        ("who is elon musk", "who is elon musk?"),
    ]
    for a, b in pairs:
        print(f"  '{a}'  vs  '{b}'  ->  {ff.similarity(a, b):.3f}")


if __name__ == "__main__":
    demo_bow()
    demo_tfidf()
    demo_word2vec()
    demo_sbert()
    demo_fusion()
    print("\n✅ All feature demos completed.")