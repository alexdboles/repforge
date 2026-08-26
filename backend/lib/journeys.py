"""Recurring prospect journeys.

A journey is one character met repeatedly across several exercises. The character
carries a single hidden dossier that is revealed only through good questioning, and
each stage inherits what the rep actually learned in earlier calls — so re-asking
something the prospect already told them is noticed and penalised.
"""
from typing import Any

JOURNEYS: list[dict[str, Any]] = [
    {
        "id": "marcus-cold",
        "title": "The cold prospect",
        "blurb": "Break in cold, survive his objections, earn the truth, then ask for the business.",
        "character": "Marcus Webb",
        "role": "Operations Director",
        "company": "Bralton Freight",
        "company_size": "180 employees, 6 depots",
        "industry": "Regional logistics",
        "product": "a fleet maintenance and compliance platform",
        "seller_role": "Account Executive at Axlebridge Systems",
        "personality": "Blunt, time-poor, dry sense of humour, hates being handled.",
        "public": "Bralton has used the same maintenance provider for four years. Marcus has been Operations Director for six.",
        "hidden": (
            "The incumbent provider is not terrible on price — it misses response-time "
            "commitments roughly twice a month, and each miss idles a truck for a day "
            "(about £1,400 in lost revenue). Marcus personally pushed the last vendor "
            "change three years ago and it went badly; he was blamed internally, so "
            "switching feels personally risky. He can approve up to £30k; above that "
            "needs the FD, Cara. The contract renews in five months. Price is NOT his "
            "real objection — reputational risk is."
        ),
        "stages": [
            {
                "exercise_id": "cold-call",
                "objective": "Earn enough interest for Marcus to agree to a real conversation later.",
                "mood": "Rushed, mildly irritated at the interruption",
                "situation": "You have never spoken. He is walking into something else.",
                "objections": ["What's this regarding?", "We already have someone for that.", "Send me an email."],
            },
            {
                "exercise_id": "objection-handling",
                "objective": "Work through his resistance without arguing, and keep the conversation alive.",
                "mood": "Guarded, testing whether you are worth the time",
                "situation": "He took your follow-up call but is leading with reasons this won't work.",
                "objections": [
                    "We're happy with our current provider.",
                    "I don't see enough difference between you and them.",
                    "Switching sounds like a nightmare.",
                    "It's probably more expensive.",
                ],
            },
            {
                "exercise_id": "discovery",
                "objective": "Uncover what is actually wrong today and what it costs Bralton.",
                "mood": "Willing to talk, still cautious",
                "situation": "He agreed to a proper conversation. He will open up in proportion to your questions.",
                "objections": ["I'm not sure this is a priority right now.", "We've been burned before."],
            },
            {
                "exercise_id": "closing",
                "objective": "Resolve the last hesitation and secure a specific commitment.",
                "mood": "Interested but hesitant",
                "situation": "He likes what he has seen. Something is still holding him back.",
                "objections": [
                    "I like what you're showing me, I'm just not sure switching now makes sense.",
                    "I'd need to bring Cara in.",
                    "Can we revisit this at renewal?",
                ],
            },
        ],
    },
    {
        "id": "sarah-network",
        "title": "The networking connection",
        "blurb": "Meet a stranger at an event and turn curiosity into a real opportunity.",
        "character": "Sarah Lindqvist",
        "role": "Head of Customer Operations",
        "company": "Merrow Health",
        "company_size": "320 staff, 9 sites",
        "industry": "Private healthcare",
        "product": "a workforce scheduling and service-quality platform",
        "seller_role": "Senior Account Executive at Rota Systems",
        "personality": "Warm, curious, socially confident, allergic to being sold to at events.",
        "public": "You are both at a regional healthcare operations conference. You know nothing about her yet.",
        "hidden": (
            "Merrow's contact centre abandons roughly 18% of patient calls at peak, and "
            "complaints have doubled since they opened two new sites. Sarah's bonus is "
            "tied to patient satisfaction. She has an internal business case half-written "
            "but no data to support it. Her COO is sceptical of new software after a failed "
            "rollout. She has no budget until April but real influence over what gets funded. "
            "She will disengage instantly if pitched at during the event."
        ),
        "stages": [
            {
                "exercise_id": "networking",
                "objective": "Start a conversation, find common ground and earn permission to follow up.",
                "mood": "Sociable, between sessions, no agenda",
                "situation": "Coffee break at the conference. She is standing alone looking at the schedule.",
                "objections": ["I'm just here for the sessions really.", "We're not looking at anything new."],
            },
            {
                "exercise_id": "commercial-30s",
                "objective": "Explain concisely what you do, pitched to what you learned about her.",
                "mood": "Genuinely curious",
                "situation": "She has asked, plainly: remind me exactly what your company does?",
                "objections": ["I'm not sure that applies to us.", "How is that different to what we have?"],
            },
            {
                "exercise_id": "discovery",
                "objective": "Quantify the operational problem and map who decides.",
                "mood": "Open, professional, time-boxed to 30 minutes",
                "situation": "She agreed to a meeting after the event. What you learned while networking is fair game.",
                "objections": ["We have no budget this year.", "My COO won't want another system."],
            },
            {
                "exercise_id": "in-person",
                "objective": "Meet her face to face and build on everything you already know.",
                "mood": "Familiar, pleased you followed through",
                "situation": "You are at Merrow Health in person. She remembers your previous conversations.",
                "objections": ["My COO is joining us for ten minutes.", "Show me this actually works."],
            },
            {
                "exercise_id": "closing",
                "objective": "Convert her interest into a funded next step with the right people in the room.",
                "mood": "Supportive but constrained",
                "situation": "She wants this. She needs help getting it past her COO.",
                "objections": ["I can't sign anything.", "April is a long way off.", "I need to think about it."],
            },
        ],
    },
    {
        "id": "david-warm",
        "title": "The warm walk-in",
        "blurb": "An existing customer walks in wanting more — and brings a complaint with him.",
        "character": "David Okonjo",
        "role": "Owner",
        "company": "Okonjo & Sons Fabrication",
        "company_size": "34 staff, one workshop",
        "industry": "Metal fabrication",
        "product": "business insurance and risk cover",
        "seller_role": "Commercial Account Manager at Halbrook Insurance",
        "personality": "Direct, relationship-driven, remembers everything, loyal until crossed.",
        "public": "David has been a customer for three years on a basic liability policy. He walked in without an appointment.",
        "hidden": (
            "He is quoting for a contract that requires £5m public liability and employer's "
            "cover he does not currently hold — winning it would grow revenue 40%. A claim "
            "last year took eleven weeks to settle and nobody called him back, which he has "
            "never raised formally but has not forgotten. A broker at his trade association "
            "has offered a cheaper package. His wife handles the finances and is the real "
            "decision maker. He wants to stay if someone finally takes him seriously."
        ),
        "stages": [
            {
                "exercise_id": "in-person",
                "objective": "Handle the walk-in well, hear him out and find why he really came in.",
                "mood": "Friendly but with something on his mind",
                "situation": "He is standing at your desk, unannounced, on a busy afternoon.",
                "objections": ["I'm probably paying too much already.", "Last time nobody got back to me."],
            },
            {
                "exercise_id": "value-statement",
                "objective": "Explain why the additional cover matters in terms of his business, not policy features.",
                "mood": "Sceptical of insurance jargon",
                "situation": "He wants to know why he should pay more than he does today.",
                "objections": ["That sounds like upselling.", "Is this actually necessary?"],
            },
            {
                "exercise_id": "objection-handling",
                "objective": "Address the competing quote and the service history honestly.",
                "mood": "Testing your loyalty",
                "situation": "He mentions someone else has quoted him less.",
                "objections": [
                    "The association broker is cheaper.",
                    "Why should I stay after last year?",
                    "I need to talk to my wife.",
                ],
            },
            {
                "exercise_id": "closing",
                "objective": "Secure the upgrade with a clear commitment and a service promise he believes.",
                "mood": "Ready if reassured",
                "situation": "He is close. He needs to trust it will be different this time.",
                "objections": ["Let me sleep on it.", "Can you put that in writing?"],
            },
        ],
    },
]


