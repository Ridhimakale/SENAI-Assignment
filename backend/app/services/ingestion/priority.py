from app.services.ingestion.normalization import normalize_text

KEYWORD_WEIGHTS: tuple[tuple[str, int], ...] = (
    ("ransomware", 100),
    ("send 2 btc", 100),
    ("data breach", 100),
    ("suspicious login", 90),
    ("p0", 80),
    ("cease and desist", 70),
    ("legal", 50),
    ("lawsuit", 50),
    ("urgent", 30),
    ("public review", 40),
    ("trustpilot", 40),
    ("g2", 35),
    ("refund", 10),
    ("churn", 25),
    ("cancel", 20),
)


def calculate_priority_score(subject: str | None, body: str | None) -> tuple[int, dict]:
    text = f"{normalize_text(subject)} {normalize_text(body)}".lower()
    matched_keywords: list[str] = []
    score = 0

    for keyword, weight in KEYWORD_WEIGHTS:
        if keyword in text:
            matched_keywords.append(keyword)
            score += weight

    return min(score, 100), {"matched_priority_keywords": matched_keywords}
