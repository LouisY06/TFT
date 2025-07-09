import re

"""
Simple TFT rules-based query processor: focus on gold management (economy), leveling decisions, and rerolling strategy.
"""

def process_voice_query(query: str) -> str:
    """
    Matches user queries about economy, leveling, or rerolling and returns basic strategic advice.
    """
    q = query.lower()

    # Reroll/shop intents
    if re.search(r"\b(reroll|roll|refresh|shop|should.*roll)\b", q):
        return (
            "Only consider rerolling once you reach level 6 with at least 50 gold. "
            "Avoid pulling below 3-star strength unless you need a crucial carry."
        )

    # Leveling intents
    if re.search(r"\b(level|level up|xp|should i level)\b", q):
        return (
            "Leveling increases shop tier and unit cap. "
            "If you’re on a win streak, delay leveling to maintain gold; "
            "on a loss streak, leveling can stabilize your board."
        )

    # Economy/gold intents
    if re.search(r"\b(gold|economy|interest|save|spend)\b", q):
        return (
            "Maintain 50 gold to maximize interest each round. "
            "Spend only surplus on key champions or level-ups to stay flexible."
        )

    # Fallback for other queries
    return (
        "Sorry, I can only advise on rerolling, leveling, or managing gold. "
        "Try asking 'should I reroll?', 'when to level up?', or 'how much gold to save?'."
    )
