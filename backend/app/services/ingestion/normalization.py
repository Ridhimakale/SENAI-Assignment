from dataclasses import dataclass
from html import unescape

MAX_LLM_SAFE_BODY_CHARS = 10_000
BODY_PREVIEW_CHARS = 500


@dataclass(frozen=True)
class NormalizedBody:
    body: str
    preview: str
    is_empty: bool
    is_truncated_for_llm: bool


def normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return unescape(value).replace("\xa0", " ").strip()


def normalize_email_body(body: str | None) -> NormalizedBody:
    cleaned = normalize_text(body)
    return NormalizedBody(
        body=cleaned,
        preview=cleaned[:BODY_PREVIEW_CHARS],
        is_empty=cleaned == "",
        is_truncated_for_llm=len(cleaned) > MAX_LLM_SAFE_BODY_CHARS,
    )
