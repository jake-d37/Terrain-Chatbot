
# Backend Setup Progress Log — AI Chatbot API

**Timestamp:** 2025-09-03 08:25  
**Owner:** Miles (AI engineer)  
**Scope:** Stand up a minimal, testable backend for the Terrain Chatbot: app factory, health check, tool registry scaffolding, LLM client (fake fallback), clean imports, and working run command.

---

## 1) Environment & Dependencies

- **Python virtualenv**
  ```bash
  cd TERRAIN-CHATBOT/backend
  python3 -m venv .venv
  source .venv/bin/activate
  ```

- **Requirements (dev)**
  - Unify **Flask** version across all requirement files to avoid resolver conflicts.
  - Add **flask-cors** for CORS support.
  - Add **python-dotenv** to load environment variables from `.env`.
  - (Optional) **google-generativeai** for Gemini integration.

  Example `requirements/dev.txt` key lines:
  ```txt
  Flask==3.1.1
  flask-cors==4.0.0
  python-dotenv==1.0.1
  google-generativeai==0.8.3
  ```

- **.env**
  ```dotenv
  GEMINI_API_KEY=YOUR_KEY   # optional for now (fake LLM fallback works without it)
  GENAI_MODEL=gemini-1.5-pro
  FLASK_DEBUG=1
  ```

- Install:
  ```bash
  pip install -r backend/requirements/dev.txt
  ```

---

## 2) Application Skeleton (what we created/edited)

### `app/app.py` — Application factory
- Loads config via `load_config(app)`.
- Initializes extensions via `init_extensions(app)` and configures logging.
- Registers blueprints: `/health`, `/v1` (chat API namespace).
- Registers global error handlers.

### `app/config.py` — Configuration
- `Config` class for ENV/DEBUG/CORS settings and placeholders (Gemini, Firebase).
- `load_config(app)` reads `.env` with `dotenv` and sets `GENAI_MODEL` / `GEMINI_API_KEY`.

### `app/extensions.py` — Extensions (minimal & robust)
- **Optional import** for `flask_cors`. If not installed, server still boots (no CORS).
- `init_extensions(app)`: attach CORS when available.
- `configure_logging(app)`: simple stdout logger.

### Blueprints
- `app/blueprints/health/routes.py`: GET `/health` → `{{"status": "ok"}}`.
- `app/blueprints/chat/schemas.py`: request/response dataclasses.
- `app/blueprints/chat/routes.py`: POST `/v1/chat` endpoint (uses tool registry + LLM client).

### Services (Tools layer)
- `app/services/tools/registry.py`: function/tool registry exposed to the LLM (includes:
  - tool declarations for the LLM,
  - `run()` for invoking handlers,
  - NL summarizer for tool outputs,
  - basic “deny second call” policy).
- `app/services/tools/book_inventory.py`: placeholder tool `search_books(...)` with demo data.
- `app/services/tools/gemini.py`: LLM client with **fake fallback** (works without API key).

### Utilities
- `app/utils/errors.py`: `ToolError` + centralized error mapping.

---

## 3) Import Path Hygiene & Package Layout

- **Final structure (relevant parts):**
  ```text
  backend/
    app/
      __init__.py
      app.py
      config.py
      extensions.py
      utils/
        __init__.py
        errors.py
      blueprints/
        __init__.py
        health/
          __init__.py
          routes.py
        chat/
          __init__.py
          routes.py
          schemas.py
      services/
        __init__.py
        tools/
          __init__.py
          registry.py
          gemini.py
          book_inventory.py
  ```

- **All imports use the `app.` prefix** (e.g., `from app.services.tools.registry import build_default_registry`).

- **Removed/renamed root shadow modules** (`backend/app.py`, `backend/config.py`, `backend/extensions.py`) that were eclipsing the `app/` package and causing:
  > `ModuleNotFoundError: No module named 'app.utils.errors'; 'app.utils' is not a package`

- Ensured every package directory has an `__init__.py` file so Python treats them as packages.

---

## 4) Issues We Hit & Fixes

