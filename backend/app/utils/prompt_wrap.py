# app/utils/prompt_wrap.py
import requests


class PromptWrapError(Exception):
    pass


def _read_from_source(link: str, timeout=10) -> str:
    if link.startswith(("http://", "https://")):
        r = requests.get(link, timeout=timeout)
        if r.status_code != 200:
            raise PromptWrapError(f"failed to fetch: {link} (status {r.status_code})")
        return r.text
    # optional local support:
    if link.startswith("file://"):
        with open(link[7:], "r", encoding="utf-8") as f:
            return f.read()
    raise PromptWrapError("unsupported link scheme (use http/https or file://)")


def wrap_prompt(outer_link: str, inner_link: str, placeholder="{{CONTENT}}") -> str:
    outer = _read_from_source(outer_link)
    inner = _read_from_source(inner_link)
    if placeholder not in outer:
        raise PromptWrapError(f"placeholder '{placeholder}' not found in outer prompt")
    # basic size guard
    if len(inner) > 100_000:
        raise PromptWrapError("inner prompt too large (>100k chars)")
    return outer.replace(placeholder, inner)
