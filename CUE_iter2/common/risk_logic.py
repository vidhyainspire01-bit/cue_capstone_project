def assess_risk_level(summary_text: str):
    keywords = {
        "high": ["p0", "escalation", "critical", "drop", "churn", "breach"],
        "medium": ["delay", "latency", "issue", "frustration"],
        "low": ["stable", "recovery", "resolved"]
    }

    text_lower = summary_text.lower()
    for level, terms in keywords.items():
        if any(term in text_lower for term in terms):
            return level.capitalize()
    return "Low"
