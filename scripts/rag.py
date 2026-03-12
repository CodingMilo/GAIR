"""
================================================================================
MODULE : RAG (RETRIEVAL AUGMENTED GENERATION)
================================================================================
Ce module implémente la logique de recherche sémantique pour enrichir les 
questions avec du contexte technique pertinent.

FONCTIONNEMENT :
1. CHARGEMENT ET CHUNKING :
   - Lit le fichier 'rag.tex' (format LaTeX original).
   - Découpe le document en sections logiques (chunks) basées sur les 
     balises '\section*{}'. Cela permet d'isoler des concepts (ex: Weibull).

2. INDEXATION (EMBEDDINGS) :
   - Pour chaque section du document, génère un vecteur numérique (embedding).
   - Ces vecteurs représentent le "sens" sémantique de la documentation.

3. RECHERCHE (SIMILARITÉ COSINUS) :
   - Lorsqu'une question est posée, elle est convertie en vecteur.
   - Le moteur calcule la similarité entre la question et toutes les sections 
     de la documentation.
   - Les 'k' sections les plus proches (les plus pertinentes) sont extraites.

4. CONTEXTE :
   - Le texte extrait est renvoyé pour être inséré dans le prompt envoyé au LLM.

AVANTAGE :
Permet au modèle de répondre avec une précision d'expert en consultant 
directement les formules et définitions du cours de fiabilité.

UTILISATION :
    from rag import RAGEngine
    rag = RAGEngine(client, config)
    rag.prepare_embeddings() # À faire une fois au début
    context = rag.get_context("Comment calculer le MTTF d'une loi de Weibull ?")
================================================================================
"""

import re
import numpy as np
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

class RAGEngine:
    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.doc_db: List[str] = []
        self.embeddings: Optional[np.ndarray] = None
        self.tfidf_vectorizer: Optional[TfidfVectorizer] = None
        self.tfidf_matrix = None
        self._initialize_docs()

    def _initialize_docs(self):
        """Charge le fichier rag.tex et le découpe en sections."""
        from pathlib import Path
        try:
            # Handle both object-like and dict-like config
            rag_path = self.config.get('rag_tex_path') if isinstance(self.config, dict) else getattr(self.config, 'rag_tex_path', None)
            
            if not rag_path:
                # Fallback to default location in scripts/rag.tex
                rag_path = Path(__file__).parent / "rag.tex"
            else:
                rag_path = Path(rag_path)

            if not rag_path.exists():
                print(f"[WARN] Document RAG introuvable à {rag_path}")
                return

            with open(rag_path, "r", encoding="utf-8") as f:
                full_text = f.read()

            # Extraction du contenu entre \begin{document} et \end{document}
            doc_match = re.search(r'\\begin\{document\}(.*?)\\end\{document\}', full_text, flags=re.DOTALL)
            content = doc_match.group(1) if doc_match else full_text
            
            # Découpage par section
            pattern = r'(\\section\*\{.*?\}.*?)(?=\\section\*\{|$)'
            self.doc_db = [s.strip() for s in re.findall(pattern, content, flags=re.DOTALL) if s.strip()]
            
            print(f"RAG : {len(self.doc_db)} sections de documentation chargées.")

            # Build TF-IDF keyword index (BM25-like) — no API calls needed
            if self.doc_db:
                self._build_tfidf_index()

        except Exception as e:
            print(f"[ERROR] Échec de l'initialisation du RAG : {e}")
            self.doc_db = []

    @staticmethod
    def _clean_for_bm25(text: str) -> str:
        """Strip LaTeX commands to improve keyword matching quality."""
        text = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', ' ', text)
        text = re.sub(r'\\[a-zA-Z]+', ' ', text)
        text = re.sub(r'[{}$&%#_^~]', ' ', text)
        return ' '.join(text.split())

    def _build_tfidf_index(self) -> None:
        """Build a TF-IDF index over doc_db for keyword (BM25-style) retrieval."""
        try:
            cleaned = [self._clean_for_bm25(doc) for doc in self.doc_db]
            self.tfidf_vectorizer = TfidfVectorizer(
                ngram_range=(1, 2),
                min_df=1,
                max_df=0.95,
                sublinear_tf=True,        # BM25-like TF saturation
                strip_accents='unicode',
                token_pattern=r'(?u)\b[a-zA-Z_][a-zA-Z0-9_]+\b',
            )
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(cleaned)
            print(f"RAG : TF-IDF index built ({self.tfidf_matrix.shape[1]} terms).")
        except Exception as exc:
            print(f"[WARN] TF-IDF index build failed: {exc}")
            self.tfidf_vectorizer = None
            self.tfidf_matrix = None

    def prepare_embeddings(self):
        """Génère les embeddings pour toute la base documentaire."""
        if not self.doc_db:
            return
            
        print("RAG : Génération des vecteurs d'embeddings pour la documentation...")
        temp_embeddings = []
        for doc in tqdm(self.doc_db):
            emb = self.client.get_embedding(doc)
            if emb:
                temp_embeddings.append(emb)
            else:
                # En cas d'échec, on met un vecteur de zéros pour garder l'alignement
                temp_embeddings.append([0.0] * 1536) # Taille standard OpenAI/OpenRouter
                
        self.embeddings = np.array(temp_embeddings)
        print("RAG : Indexation terminée.")

    def get_context(self, query: str, k: int = 8) -> str:
        """Retrieve the k most relevant sections using hybrid semantic + keyword search.

        Combines dense cosine-similarity (60 %) with TF-IDF keyword scores (40 %)
        so that exact reliability terms (e.g. 'Maturity Path', 'BOM') are not
        missed by embeddings alone.
        """
        if len(self.doc_db) == 0:
            return ""

        semantic_scores = None
        if self.embeddings is not None and getattr(self.embeddings, "size", 0) > 0:
            raw_emb = self.client.get_embedding(query)
            if raw_emb and len(raw_emb) > 0:
                query_emb = np.array(raw_emb).reshape(1, -1)
                if self.embeddings.shape[1] > 0:
                    semantic_scores = cosine_similarity(query_emb, self.embeddings)[0]
            else:
                print("[WARN] Query embedding failed. Falling back to TF-IDF retrieval.")

        # ── Keyword (TF-IDF / BM25-like) scores ─────────────────────────────
        keyword_scores = None
        if self.tfidf_vectorizer is not None and self.tfidf_matrix is not None:
            try:
                q_tfidf = self.tfidf_vectorizer.transform(
                    [self._clean_for_bm25(query)]
                )
                keyword_scores = np.asarray(
                    self.tfidf_matrix.dot(q_tfidf.T).todense()
                ).flatten()
            except Exception:
                keyword_scores = None

        if semantic_scores is not None and keyword_scores is not None:
            sem_max = semantic_scores.max() or 1.0
            kw_max = keyword_scores.max() or 1.0
            combined = (
                0.6 * (semantic_scores / sem_max)
                + 0.4 * (keyword_scores / kw_max)
            )
        elif semantic_scores is not None:
            combined = semantic_scores
        elif keyword_scores is not None:
            combined = keyword_scores
        else:
            print("[WARN] Neither embeddings nor TF-IDF retrieval is available. No context retrieved.")
            return ""
        
        top_k_indices = np.argsort(combined)[-k:][::-1]
        context_parts = [self.doc_db[i] for i in top_k_indices]
        return "\n\n".join(context_parts)
