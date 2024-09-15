Document Retrieval Backend
This project is a document retrieval backend that utilizes embeddings and vector search to retrieve relevant documents based on semantic similarity. It is built using FastAPI and uses FAISS for fast similarity search and Redis for caching search results and tracking API usage.
Features
	•	Document Search: Provides an API endpoint to search documents based on a query using text embeddings.
	•	Caching: Uses Redis to cache results for faster retrieval on repeated searches.
	•	Rate Limiting: Limits each user to a maximum of 5 search requests per day.
	•	Logging: Logs important events like request frequency, search timings, and background tasks.
	•	Background Task: Runs a background scraper to ingest documents (e.g., news articles).
	•	Dockerized: The entire application can be containerized using Docker for easy deployment.
Technologies Used
	•	FastAPI: A modern web framework for building APIs with Python.
	•	FAISS: A library for efficient similarity search and clustering of dense vectors.
	•	Redis: An in-memory data store used for caching and rate-limiting.
	•	Loguru: For structured logging.
	•	Docker: To containerize the application.
	•	Sentence-Transformers: For generating embeddings from textual data.
Setup Instructions
1. Clone the Repository
git clone https://github.com/your-username/document-retrieval-backend.git
cd document-retrieval-backend
2. Install Dependencies
Using Python and Virtual Environment:
1.Create a virtual environment:
python3 -m venv venv
source venv/bin/activate  # On Linux/macOS
venv\Scripts\activate  # On Windows
2.Install the dependencies:
pip install -r requirements.txt
3. Run Redis Server
Make sure Redis is installed and running on your machine:
redis-server
4. Run the Application
Start the FastAPI server using Uvicorn:
uvicorn app.main:app --reload
The API will be available at http://localhost:8000.
5. Run with Docker
1.Build the Docker Image:
docker build -t document-retrieval-app .
2.Run the Docker Container:
docker run -p 8000:8000 document-retrieval-app
API Endpoints
1. Health Check
	•	Endpoint: /health
	•	Method: GET
	•	Description: Simple endpoint to verify that the API is running.

2. Search Documents
	•	Endpoint: /search
	•	Method: POST
	•	Description: Search for documents based on a query using text embeddings.
	•	Parameters:
	◦	user_id (str): A unique identifier for the user making the request.
	◦	text (str): The query text for searching documents.
	◦	top_k (int, optional): The number of top results to return (default is 10).
	◦	threshold (float, optional): The minimum similarity score for a document to be included in the response (default is 0.5).
Example:
curl -X POST "http://localhost:8000/search" \
-H "Content-Type: application/json" \
-d '{
  "user_id": "user123",
  "text": "natural language processing",
  "top_k": 5,
  "threshold": 0.7
}'
Response:

{
  "results": [
    {
      "doc_id": 1,
      "similarity": 0.85
    },
    {
      "doc_id": 2,
      "similarity": 0.80
    }
  ],
  "inference_time": 0.45
}
3. Rate Limiting
Each user is allowed a maximum of 5 requests per day. After exceeding this limit, the API will return an HTTP 429 (Too Many Requests) status code.
Response:
{
  "detail": "Too many requests"
}

Project Structure
.
├── app/
│   ├── __init__.py         # App initialization, including background tasks and Redis setup
│   ├── main.py             # FastAPI app routes and endpoints
│   ├── search.py           # Search logic using FAISS and Sentence-Transformers
│   ├── utils.py            # Utility functions (caching, rate limiting, logging)
├── Dockerfile              # Docker configuration
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
└── ...



How It Works
Document Search
	•	When a user submits a search query, the text is converted into an embedding using Sentence-Transformers.
	•	FAISS is then used to find the most similar document embeddings from the stored documents.
	•	The top k results (based on cosine similarity) are returned to the user.
Caching
	•	Each search request is cached in Redis with a unique cache key (based on user_id and text).
	•	If the same query is made within a short period (default: 5 minutes), the cached result is returned, improving response times.
Rate Limiting
	•	The number of requests made by each user is tracked using Redis.
	•	If a user exceeds the limit of 5 requests per day, an HTTP 429 response is returned.
Background Task
	•	A background task is initiated when the server starts, which scrapes and ingests new documents (e.g., news articles) into the system. You can customize this task to ingest documents as needed.

Future Improvements
	•	Add more advanced ranking and filtering mechanisms for document retrieval.
	•	Implement authentication and user-specific document collections.
	•	Enhance background scraping tasks with advanced scheduling.
	•	Improve caching and rate limiting with more sophisticated policies.

License
This project is licensed under the MIT License - see the LICENSE file for details.

