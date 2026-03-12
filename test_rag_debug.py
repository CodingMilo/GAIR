import sys
sys.path.insert(0, r'c:\Users\miloh\Documents\Etudes\CS\3A\Mention ORRA\GAIR_TEAM_PROJECT')
sys.path.insert(0, r'c:\Users\miloh\Documents\Etudes\CS\3A\Mention ORRA\GAIR_TEAM_PROJECT\scripts')
from supporting_scripts import OpenRouterClient
from scripts.rag import RAGEngine

client = OpenRouterClient()

config = {
    'rag_tex_path': r'c:\Users\miloh\Documents\Etudes\CS\3A\Mention ORRA\GAIR_TEAM_PROJECT\scripts\rag.tex',
    'embedding_model': 'text-embedding-3-small',
}

print('--- Creating RAGEngine ---')
rag = RAGEngine(client, config)
print(f'doc_db length: {len(rag.doc_db)}')
print(f'tfidf_matrix shape: {rag.tfidf_matrix.shape if rag.tfidf_matrix is not None else None}')

print()
print('--- Testing raw embedding call ---')
emb = client.get_embedding("Weibull distribution MTTF formula")
print(f'embedding type: {type(emb)}')
print(f'embedding length: {len(emb) if emb else "None"}')
print(f'embedding first 5 values: {emb[:5] if emb else "None"}')
all_zero = all(v == 0.0 for v in emb) if emb else True
print(f'all zeros (fallback triggered?): {all_zero}')

print()
print('--- Testing prepare_embeddings ---')
rag.prepare_embeddings()
print(f'embeddings shape: {rag.embeddings.shape if rag.embeddings is not None else None}')
if rag.embeddings is not None and rag.embeddings.size > 0:
    all_zero_emb = (rag.embeddings == 0).all()
    print(f'all zero embeddings: {all_zero_emb}')

print()
print('--- Testing get_context ---')
ctx = rag.get_context("What is Weibull distribution MTTF?", k=2)
print(f'context length: {len(ctx)}')
print(f'context preview: {ctx[:300]}')