| Error / Symptom | Root Cause | Fix |
|---|---|---|
| `Cannot install Flask==3.1.1 and flask==3.0.3...` | Dev/prod requirements pinned to conflicting Flask versions | Unified Flask version across all requirement files |
| `ModuleNotFoundError: No module named 'flask_cors'` | `flask-cors` not installed | Added `flask-cors` to requirements and installed; also made CORS optional in `extensions.py` |
| `ModuleNotFoundError: No module named 'services'` | Imports assumed `services` was a top-level package | Use absolute package path: `app.services...` |
| `No module named 'utils'` | Imports referenced top-level `utils` | Move `utils/errors.py` under `app/utils` and import via `app.utils.errors` |
| `'app.utils' is not a package` | Root-level `backend/app.py` shadowed the `app/` package | Remove/rename shadow files; ensure `app/__init__.py` exists |
| Startup warning about CORS/logging | Using global `cors` instance and duplicate `init_extensions` functions | Simplified `extensions.py` to a single `init_extensions` + `configure_logging` |

---

## 5) How to Run (current)

```bash
# from repository root
python3 -m venv .venv
source backend/.venv/bin/activate            # if not already
flask --app backend/app.app:create_app run -p 8000
# test health
curl -s http://localhost:8000/health/
# => {"status": "ok"}
```


Optional: quick chat smoke test (fake LLM fallback will work without an API key):
```bash
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Look for a book for me"}'

```

---

## 6) Decisions & Rationale

- **App factory pattern** to keep config and extension initialization deterministic and testable.
- **Absolute imports (`app.*`)** to avoid path ambiguity and to make unit tests cleaner.
- **Tool Registry** as a single point to expose functions to the LLM, enforce policies (e.g., deny duplicate calls), and convert structured results to natural language (“Return NL from DB results”).  
- **Fake LLM fallback** to develop offline and avoid API key blockers.
- **CORS optionality** so the server can still boot if `flask-cors` is missing.
- **Minimal health endpoint** for CI and local smoke checks.

---

## 7) Feature: Real Gemini API calling (and JSON encoding)

**What we changed**

* Switched `LLMClient` to call **real Gemini** when `GEMINI_API_KEY` is present.

  * Decision pass: model returns a strict JSON like `{"tool":"...", "args":{...}}`.
  * If a tool is requested → run it via the registry → second call asks Gemini to **summarize** the tool result.
  * If no tool needed → direct answer.
* Clear logging of mode: `using_fake=True|False`.
* Tried to set UTF-8 JSON output (no `\uXXXX`) via `app.config["JSON_AS_ASCII"] = False` in `create_app()`; still needs verification in the client/CLI.

**Key snippets**

```python
# app/services/tools/gemini.py (simplified)
genai.configure(api_key=self.api_key)
self._model = genai.GenerativeModel(self.model_name)
# self._use_fake = not bool(self.api_key)  # logs FAKE when no key

# app/app.py
def create_app():
    app = Flask(__name__)
    app.config["JSON_AS_ASCII"] = False  # return actual UTF-8 in jsonify
    ...
```

**How to test**

```bash
# .env
GEMINI_API_KEY=YOUR_REAL_KEY
GENAI_MODEL=gemini-1.5-pro

# start
flask --app backend/app.app:create_app run -p 8000

# observe logs
# INFO [LLM] Mode check: using_fake=False

# basic call
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Help me to find a book about AI"}' | jq

# tip: to see raw UTF-8 text from JSON, use jq -r
curl -s ... | jq -r .text
```

**Note (encoding)**

* If you still see `\uXXXX`, confirm `JSON_AS_ASCII=False` ran, or print with `jq -r`.
* As a fallback you can return a `Response(json.dumps(obj, ensure_ascii=False), mimetype="application/json")` for the payloads where you require strict UTF-8.

---

## 8) Feature: Ephemeral chat history (stateless server)

**What we changed**

* **`ChatRequest`** now: `message: str`, `user_id: Optional[str]`, `history: Optional[List[Dict[str,str]]]`, etc.
* `/v1/chat` accepts an optional `history` array and **rehydrates the last 20 turns** (`user`/`assistant`) before appending the new user message.
* Defensive parsing + logging to avoid 500s on malformed bodies.
* The server **does not persist** history; the **client** owns it (e.g., `sessionStorage`).

