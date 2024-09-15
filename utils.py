import time
from loguru import logger
from redis import Redis
from fastapi import HTTPException

# Initialize Redis connection for caching and rate-limiting
redis_client = Redis(host='localhost', port=6379, db=0)

# Logging configuration using loguru
logger.add("logs/app.log", rotation="500 MB", retention="10 days", level="INFO")

def rate_limiter(user_id: str, max_requests: int = 5):
    """
    Rate limiting based on user_id. Raises HTTP 429 if the user exceeds max requests.
    
    Args:
    - user_id (str): A unique identifier for the user making requests.
    - max_requests (int): Maximum number of requests allowed per user (default is 5).
    
    Raises:
    - HTTPException: Throws 429 Too Many Requests if the user exceeds the allowed requests.
    """
    user_requests = redis_client.get(user_id)
    
    if user_requests and int(user_requests) >= max_requests:
        logger.warning(f"User {user_id} exceeded request limit")
        raise HTTPException(status_code=429, detail="Too many requests")
    
    # Increment user request count, with expiry for rate limit (e.g., 24 hours)
    redis_client.incr(user_id)
    redis_client.expire(user_id, 86400)  # Expires after 24 hours

def cache_search_results(query_key: str, results: dict, cache_duration: int = 300):
    """
    Cache search results in Redis for faster future retrieval.
    
    Args:
    - query_key (str): A unique key representing the search query.
    - results (dict): The search results to be cached.
    - cache_duration (int): Cache expiry time in seconds (default is 5 minutes).
    """
    redis_client.set(query_key, str(results), ex=cache_duration)
    logger.info(f"Cached search results for query '{query_key}'")

def get_cached_results(query_key: str):
    """
    Retrieve cached search results from Redis.
    
    Args:
    - query_key (str): The key representing the search query.
    
    Returns:
    - dict or None: Returns the cached results if available, otherwise None.
    """
    cached_results = redis_client.get(query_key)
    
    if cached_results:
        logger.info(f"Cache hit for query '{query_key}'")
        return eval(cached_results)  # Convert string back to dictionary
    
    logger.info(f"Cache miss for query '{query_key}'")
    return None

def log_inference_time(user_id: str, start_time: float):
    """
    Log the inference time for the document retrieval process.
    
    Args:
    - user_id (str): A unique identifier for the user making the request.
    - start_time (float): The timestamp when the search started.
    """
    inference_time = time.time() - start_time
    logger.info(f"User {user_id}, Inference time: {inference_time:.4f} seconds")
    return inference_time
