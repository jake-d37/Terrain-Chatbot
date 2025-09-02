# Interaction with Gemini, function calling loop
from typing import List, Dict, Any, Tuple
import os


def _fake_llm(messages, tool_decls, tool_runner):
    # Simplified simulation of LLM behavior
    user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
    used = []
    if any(k in user_msg for k in ["find", "looking for", "AI", "book"]):
        used.append("search_books")
        tool_res = tool_runner("search_books", {"query": "AI"})
        return tool_res.get("_nl", "Finished operation."), used
    return (
        "Hi, I'm Terrain Assistant. You can ask me to find books, for example: 'Help me find books related to AI.'",
        used,
    )


class LLMClient:
    def __init__(self, model_name: str = "gemini-1.5-pro", api_key: str | None = None):
        self.model_name = model_name
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")

        self._use_fake = not bool(self.api_key)
        if not self._use_fake:
            import google.generativeai as genai

            genai.configure(api_key=self.api_key)
            self._genai = genai
            self._model = genai.GenerativeModel(model_name)

    def chat_with_tools(
        self,
        messages: List[Dict[str, str]],
        tool_decls: List[Dict[str, Any]],
        tool_runner,
    ) -> Tuple[str, List[str]]:
        if self._use_fake:
            return _fake_llm(messages, tool_decls, tool_runner)
        # Real Gemini call (adjust field names as needed)
        resp = self._model.generate_content(
            contents=messages,
            tools=[{"function_declarations": tool_decls}] if tool_decls else None,
        )
        # Simplified: if no function call, take text directly
        cand = resp.candidates[0]
        if not getattr(cand, "function_call", None):
            return cand.content.parts[0].text, []
        call = cand.function_call
        used = [call.name]
        tool_res = tool_runner(call.name, call.args or {})
        # Append tool result to messages
        messages = messages + [{"role": "tool", "name": call.name, "content": tool_res}]
        resp2 = self._model.generate_content(
            contents=messages,
            tools=[{"function_declarations": tool_decls}] if tool_decls else None,
        )
        return resp2.candidates[0].content.parts[0].text, used
