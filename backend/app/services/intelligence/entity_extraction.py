import re

from app.schemas.classification import DetectedEntities


ORDER_ID_PATTERN = re.compile(r"\b(?:order|ord)[-_ ]?([A-Z0-9]{4,})\b", re.IGNORECASE)
TICKET_ID_PATTERN = re.compile(r"\b(?:ticket|case)[-_ ]?([A-Z0-9]{3,})\b", re.IGNORECASE)
MONEY_PATTERN = re.compile(r"(?:\$|USD\s?)\d[\d,]*(?:\.\d{2})?")
DEADLINE_PATTERN = re.compile(
    r"\b(?:by|before|until|deadline|within)\s+([A-Za-z0-9 ,\-]+)",
    re.IGNORECASE,
)
PRODUCT_KEYWORDS = ("api", "dashboard", "chatbot", "standard plan", "enterprise plan")


def extract_entities(text: str) -> DetectedEntities:
    lower_text = text.lower()
    return DetectedEntities(
        order_ids=[match.group(1) for match in ORDER_ID_PATTERN.finditer(text)],
        ticket_ids=[match.group(1) for match in TICKET_ID_PATTERN.finditer(text)],
        monetary_amounts=[match.group(0) for match in MONEY_PATTERN.finditer(text)],
        deadlines=[match.group(1).strip() for match in DEADLINE_PATTERN.finditer(text)],
        products_mentioned=[keyword for keyword in PRODUCT_KEYWORDS if keyword in lower_text],
    )
