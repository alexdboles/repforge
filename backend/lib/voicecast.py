"""Fixed ElevenLabs voice cast.

A recurring buyer must sound like the same person every time they come back, so
voices are assigned by *character name* — never randomly, and never re-derived
from mood. Settings are tuned per character for conversational speech (lower
stability = more natural variation; high similarity = recognisable identity).

Voice ids below are verified against the account's available voices; see
GET /api/voice/cast for a live verification of the whole cast.
"""

# name -> ElevenLabs voice + delivery settings
CAST: dict[str, dict] = {
    # --- recurring journey characters ---
    "Marcus Webb": {
        "voice_id": "iP95p4xoKVk53GoZ742B",  # Chris — charming, down-to-earth
        "voice_label": "Chris",
        "role": "Operations Director / Owner",
        "style_note": "Casual and direct. Short acknowledgements, busy, price-conscious.",
        "settings": {"stability": 0.42, "similarity_boost": 0.78, "style": 0.0, "speed": 1.04},
    },
    "Sarah Lindqvist": {
        "voice_id": "hpp4J3VqNfWAUOO0d1Us",  # Bella — professional, bright, warm
        "voice_label": "Bella",
        "role": "Head of Customer Operations",
        "style_note": "Calm, analytical, polite but sceptical. Pauses before answering.",
        "settings": {"stability": 0.5, "similarity_boost": 0.82, "style": 0.0, "speed": 0.98},
    },
    "David Okonjo": {
        "voice_id": "cjVigY5qzO86Huf0OWal",  # Eric — smooth, trustworthy
        "voice_label": "Eric",
        "role": "Owner",
        "style_note": "Warm but time-poor. Friendly, gets to the point quickly.",
        "settings": {"stability": 0.46, "similarity_boost": 0.8, "style": 0.0, "speed": 1.02},
    },
    # --- catalog scenario prospects ---
    "Jordan Miller": {
        "voice_id": "pNInz6obpgDQGcFmaJgB",  # Adam — firm, brisk executive
        "voice_label": "Adam",
        "role": "VP of Sales",
        "style_note": "Senior, time-conscious. Concise, interrupts rambling.",
        "settings": {"stability": 0.55, "similarity_boost": 0.8, "style": 0.0, "speed": 1.02},
    },
    "Alicia Reyes": {
        "voice_id": "XrExE9yKIg1WjnnlVkGX",  # Matilda — knowledgeable, professional
        "voice_label": "Matilda",
        "role": "Director of Operations",
        "style_note": "Measured, guarded operations buyer. Concise answers.",
        "settings": {"stability": 0.52, "similarity_boost": 0.82, "style": 0.0, "speed": 0.97},
    },
    "Daniel Okafor": {
        "voice_id": "nPczCjzI2devNBz1zQrb",  # Brian — deep, resonant
        "voice_label": "Brian",
        "role": "Chief Financial Officer",
        "style_note": "Analytical, price-pressure CFO. Comfortable with silence.",
        "settings": {"stability": 0.58, "similarity_boost": 0.84, "style": 0.0, "speed": 0.96},
    },
    "Priya Raghavan": {
        "voice_id": "cgSgspJ2msm6clMCkdW9",  # Jessica — bright, quick
        "voice_label": "Jessica",
        "role": "Co-founder & CTO",
        "style_note": "Fast, impatient founder. Challenges vague claims immediately.",
        "settings": {"stability": 0.4, "similarity_boost": 0.76, "style": 0.0, "speed": 1.06},
    },
    # --- the instructional voice: never reused for a buyer ---
    "REP COACH": {
        "voice_id": "Xb7hH8MSUJpSbSDYk0k2",  # Alice — clear, engaging educator
        "voice_label": "Alice",
        "role": "Sales coach narrator",
        "style_note": "Calm, warm, instructional. Used only for training narration.",
        "settings": {"stability": 0.6, "similarity_boost": 0.8, "style": 0.0, "speed": 1.0},
    },
}

# Archetype voices for AI-generated ("Practice my business") prospects, whose
# names are not known in advance. Still deterministic per persona.
PERSONA_VOICES: dict[str, str] = {
    "rushed_executive": "Jordan Miller",
    "analytical_cfo": "Daniel Okafor",
    "friendly_owner": "David Okonjo",
    "skeptical_director": "Sarah Lindqvist",
    "guarded_operations": "Alicia Reyes",
    "impatient_founder": "Priya Raghavan",
    "default": "Jordan Miller",
}

DEFAULT_KEY = "Jordan Miller"


def resolve(character: str = "", persona: str = "default") -> dict:
    """Approved voice config for a character name, falling back to its archetype."""
    entry = CAST.get((character or "").strip())
    if entry:
        return {"character": character.strip(), **entry}
    key = PERSONA_VOICES.get(persona, DEFAULT_KEY)
    return {"character": key, **CAST[key]}


def cast_entries() -> list[dict]:
    return [{"character": name, **cfg} for name, cfg in CAST.items()]
