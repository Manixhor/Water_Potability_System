from fastapi import FastAPI, HTTPException
import time
from app.search import search_documents
from redis import Redis

app = FastAPI()

# Redis connection for caching and rate limiting
redis_client = Redis(host='localhost', port=6379, db=0)

@app.get("/health")
def health_check():
    return {"status": "active"}

@app.post("/search")
def search(text: str, user_id: str, top_k: int = 10, threshold: float = 0.5):
    user_requests = redis_client.get(user_id)
    
    if user_requests and int(user_requests) > 5:
        raise HTTPException(status_code=429, detail="Too many requests")

    # Increment user request count
    redis_client.incr(user_id)

    start_time = time.time()
    
    # Perform document search (use the search module here)
    results = search_documents(text, top_k, threshold)

    # Calculate and log inference time
    inference_time = time.time() - start_time
    app.logger.info(f"User {user_id}, inference time: {inference_time}s")

    return {"results": results, "inference_time": inference_time}