def journey_by_id(jid: str) -> dict[str, Any] | None:
    return next((j for j in JOURNEYS if j["id"] == jid), None)


def stage_for(journey: dict[str, Any], exercise_id: str) -> dict[str, Any] | None:
    return next((s for s in journey["stages"] if s["exercise_id"] == exercise_id), None)


def public_journey(j: dict[str, Any]) -> dict[str, Any]:
    """Journey shape for the UI — the hidden dossier is never included."""
    return {
        "id": j["id"],
        "title": j["title"],
        "blurb": j["blurb"],
        "character": j["character"],
        "role": j["role"],
        "company": j["company"],
        "company_size": j["company_size"],
        "industry": j["industry"],
        "product": j["product"],
        "seller_role": j["seller_role"],
        "public": j["public"],
        "stages": [
            {
                "exercise_id": s["exercise_id"],
                "objective": s["objective"],
                "situation": s["situation"],
                "mood": s["mood"],
                "completed": False,
                "best_score": None,
                "simulation_id": None,
            }
            for s in j["stages"]
        ],
    }


def scenario_for_stage(journey: dict[str, Any], exercise_id: str) -> dict[str, Any] | None:
    """Build the scenario dict the prospect engine and brief screens expect."""
    stage = stage_for(journey, exercise_id)
    if not stage:
        return None
    return {
        "id": f"{journey['id']}::{exercise_id}",
        "journey_id": journey["id"],
        "product": journey["product"],
        "seller_role": journey["seller_role"],
        "product_sheet": None,
        "things_to_remember": [
            stage["situation"],
            f"{journey['character']} remembers every previous conversation you have had.",
        ],
        "prospect_name": journey["character"],
        "prospect_role": journey["role"],
        "company": journey["company"],
        "company_size": journey["company_size"],
        "industry": journey["industry"],
        "known": f"{journey['public']} {stage['situation']}",
        "hidden": journey["hidden"],
        "objective": stage["objective"],
        "personality": journey["personality"],
        "mood": stage["mood"],
        "objections": stage["objections"],
    }
