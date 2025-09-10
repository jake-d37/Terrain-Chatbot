# POST /api/chat
from flask import Blueprint, request, jsonify, current_app
from app.blueprints.chat.schemas import ChatRequest, ChatResponse
from app.services.tools.registry import build_default_registry
from app.services.tools.gemini import LLMClient
import logging
from app.utils.prompt_wrap import wrap_prompt, PromptWrapError
from app.utils.relevance import (
    check_relevance,
    prewritten_response,
    OFFTOPIC_MESSAGE,
    should_force_english,
)

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

        # 0) Prewritten fast path (greetings, basics)
        canned = prewritten_response(req.message)
        if canned:
            resp = ChatResponse(text=canned, used_tools=[], session_id=req.session_id)
            return jsonify(resp.__dict__)

        # 0.5) Off-topic gating: avoid LLM/tool calls to save cost
        rel = check_relevance(req.message)
        if not rel.is_relevant:
            current_app.logger.info("off-topic denied: %s", rel.reason)
            resp = ChatResponse(text=OFFTOPIC_MESSAGE, used_tools=[], session_id=req.session_id)
            return jsonify(resp.__dict__)

        registry = build_default_registry()
        tool_decls = registry.list_for_llm()
        tool_docs = registry.docs_for_prompt()

        # Language policy: if user message is not in English, force English answer
        force_en = should_force_english(req.message)
        language_note = (
            "Always respond in English, even if the user's message is not in English.\n"
            if force_en
            else "Respond in clear English.\n"
        )

        system_prompt = (
            "You are Terrain's assistant. Use tools when helpful.\n" + language_note +
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


@chat_bp.route("/wrap", methods=["POST"])
def wrap_only():
    body = request.get_json(force=True) or {}
    outer = body.get("outer_link")
    inner = body.get("inner_link")
    placeholder = body.get("placeholder", "{{CONTENT}}")
    if not outer or not inner:
        return jsonify({"error": "outer_link and inner_link are required"}), 400
    try:
        wrapped = wrap_prompt(outer, inner, placeholder=placeholder)
        return jsonify({"wrapped": wrapped})
    except PromptWrapError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        current_app.logger.exception("wrap failed: %s", e)
        return jsonify({"error": "internal error"}), 500
