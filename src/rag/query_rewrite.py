"""Query rewriting and expansion for retrieval."""

from src.rag.preparation import ACRONYM_MAP

EXPANSION_MAP = {
    "kart kayıp": "kayıp kart çalıntı kart kart bloke etme",
    "kmh": "kredili mevduat hesabı",
    "limit ne kadar": "kredi kartı limiti FAST limiti EFT limiti",
}


def rewrite_query(query: str) -> str:
    """Expand acronyms and common banking shorthand."""
    normalized = query.strip()
    lower = normalized.lower()

    for phrase, expansion in EXPANSION_MAP.items():
        if phrase in lower:
            normalized = f"{normalized} {expansion}"

    for acronym in ACRONYM_MAP:
        if acronym.lower() in lower and acronym not in normalized:
            normalized = f"{normalized} {ACRONYM_MAP[acronym]}"

    return " ".join(normalized.split())
