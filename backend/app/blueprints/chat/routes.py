# POST /api/chat
from flask import Blueprint, request, jsonify, current_app
from app.blueprints.chat.schemas import ChatRequest, ChatResponse
from app.services.tools.registry import build_default_registry
from app.services.tools.gemini import LLMClient
import logging

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True) or {}

    # sanitize history (must be a list of {role, content})
    raw_hist = body.get("history")
    if not isinstance(raw_hist, list):
        raw_hist = []

    try:
        req = ChatRequest(
            message=(body.get("message") or "").strip(),
            user_id=body.get("user_id"),
            history=raw_hist,
            session_id=body.get("session_id"),
            stream=bool(body.get("stream", False)),
            meta=body.get("meta"),
        )
        if not req.message:
            return jsonify({"error": "message is required"}), 400

        registry = build_default_registry()
        tool_decls = registry.list_for_llm()
        tool_docs = registry.docs_for_prompt()

        system_prompt = (
            "You are Terrain's assistant. Use tools when helpful.\n"
            "Available tools:\n" + tool_docs
        )

        messages = [{"role": "system", "content": system_prompt}]
        for m in (req.history or [])[-20:]:
            r = m.get("role")
            c = m.get("content")
            if r in ("user", "assistant") and isinstance(c, str) and c.strip():
                messages.append({"role": r, "content": c})
        messages.append({"role": "user", "content": req.message})

        llm = LLMClient(
            model_name=current_app.config.get("GENAI_MODEL", "gemini-1.5-pro"),
            api_key=current_app.config.get("GEMINI_API_KEY"),
        )
        final_text, used_tools = llm.chat_with_tools(messages, tool_decls, registry.run)

        resp = ChatResponse(
            text=final_text, used_tools=used_tools, session_id=req.session_id
        )
        return jsonify(resp.__dict__)
    except Exception as e:
        # log full traceback so we can see the real cause
        current_app.logger.exception("chat endpoint failed: %s", e)
        return jsonify({"error": "internal error"}), 500
