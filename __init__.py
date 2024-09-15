from fastapi import FastAPI
from redis import Redis
from loguru import logger
from threading import Thread

# Initialize Redis connection (for caching and rate-limiting)
redis_client = Redis(host='localhost', port=6379, db=0)

# Initialize the FastAPI app
app = FastAPI()

# Background task for document scraping
def start_background_tasks():
    logger.info("Starting background document scraping task...")
    # You can call your document scraping function here
    # Example: scrape_and_ingest_documents()

# Function to be called when the FastAPI app starts
@app.on_event("startup")
def on_startup():
    # Start the background task in a separate thread
    scraping_thread = Thread(target=start_background_tasks)
    scraping_thread.start()
    logger.info("FastAPI app has started")

# Function to be called when the FastAPI app shuts down
@app.on_event("shutdown")
def on_shutdown():
    logger.info("FastAPI app is shutting down")

# Import your routes (endpoints)
from app.main import health, search
