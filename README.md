# 📖 Terrain Chatbot Backend

This project is a **Flask-based backend** for a chatbot system.
It acts as an **API gateway** between the frontend, Gemini (LLM), and external data sources (e.g., Firebase / partner APIs).
The backend is **stateless**: it does not store user sessions or long-term chat history — the frontend passes the conversation history in each request.

---

## 🔧 Project Structure

```
backend/
  app/
    __init__.py          # Application factory (create_app)
    config.py            # Environment-based configuration
    extensions.py        # Initialize extensions (CORS, logging, Firebase, etc.)
    utils/
      errors.py          # Unified error handling (returns JSON)
    middlewares/
      request_context.py # (Optional) Middleware for request IDs/logging
    blueprints/
      chat/
        __init__.py
        routes.py        # POST /api/chat (main chatbot API)
        schemas.py       # Request/response validation using Pydantic
      health/
        __init__.py
        routes.py        # GET /health (health check endpoint)
    services/
      gemini.py          # Handles Gemini API calls + function calling loop
      tools/
        registry.py      # Registry of all available tools
        book_inventory.py# Example tool: check book availability
      data_providers/
        base.py          # Abstract provider interface
        firebase_provider.py # Direct Firebase implementation
        http_provider.py     # Partner HTTP API implementation
  tests/
    test_chat_flow.py    # Integration test for /api/chat
    test_inventory_tool.py # Unit tests for tools
  wsgi.py                # Entry point for running the Flask app
  requirements.txt       # Python dependencies
  .env.example           # Example environment variables
```

### Key Concepts

* **Blueprints**:

  * `chat`: The main API (`POST /api/chat`) that forwards user messages to Gemini.
  * `health`: A simple health check (`GET /health`).

* **Services**:

  * `gemini.py`: Handles interaction with Gemini, including tool calls.
  * `tools/`: Functions (e.g., book lookup) that Gemini can call.
  * `data_providers/`: How tools fetch real data (via Firebase or partner HTTP APIs).

* **Stateless**:

  * No `users/` or `database/` modules.
  * Chat history is stored in the **browser (cookies)** and passed on each request.

---

## 📦 Required Libraries

The core dependencies are:

```
Flask>=2.3
flask-cors>=4.0
google-generativeai>=0.7
pydantic>=2.6
structlog>=24.1
python-dotenv>=1.0
httpx>=0.27
firebase-admin>=6.5
ruff>=0.4
black>=24.4
isort>=5.13
pytest>=8.2
pytest-cov>=5.0
```

---

## ⚙️ Setup & Installation

1. **Clone the repo & enter the backend folder**

   ```bash
   git clone <repo-url>
   cd backend
   ```

2. **Create and activate a virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Linux/Mac
   .venv\Scripts\activate      # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Copy `.env.example` and configure it**

   ```bash
   cp .env.example .env
   ```

   Set your keys:

   * `GEMINI_API_KEY`
   * Either Firebase credentials (`GOOGLE_APPLICATION_CREDENTIALS`, `FIREBASE_PROJECT_ID`)
     **or** partner API (`INVENTORY_BASE_URL`, `INVENTORY_API_KEY`)

---

## 🚀 Running the App

```bash
export FLASK_APP=wsgi.py
export FLASK_ENV=development   # or production
flask run --debug
```

The server runs at: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

* `GET /health` → `{ "status": "ok" }`
* `POST /api/chat` → Main chatbot API

---

## ✅ Testing

Run all tests with coverage:

```bash
pytest --cov=app
```

---

## 📝 Notes for Teammates

* Do **not** add any secrets to the repo. Use `.env`.
* The backend is **API-only** (no HTML templates, no user accounts).
* To add new functionality for the bot:

  1. Write a new tool in `services/tools/`.
  2. Register it in `registry.py`.
  3. Add unit tests in `tests/`.

