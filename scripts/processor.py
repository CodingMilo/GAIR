"""
================================================================================
MODULE : PROCESSOR (INTELLIGENCE & PARSING)
================================================================================
Ce module contient la logique "métier" de l'agent IA. 
Il fait le pont entre les données brutes et les réponses structurées.

FONCTIONNALITÉS :
1. PROMPT ENGINEERING :
   - Définit le 'System Prompt' qui transforme le LLM en ingénieur fiabilité.
   - Définit les contraintes de sortie (format, longueur, style).

2. ORCHESTRATION D'UNE QUESTION :
   - Prend une question brute.
   - Appelle le RAG pour obtenir le contexte pertinent.
   - Construit le prompt final (Question + Contexte).
   - Envoie le tout au client API.

3. PARSING DES RÉPONSES (EXTRACTION) :
   - Analyse la réponse textuelle du modèle pour extraire les lettres choisies.
   - Gère le format imposé '[Answer] [x]'.
   - Nettoie et trie les lettres (ex: 'b, a' devient 'a, b') pour assurer
     la compatibilité avec les systèmes d'évaluation (Kaggle).

AVANTAGE :
En isolant le prompt et le parsing ici, vous pouvez facilement tester de
nouvelles instructions sans toucher à la mécanique de l'API ou du RAG.

UTILISATION :
    from processor import Processor
    proc = Processor(config, client, rag)
    result = proc.process_question("Quelle est l'unité du taux de défaillance ?")
================================================================================
"""

import re
import json
from typing import Dict, Any, Optional

class Processor:
    def __init__(self, config, client, rag, prompt_name: str = "default", custom_system_prompt=None):
        self.config = config
        self.client = client
        self.rag = rag
        self.prompt_name = prompt_name
        
        # Chargement des prompts depuis le fichier JSON
        self.prompts = self._load_prompts()
        
        if custom_system_prompt:
            self.system_prompt = custom_system_prompt
        else:
            self.system_prompt = self.prompts.get(prompt_name, self.prompts.get("default", ""))

    def _load_prompts(self) -> Dict[str, str]:
        """Charge la bibliothèque de prompts."""
        if self.config.prompts_path.exists():
            with open(self.config.prompts_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"default": "You are a helpful assistant."}

    def parse_answer(self, text: str) -> str:
        """Extrait et normalise les lettres de réponse du texte généré."""
        # On cherche d'abord le bloc [Answer] [x, y]
        match = re.search(r'\[Answer\]\s*\[(.*?)\]', text, re.IGNORECASE)
        if match:
            # Extraction de toutes les lettres individuelles à l'intérieur des crochets
            letters = re.findall(r'([a-zA-Z])', match.group(1))
            return ", ".join(sorted(l.lower() for l in set(letters)))
        
        # Fallback : si le format strict n'est pas respecté, on cherche n'importe quel [x]
        letters = re.findall(r'\[([a-zA-Z])\]', text)
        if letters:
            return ", ".join(sorted(l.lower() for l in set(letters)))
            
        return ""

    def process_question(self, question: str, use_rag: bool = True, k: int = 2) -> Dict[str, Any]:
        """Traite une question unique : recherche de contexte, appel LLM et parsing."""
        
        # 1. Récupération du contexte (RAG)
        context = ""
        if use_rag:
            context = self.rag.get_context(question, k=k)

        # 2. Construction du prompt utilisateur
        user_content = f"Question: {question}\n\n"
        if context:
            user_content += (
                "--- BACKGROUND KNOWLEDGE FROM MANUAL ---\n"
                f"{context}\n"
                "-----------------------------------------\n"
                "Please analyze the question based on the technical documentation above."
            )

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_content}
        ]
        
        # 3. Appel au modèle
        raw_response = self.client.chat(messages)
        
        # 4. Extraction de la réponse
        prediction = self.parse_answer(raw_response)
        
        return {
            "raw_response": raw_response,
            "prediction": prediction,
            "context_used": context
        }
