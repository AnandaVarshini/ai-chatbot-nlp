"""
Feature Fusion Module
Combines BOW + TF-IDF + Word2Vec + Sentence-BERT + BERT features
into a single unified vector for improved intent classification
and semantic knowledge-base search.
"""

import os
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

_sbert_model = None


class FeatureFusion:
    def __init__(self, kb_questions=None, cache_dir=None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "models")
        self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        self.bow = CountVectorizer(max_features=200)
        self.tfidf = TfidfVectorizer(max_features=200)
        self.word2vec = None
        self.sbert = None
        self._bert_tok = None
        self._bert_model = None
        self.fitted = False

        if kb_questions:
            self.fit(kb_questions)

    def fit(self, corpus):
        print(f"[FeatureFusion] Fitting on {len(corpus)} documents...")
        
        # 1. Load the external SQuAD dataset to enrich training
        import json
        import os
        
        full_corpus = list(corpus) # Start with your KB questions
        dataset_path = os.path.join(os.path.dirname(__file__), "..", "data", "squad_dataset.json")
        
        if os.path.exists(dataset_path):
            try:
                print("[FeatureFusion] Loading SQuAD dataset for additional training...")
                with open(dataset_path, 'r', encoding='utf-8') as f:
                    squad_data = json.load(f)
                    
                # Extract questions ONLY from Computer Science, Science, and Education articles
                count = 0
                allowed_titles = [
                    'computer', 'science', 'artificial', 'intelligence', 'machine', 
                    'learning', 'software', 'internet', 'physics', 'biology', 
                    'chemistry', 'mathematics', 'technology', 'university', 'education',
                    'engineering', 'algorithm', 'programming', 'data', 'network'
                ]
                
                for article in squad_data.get('data', []):
                    article_title = article.get('title', '').lower()
                    
                    # Only keep articles related to study topics
                    if any(topic in article_title for topic in allowed_titles):
                        for paragraph in article.get('paragraphs', []):
                            for qa in paragraph.get('qas', []):
                                full_corpus.append(qa['question'])
                                count += 1
                print(f"[FeatureFusion] Added {count} study-related questions from SQuAD dataset.")
            except Exception as e:
                print(f"[FeatureFusion] Could not load dataset: {e}")
        
        # 2. Fit vectorizers on the combined corpus
        self.bow.fit(full_corpus)
        self.tfidf.fit(full_corpus)

        # 3. Train Word2Vec on the combined corpus
        try:
            from gensim.models import Word2Vec
            tokenized = [doc.lower().split() for doc in full_corpus]
            self.word2vec = Word2Vec(
                tokenized, vector_size=100, window=5,
                min_count=1, epochs=20, workers=2,
            )
            print("[FeatureFusion] Word2Vec trained.")
        except Exception as e:
            print(f"[FeatureFusion] Word2Vec failed: {e}")

        self.fitted = True
        print("[FeatureFusion] Fit complete.")

    def _get_sbert(self):
        global _sbert_model
        if _sbert_model is None:
            from sentence_transformers import SentenceTransformer
            print("[FeatureFusion] Loading Sentence-BERT (first time)...")
            _sbert_model = SentenceTransformer("all-MiniLM-L6-v2")
        return _sbert_model

    def bow_features(self, text):
        return self.bow.transform([text]).toarray()[0]

    def tfidf_features(self, text):
        return self.tfidf.transform([text]).toarray()[0]

    def word2vec_features(self, text):
        if self.word2vec is None:
            return np.zeros(100)
        tokens = text.lower().split()
        vecs = [self.word2vec.wv[t] for t in tokens if t in self.word2vec.wv]
        if not vecs:
            return np.zeros(100)
        return np.mean(vecs, axis=0)

    def sbert_features(self, text):
        return self._get_sbert().encode([text], show_progress_bar=False)[0]

    def bert_features(self, text):
        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            if self._bert_tok is None:
                print("[FeatureFusion] Loading BERT (first time)...")
                self._bert_tok = AutoTokenizer.from_pretrained("bert-base-uncased")
                self._bert_model = AutoModel.from_pretrained("bert-base-uncased")
                self._bert_model.eval()
            inputs = self._bert_tok(text, return_tensors="pt",
                                     truncation=True, max_length=64)
            with torch.no_grad():
                out = self._bert_model(**inputs)
            return out.last_hidden_state[:, 0, :].squeeze().numpy()
        except Exception as e:
            print(f"[FeatureFusion] BERT unavailable: {e}")
            return np.zeros(768)

    def extract(self, text, use_sbert=True, use_bert=False):
        if not self.fitted:
            return np.zeros(1)
        parts = [
            self.bow_features(text),
            self.tfidf_features(text),
            self.word2vec_features(text),
        ]
        if use_sbert:
            parts.append(self.sbert_features(text))
        if use_bert:
            parts.append(self.bert_features(text))
        return np.concatenate(parts)

    def similarity(self, text1, text2, use_sbert=True, use_bert=False):
        if not self.fitted:
            return 0.0
        v1 = self.extract(text1, use_sbert=use_sbert, use_bert=use_bert)
        v2 = self.extract(text2, use_sbert=use_sbert, use_bert=use_bert)
        denom = np.linalg.norm(v1) * np.linalg.norm(v2)
        return float(np.dot(v1, v2) / denom) if denom else 0.0


_fusion_instance = None


def init_fusion(kb_questions):
    global _fusion_instance
    _fusion_instance = FeatureFusion(kb_questions)
    return _fusion_instance


def get_fusion():
    return _fusion_instance