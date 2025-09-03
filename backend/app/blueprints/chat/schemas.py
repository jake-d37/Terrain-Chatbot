# Pydantic request/response model
from dataclasses import dataclass
from typing import Optional, Dict, Any, List


@dataclass
class ChatRequest:
    user_id: str
    message: str
    session_id: Optional[str] = None
    stream: bool = False
    meta: Optional[Dict[str, Any]] = None


@dataclass
class ChatResponse:
    text: str
    used_tools: List[str]
    session_id: Optional[str] = None