**Server test (without frontend)**

```bash
# single-shot
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello"}' | jq

# simulate context via client-provided history (two prior turns)
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Continue our discussion.",
    "history": [
      {"role":"user","content":"I like sci-fi books."},
      {"role":"assistant","content":"Noted. Do you prefer hard or soft sci-fi?"}
    ]
  }' | jq
```

**Frontend pattern (per-tab memory)**

```html
<script>
const KEY = 'chat_history_v1';
function loadH(){ try{return JSON.parse(sessionStorage.getItem(KEY)||'[]')}catch{return[]}}
function saveH(h){ sessionStorage.setItem(KEY, JSON.stringify(h.slice(-40))); }

async function sendMessage(message){
  const history = loadH();
  const res = await fetch('/v1/chat', {
    method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({ message, history })
  });
  const data = await res.json();
  history.push({role:'user', content:message});
  history.push({role:'assistant', content:data.text});
  saveH(history);
  return data;
}
</script>
```

---

## 9) (Removed) Prompt wrapping utility

This feature has been retired. The `/v1/wrap` endpoint, wrap-related tools, and
environment toggles are no longer available. Prompts now live directly in
`app/services/tools/gemini.py`, and configuration happens there.



---

## 10) Feature: Kill irrelevant communication (off-topic gating + prewritten)

**What we added (2025-09-10)**

- `app/utils/relevance.py`
  - `check_relevance(text) -> RelevanceResult`: fast, local keyword heuristic for ecology/environment, books/library, and TERRAIN topics (EN + basic CN).
  - `prewritten_response(text) -> Optional[str]`: canned replies for greetings and “What is TERRAIN?” to avoid LLM calls.
  - `OFFTOPIC_MESSAGE`: standard deny message in English.
  - Language helpers: `is_probably_english(text)`, `should_force_english(text)` to decide whether to enforce English replies.

- `app/blueprints/chat/routes.py`
  - Before creating the LLM client:
    1) Run `prewritten_response` → if matched, return immediately (no LLM/tools).
    2) Run `check_relevance` → if not relevant, return `OFFTOPIC_MESSAGE` (no LLM/tools) and log `off-topic denied: ...`.
    3) Build system prompt. If `should_force_english(message)` is True, add: “Always respond in English …”.

- `app/services/tools/gemini.py`
  - Tool-result summarizer now explicitly says “in English”. Fallback errors are in English.

- `app/app.py`
  - Ensure UTF-8 JSON without `\uXXXX` escaping: set `app.config["JSON_AS_ASCII"] = False` and `app.json.ensure_ascii = False` (Flask 3).

**Why**
- Reduce token cost by short-circuiting irrelevant or trivial intents.
- Provide fast, deterministic responses for greetings/basic intro.
- Keep outputs consistent and readable for an English-first audience.

**How to test**

1) Start server
```bash
flask --app backend/app.app:create_app run -p 8000
```

2) Prewritten greeting (no LLM/tools)
```bash
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"hello"}' | jq -r .text
# EXPECT: English greeting text. used_tools should be []
```

3) Off-topic deny (no LLM/tools)
```bash
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Tell me a football joke"}' | jq -r .text
# EXPECT: English deny message about ecology/books scope. used_tools == []
```

4) Relevant request passes gating
```bash
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"Recommend beginner books on climate and design"}' | jq -r .text
# EXPECT: Not denied. Response content depends on LLM mode:
#  - With GEMINI_API_KEY: real model answer.
#  - Without key (FAKE mode): a simple placeholder reply.
```

5) Verify UTF-8 JSON (no \uXXXX)
```bash
curl -s -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"你好"}' | python3 -c 'import sys,json;print(json.dumps(json.load(sys.stdin), ensure_ascii=False, indent=2))'
```

6) Logs
```bash
# Terminal running Flask should print an info log when off-topic is denied:
# INFO off-topic denied: <reason>
```

**Notes / knobs**
- Broaden/narrow relevance by editing keywords in `relevance.py` or changing `min_hits`.
- Add more prewritten replies in `prewritten_response` for FAQs.
- English-only behavior is injected via `should_force_english`; remove that line to follow user language.
