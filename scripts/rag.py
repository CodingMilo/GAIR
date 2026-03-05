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

class RAGEngine:
    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.doc_db: List[str] = []
        self.embeddings: Optional[np.ndarray] = None
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
        except Exception as e:
            print(f"[ERROR] Échec de l'initialisation du RAG : {e}")
            self.doc_db = []

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

    def get_context(self, query: str, k: int = 2) -> str:
        """Récupère les k sections les plus pertinentes pour une question donnée."""
        if self.embeddings is None or len(self.doc_db) == 0:
            return ""

        raw_emb = self.client.get_embedding(query)
        if not raw_emb or len(raw_emb) == 0:
            print("[WARN] Query embedding failed. No context retrieved.")
            return ""
            
        query_emb = np.array(raw_emb).reshape(1, -1)
        
        # Vérification des dimensions des embeddings indexés
        if self.embeddings.shape[1] == 0:
             print("[ERROR] Document embeddings are empty. No context retrieved.")
             return ""
             
        # Calcul de la similarité cosinus entre la question et la doc
        similarities = cosine_similarity(query_emb, self.embeddings)[0]
        
        # Récupération des indices des k meilleurs résultats
        top_k_indices = np.argsort(similarities)[-k:][::-1]
        
        context_parts = [self.doc_db[i] for i in top_k_indices]
        return "\n\n".join(context_parts)
