import re

PII_PATTERNS = {
    "PHONE": re.compile(r"\b(\+?\d{2,3}[ -]?\d{4}[ -]?\d{4})\b"),
    "EMAIL": re.compile(r"\b([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b"),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "CURP": re.compile(r"\b[A-Z]{4}\d{6}[H,M][A-Z]{5}[A-Z0-9]{2}\b"),
    "PHONE_MX_DIRECT": re.compile(r"\b(\d{10})\b"),
    "ADDRESS_DETAIL": re.compile(r"\b(calle|av|avenida|privada|cerrada|andador|boulevard|blvd)\s+\w+", re.IGNORECASE),
}


INJECTION_PATTERNS = [
    re.compile(r"ignora\s+(las\s+)?(instrucciones|comandos|reglas|lo\s+anterior)", re.IGNORECASE),
    re.compile(r"olvida\s+(las\s+)?(instrucciones|comandos|reglas|todo)", re.IGNORECASE),
    re.compile(r"bypass\s+(all\s+)?rules?", re.IGNORECASE),
    re.compile(r"auto.?aprobad?[oa]\s*(sin\s+)?revisi[oó]n", re.IGNORECASE),
    re.compile(r"no\s+sigas\s+(las\s+)?(instrucciones|reglas)", re.IGNORECASE),
    re.compile(r"aprueba\s+(mi\s+)?solicitud\s+sin\s+(revisi[oó]n|preguntar)", re.IGNORECASE),
    re.compile(r"ignore\s+(all\s+)?(instructions|previous)", re.IGNORECASE),
    re.compile(r"(eres\s+un\s+)?asistente\s+que\s+aprueba", re.IGNORECASE),
]


def redact_pii(text: str) -> tuple[str, list[str]]:
    redacted = text
    redacted_categories = []

    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            redacted_categories.append(pii_type)
            redacted = pattern.sub(f"[{pii_type}_REDACTED]", redacted)

    return redacted, redacted_categories


def detect_prompt_injection(text: str) -> list[str]:
    found = []
    for pattern in INJECTION_PATTERNS:
        match = pattern.search(text)
        if match:
            found.append(match.group(0))
    return found


class SecurityScreen:
    def process(self, user_input: str) -> dict:
        redacted_text, redacted_categories = redact_pii(user_input)
        injection_matches = detect_prompt_injection(redacted_text)

        return {
            "original_text": user_input,
            "redacted_text": redacted_text,
            "redacted_categories": redacted_categories,
            "injection_detected": len(injection_matches) > 0,
            "injection_matches": injection_matches,
            "safe_to_proceed": len(injection_matches) == 0,
        }
