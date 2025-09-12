# app/utils/relevance.py
"""
Lightweight topic relevance checks and prewritten responses to reduce LLM calls.

- check_relevance(text): fast keyword heuristic for ecology/books/TERRAIN topics
- prewritten_response(text): returns canned replies for greetings and basics (English)
- is_probably_english(text) / should_force_english(text): simple language heuristic

This is intentionally minimal and fully local to avoid extra API cost.
You can later swap in a ML classifier while keeping the same interface.
"""
from dataclasses import dataclass
from typing import List, Optional, Tuple
import re


# Core topic keywords (English + Chinese) — extend as needed
ECOLOGY = [
    "ecology",
    "ecological",
    "environment",
    "environmental",
    "climate",
    "sustainab",
    "biodiversity",
    "conservation",
    "pollution",
    "carbon",
    "recycl",
    "green",
    # CN
    "生态",
    "环保",
    "环境",
    "气候",
    "可持续",
    "多样性",
    "保育",
    "污染",
    "碳",
    "回收",
]

BOOKS = [
    "book",
    "books",
    "reading",
    "read list",
    "reading list",
    "catalog",
    "catalogue",
    "library",
    "borrow",
    "loan",
    "return",
    "overdue",
    "author",
    "title",
    "recommend",
    # CN
    "书",
    "图书",
    "书单",
    "阅读",
    "借阅",
    "还书",
    "逾期",
    "作者",
    "书名",
    "推荐",
]

TERRAIN = [
    "terrain",
    "manifesto",
    "workshop",
    "event",
    "program",
    "project",
    # CN
    "宣言",
    "活动",
    "项目",
    "工作坊",
]


GREETING = [
    "hi",
    "hello",
    "hey",
    "yo",
    "good morning",
    "good afternoon",
    "good evening",
    "你好",
    "嗨",
    "哈喽",
]


_TOPIC_TABLE: List[Tuple[str, List[str]]] = [
    ("ecology", ECOLOGY),
    ("books", BOOKS),
    ("terrain", TERRAIN),
]


def _normalize(text: str) -> str:
    text = text or ""
    # Lowercase and squeeze spaces; keep CJK characters
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


@dataclass
class RelevanceResult:
    is_relevant: bool
    categories: List[str]
    matched: List[str]
    reason: str


def check_relevance(text: str, min_hits: int = 1) -> RelevanceResult:
    """Simple keyword heuristic.

    A message is considered relevant if it hits at least `min_hits` keywords
    across any of the topic groups.
    """
    t = _normalize(text)
    hits: List[str] = []
    cats: List[str] = []
    for cat, words in _TOPIC_TABLE:
        local_hits = [w for w in words if w in t]
        if local_hits:
            cats.append(cat)
            hits.extend(local_hits)
    relevant = len(hits) >= min_hits
    reason = (
        "matched keywords: " + ", ".join(sorted(set(hits)))
        if relevant
        else "no topic keywords"
    )
    return RelevanceResult(
        is_relevant=relevant, categories=cats, matched=hits, reason=reason
    )


def prewritten_response(text: str) -> Optional[str]:
    """Return a canned response for common intents to avoid LLM calls.

    Currently handles:
    - Greetings
    - "What is TERRAIN" style questions
    """
    t = _normalize(text)

    # Greetings
    if any(g in t for g in GREETING) or t in ("/start", "start"):
        return (
            "Hi! I’m the TERRAIN assistant. I focus on ecology, the arts, and books. "
            "I can help with reading lists, events, and borrowing information. How can I help?"
        )

    # What is TERRAIN?
    if (
        "what is terrain" in t
        or "terrain 是什么" in t
        or ("terrain" in t and "what" in t)
    ):
        return (
            "TERRAIN is a collection of projects that reconnect people with the more‑than‑human world "
            "through arts and cross‑disciplinary collaboration. We offer book lending, curated reading lists, "
            "events, and workshops that link ecology, technology, and community care."
        )

    return None


OFFTOPIC_MESSAGE = (
    "Sorry, this assistant focuses on ecology/environment, the arts, and books (e.g., reading recommendations, "
    "catalog queries, events, and workshops). To conserve resources we do not process unrelated requests. "
    "You can try: ‘Recommend a few beginner books on climate and design’, ‘How do I join a TERRAIN event?’, or ‘Search books by author’."
)


# -------------------------
# Language heuristic helpers
# -------------------------
def _has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def is_probably_english(text: str, ascii_ratio_threshold: float = 0.6) -> bool:
    """Best‑effort language heuristic without external deps.

    - If CJK characters are present → treat as non‑English.
    - Otherwise compute the ratio of ASCII letters to all letters; if above threshold → English.
    - If no letters at all → default to English.
    """
    if not text:
        return True
    if _has_cjk(text):
        return False
    alpha_total = 0
    ascii_alpha = 0
    for ch in text:
        if ch.isalpha():
            alpha_total += 1
            if "a" <= ch.lower() <= "z":
                ascii_alpha += 1
    if alpha_total == 0:
        return True
    return (ascii_alpha / alpha_total) >= ascii_ratio_threshold


def should_force_english(text: str) -> bool:
    """Return True when the bot should answer in English regardless of input.

    Usage: if this returns True, set your prompts/instructions to “answer in English”.
    This does not translate content; it only decides the output language policy.
    """
    return not is_probably_english(text)
