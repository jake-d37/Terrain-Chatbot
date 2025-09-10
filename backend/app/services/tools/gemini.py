# backend/app/services/tools/gemini.py
from typing import List, Dict, Any, Tuple
import os, json, logging

import google.generativeai as genai


SYSTEM_TOOL_PROTOCOL = """
You are Terrain's assistant. You can either answer directly, or if a tool is needed,
you must output ONLY a single JSON object on one line with this structure:

{"tool": "<tool_name>", "args": { ... }}

Rules:
- Do not include any extra text or Markdown, only the JSON.
- If no tool is needed, output {"tool": null}.
- Tool names must exactly match those provided below.
Available tools:
{TOOL_DOCS}
"""

FOLLOWUP_SUMMARIZER = """
Summarize the following TOOL_RESULT for the user in English.
Be concise and helpful.

TOOL_RESULT:

{tool_text}
"""


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
        decide_text = self._call(sys_prompt + "\n\nUser:\n" + user_text).strip()

        # Try to parse JSON
        tool_req = None
        try:
            tool_req = json.loads(decide_text)
        except json.JSONDecodeError:
            # Model didn't follow protocol; fall back to direct answer
            logging.info("[LLM] decision was not JSON -> treating as direct answer")
            answer = decide_text if decide_text else self._call(user_text)
            return answer, used

        if not tool_req or tool_req.get("tool") in (None, "", "none"):
            # No tool, generate final answer directly
            answer = self._call(user_text)
            return answer, used

        # 2) Run the tool
        tool_name = tool_req.get("tool")
        args = tool_req.get("args") or {}
        used.append(tool_name)
        tool_result = tool_runner(tool_name, args)
        nl = tool_result.get("_nl") or "操作完成。"

        # 3) Ask model to summarize tool result for user
        summary_prompt = FOLLOWUP_SUMMARIZER.format(tool_text=nl)
        final = self._call(summary_prompt)
        return final, used
