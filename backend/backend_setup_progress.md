
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

*Status:* ✅ Server check returns **200 OK**.

✅ API calling successful returns **200 OK**.
