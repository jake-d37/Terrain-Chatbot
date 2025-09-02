# Tool Registry
from typing import Callable, Dict, Any, List
from dataclasses import dataclass
from utils.errors import ToolError
from services.tools.book_inventory import search_books


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: Dict[str, Any]
    handler: Callable[[Dict[str, Any]], Dict[str, Any]]
    allow_multiple: bool = False


class ToolsRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolSpec] = {}
        self._called: set[str] = set()

    def register(self, spec: ToolSpec):
        self._tools[spec.name] = spec

    def list_for_llm(self) -> List[Dict[str, Any]]:
        return [
            {"name": t.name, "description": t.description, "parameters": t.parameters}
            for t in self._tools.values()
        ]

    def docs_for_prompt(self) -> str:
        lines = []
        for t in self._tools.values():
            params = ", ".join(t.parameters.get("properties", {}).keys())
            lines.append(f"- {t.name}: {t.description} | params=[{params}]")
        return "\n".join(lines)

    def run(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        if name not in self._tools:
            raise ToolError(f"Unknown tool: {name}")
        tool = self._tools[name]
        if not tool.allow_multiple and name in self._called:
            return {
                "_policy": "deny_second_call",
                "message": f"Tool '{name}' already used.",
            }
        self._called.add(name)
        result = tool.handler(args)
        return {"_nl": self._to_nl(name, result), "_raw": result}

    def _to_nl(self, name: str, payload: Dict[str, Any]) -> str:
        if name == "search_books":
            items = payload.get("items", [])
            if not items:
                return "No matching books found."
            tops = [
                f"\"{it.get('title')}\" by {it.get('author')} ({it.get('status','unknown')})"
                for it in items[:5]
            ]
            return "I found these books:\n- " + "\n- ".join(tops)
        return "Operation completed."


def build_default_registry() -> ToolsRegistry:
    reg = ToolsRegistry()
    reg.register(
        ToolSpec(
            name="search_books",
            description="Search library books by keyword (title/author/subject).",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
            handler=lambda args: {"items": search_books(args.get("query", ""))},
            allow_multiple=True,
        )
    )
    return reg
