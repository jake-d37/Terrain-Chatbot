# backend/app/services/tools/gemini.py
from typing import List, Dict, Any, Tuple, Deque
from collections import deque
import threading
import time
import os, json, logging

import google.generativeai as genai


# Developer/system-level guardrails used for the tool-decision pass. This plays the
# role of the "inner" prompt: it is never shown to customers and encodes how the
# assistant should think about tools.
SYSTEM_TOOL_PROTOCOL = """
You are Terrain's assistant. You can either answer directly, or if a tool is needed,
you must output ONLY a single JSON object on one line with this structure:

{"tool": "<tool_name>", "args": { ... }, "success_message": "...", "empty_message": "...""}




Rules:
- Do not include any extra text or Markdown, only the JSON.
- If no tool is needed, output {"tool": null}.
- Tool names must exactly match those provided below.
Available tools:
{TOOL_DOCS}
"""

# Template used after a tool executes to explain the result back to the user. This
# effectively acts like the "outer" prompt, because it turns internal tool output
# into customer-facing text.
FOLLOWUP_SUMMARIZER = """
Summarize the following TOOL_RESULT for the user in English.
Be concise and helpful.

TOOL_RESULT:

{tool_text}
"""


RATE_LIMITED_MESSAGE = "Sorry, I’m handling too many requests right now. Please try again soon."


class _RateLimiter:
    """Simple sliding-window limiter to throttle outbound Gemini calls."""

    def __init__(self, max_calls: int, window_seconds: float, mode: str):
        self.max_calls = max_calls
        self.window = window_seconds
        self.mode = mode
        self._history: Deque[float] = deque()
        self._lock = threading.Lock()

    def acquire(self):
        if not self.max_calls or self.max_calls < 0:
            return
        while True:
            now = time.monotonic()
            with self._lock:
                while self._history and now - self._history[0] >= self.window:
                    self._history.popleft()
                if len(self._history) < self.max_calls:
                    self._history.append(now)
                    return
                wait_for = self.window - (now - self._history[0])
            if self.mode == "error":
                raise RuntimeError("Gemini API rate limit exceeded; try again later.")
            # Default behaviour: block until a slot frees up.
            time.sleep(max(wait_for, 0.0))


_CALLS_PER_MINUTE = int(os.environ.get("GEMINI_CALLS_PER_MINUTE", "0") or 0)
_RATE_LIMIT_MODE = os.environ.get("GEMINI_RATE_LIMIT_MODE", "block").lower()
_GEMINI_LIMITER = _RateLimiter(
    _CALLS_PER_MINUTE, 60.0, "error" if _RATE_LIMIT_MODE == "error" else "block"
)


class LLMClient:
    def __init__(self, model_name: str = "gemini-1.5-pro", api_key: str | None = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        if not self.api_key:
            # will still run but clearly log we're faking
            self._use_fake = True
            logging.warning("[LLM] No GEMINI_API_KEY found -> using FAKE mode")
            return
        self._use_fake = False
        genai.configure(api_key=self.api_key)
        self._model = genai.GenerativeModel(self.model_name)

    def _call(self, prompt: str) -> str:
        """Low-level real call that returns raw text."""
        if not self._use_fake:
            try:
                _GEMINI_LIMITER.acquire()
            except RuntimeError as e:
                logging.warning("[LLM] %s", e)
                raise
        resp = self._model.generate_content(prompt)
        try:
            return resp.candidates[0].content.parts[0].text
        except Exception as e:
            logging.exception("Gemini response parsing failed: %s", e)
            return "Sorry, I’m unable to generate a reply right now."

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tool_decls: List[Dict[str, Any]],
        tool_runner,
    ) -> Tuple[str, List[str]]:
        """
        JSON tool protocol:
        1) First call asks the model whether to call a tool; it must reply with a JSON object.
        2) If a tool is requested -> run it -> second call asks the model to summarize tool result.
        3) If no tool -> just do a direct answer (second call).
        """
        used: List[str] = []

        if self._use_fake:
            user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
            if any(k in user_msg for k in ["找", "书", "AI", "book"]):
                used.append("search_books")
                result = tool_runner("search_books", {"query": "AI"})
                return result.get("_nl", "Done."), used
            return "Hello, I am the TERRAIN assistant.", used

        # 1) Ask model whether to call a tool
        tool_docs = []
        for t in tool_decls:
            params = ", ".join(t.get("parameters", {}).get("properties", {}).keys())
            tool_docs.append(f"- {t['name']}: {t['description']} (params: {params})")
        sys_prompt = SYSTEM_TOOL_PROTOCOL.replace("{TOOL_DOCS}", "\n".join(tool_docs))

        user_text = next((m["content"] for m in messages if m["role"] == "user"), "")
        try:
            decide_text = self._call(sys_prompt + "\n\nUser:\n" + user_text).strip()
        except RuntimeError:
            logging.warning("[LLM] rate limiter denied tool decision call")
            return RATE_LIMITED_MESSAGE, used

        # Try to parse JSON
        tool_req = None
        try:
            tool_req = json.loads(decide_text)
        except json.JSONDecodeError:
            # Model didn't follow protocol; fall back to direct answer
            logging.info("[LLM] decision was not JSON -> treating as direct answer")
            if decide_text:
                answer = decide_text
            else:
                try:
                    answer = self._call(user_text)
                except RuntimeError:
                    logging.warning("[LLM] rate limiter denied direct answer")
                    return RATE_LIMITED_MESSAGE, used
            return answer, used

        if not tool_req or tool_req.get("tool") in (None, "", "none"):
            # No tool, generate final answer directly
            try:
                answer = self._call(user_text)
            except RuntimeError:
                logging.warning("[LLM] rate limiter denied direct answer")
                return RATE_LIMITED_MESSAGE, used
            return answer, used

        # 2) Run the tool
        tool_name = tool_req.get("tool")
        args = tool_req.get("args") or {}
        used.append(tool_name)
        tool_result = tool_runner(tool_name, args)
        nl = tool_result.get("_nl") or "操作完成。"

        # 3) Ask model to summarize tool result for user
        summary_prompt = FOLLOWUP_SUMMARIZER.format(tool_text=nl)
        try:
            final = self._call(summary_prompt)
        except RuntimeError:
            logging.warning("[LLM] rate limiter denied follow-up summarizer")
            return RATE_LIMITED_MESSAGE, used
        return final, used
