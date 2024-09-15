from sentence_transformers import SentenceTransformer
import faiss

# Load sentence transformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# FAISS index (simulated - in practice, load embeddings into FAISS index)
index = faiss.IndexFlatL2(384)  # Adjust dimensions based on model output

def search_documents(query: str, top_k: int, threshold: float):
    query_embedding = model.encode([query])
    
    # Search for the top_k results (simulated with FAISS here)
    D, I = index.search(query_embedding, top_k)

    # Mock results for demonstration purposes
    results = [{"doc_id": int(i), "similarity": float(d)} for d, i in zip(D[0], I[0]) if d > threshold]
    
    return results
