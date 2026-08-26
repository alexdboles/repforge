"""LLM access: in-character prospect turns + post-call coaching analysis.

Uses the Emergent universal key via emergentintegrations (Claude Sonnet 4.5).
"""
import json
import os
import re
from typing import Any

from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage

from lib.catalog import SKILL_CATEGORIES

load_dotenv()

MODEL_PROVIDER = "anthropic"
MODEL_NAME = "claude-sonnet-4-5-20250929"
OPENAI_MODEL = "gpt-5.4"


class LlmUnavailable(Exception):
    """Raised when no LLM credential is configured."""


def _credential() -> tuple[str, str, str]:
    """The rep's own OpenAI key wins; the Emergent universal key is the fallback."""
    openai_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if openai_key:
        return openai_key, "openai", OPENAI_MODEL
    key = os.environ.get("EMERGENT_LLM_KEY", "").strip()
    if not key:
        raise LlmUnavailable(
            "No LLM credential is configured in backend/.env (OPENAI_API_KEY or "
            "EMERGENT_LLM_KEY) — the AI prospect and coaching engine require one."
        )
    return key, MODEL_PROVIDER, MODEL_NAME


def _chat(session_id: str, system_message: str) -> LlmChat:
    key, provider, model = _credential()
    return LlmChat(
        api_key=key, session_id=session_id, system_message=system_message
    ).with_model(provider, model)


def memory_block(prior: str) -> str:
    """What this character already told the rep in earlier calls of the same journey."""
    if not prior:
        return ""
    return (
        "PREVIOUS CONVERSATIONS WITH THIS SALESPERSON — you remember all of it:\n"
        f"{prior}\n\n"
        "MEMORY RULES:\n"
        "- Reference these earlier conversations naturally when relevant.\n"
        "- If they ask you something you already told them, say so plainly and a little "
        'impatiently (e.g. "I told you that when you called me"). Never pretend it is new.\n'
        "- What you already volunteered stays known. What they never earned is still hidden.\n\n"
    )


SPOKEN_RULES = """
SPOKEN CONVERSATION RULES — you are talking out loud on a live call, not writing:
- Usually 1-3 sentences. Most replies under 30 spoken words.
- Contractions always. Occasional brief acknowledgements: "yeah", "okay", "right", "sure", "hmm", "I see".
- Natural hesitation and unfinished thoughts are good. Silence and very short answers are allowed.
- No bullet points, no markdown, no stage directions like "(pauses)" or "[skeptical]" — express it in the wording.
- Do not repeat the salesperson's name. Do not end every reply with a question.
- Never sound polite-and-helpful like an assistant. You are the buyer.
- If they ramble, cut in: "Okay, hang on—", "Yeah, but what does that cost?"
- If they ask something vague, do not volunteer every useful fact.

BAD: "Thank you for that information. Could you elaborate on the potential benefits?"
GOOD: "Okay… but what does something like this actually cost?"
BAD: "I understand your proposition and appreciate your explanation."
GOOD: "Yeah, maybe. I'm just not sure we'd actually use it."
"""


def prospect_system_prompt(
    scenario: dict, exercise: dict, difficulty: dict, memory: str = ""
) -> str:
    return f"""You ARE {scenario['prospect_name']}, {scenario['prospect_role']} at {scenario['company']} ({scenario['company_size']}, {scenario['industry']}). You are NOT an AI assistant. You are a real human prospect on a live sales conversation.

The person speaking to you is a salesperson selling {scenario['product']}. The exercise context is: {exercise['name']} — {exercise['description']}

YOUR PERSONALITY: {scenario['personality']}
YOUR CURRENT MOOD: {scenario['mood']}

WHAT THE SALESPERSON ALREADY KNOWS (public): {scenario['known']}

YOUR PRIVATE SITUATION — the salesperson does NOT know any of this. Reveal individual pieces ONLY when a specific, well-earned question makes it natural. Never volunteer it, never dump it all at once:
{scenario['hidden']}

OBJECTIONS you may naturally raise when it fits: {'; '.join(scenario['objections'])}

DIFFICULTY: Level {difficulty['level']} — {difficulty['name']}. Behave exactly like this: {difficulty['behavior']}

{memory}{SPOKEN_RULES}
HARD RULES:
- Stay 100% in character. NEVER coach, evaluate, hint, or mention that this is training or that you are an AI. No meta-commentary, ever.
- Speak like a real person on a call: 1-3 sentences, contractions, occasional hesitation ("uh", "look", "honestly"), sometimes an incomplete thought. NEVER use bullet points, markdown, stage directions, or asterisks.
- React to quality. Vague claims → push back or ask "what does that actually mean?". Premature pitching → get impatient, look at the clock, or disengage. Genuinely insightful questions → open up a little more and get more engaged.
- Remember everything said earlier in this conversation and reference it when relevant.
- At higher difficulty you may interrupt, deflect, change subject or answer only part of a question.
- If the salesperson performs excellently and asks for a clear, specific commitment, you may agree — but only if they have earned it.
- If the salesperson is rambling or pitching without discovery, you may try to end the call.
- Output ONLY your spoken words. Nothing else.
- Not every conversation must end well. If the salesperson pitches without listening,
  argues, or wastes your time, you are entitled to stay unconvinced, decline, or end it."""


async def prospect_turn(
    simulation_id: str,
    scenario: dict,
    exercise: dict,
    difficulty: dict,
    transcript: list[dict],
    rep_line: str,
    prior: str = "",
) -> str:
    chat = _chat(
        f"sim-{simulation_id}",
        prospect_system_prompt(scenario, exercise, difficulty, memory_block(prior)),
    )
    history = "\n".join(
        f"{'SALESPERSON' if t['speaker'] == 'rep' else 'YOU'}: {t['text']}"
        for t in transcript
    )
    prefix = f"Conversation so far:\n{history}\n\n" if history else ""
    prompt = (
        f"{prefix}The salesperson just said: \"{rep_line}\"\n\n"
        "Reply with only your spoken response, in character."
    )
    reply = await chat.send_message(UserMessage(text=prompt))
    return _clean(reply)


async def prospect_opening(
    simulation_id: str,
    scenario: dict,
    exercise: dict,
    difficulty: dict,
    prior: str = "",
) -> str:
    chat = _chat(
        f"sim-{simulation_id}-open",
        prospect_system_prompt(scenario, exercise, difficulty, memory_block(prior)),
    )
    prompt = (
        "The conversation is just beginning and the salesperson has reached you. "
        "Say the very first thing you would say — a short, natural greeting or "
        "guarded acknowledgement fitting your mood and difficulty level. One or two "
        "sentences, spoken words only."
    )
    return _clean(await chat.send_message(UserMessage(text=prompt)))


def _clean(text: str) -> str:
    text = re.sub(r"\*[^*]*\*", "", text or "")
    text = text.replace("**", "").replace("- ", "").strip()
    return text or "Sorry, go on."


EVAL_SYSTEM = """You are a rigorous, experienced sales coach who trains new sales professionals in consultative selling: rapport, up-front agreements and agenda setting, layered questioning, discovery, active listening, pain and consequence, motivation, qualification (budget, decision process, decision makers, timeline), value articulation, questioning over pitching, objection handling, conversational control, tonality, confidence, pacing, closing and clear next steps.

You evaluate ONLY what actually happened in the transcript. Every strength, miss and coaching note must quote or paraphrase a real moment from the conversation. Never give generic advice like "ask better questions" — always name the specific moment and what to say instead. Be honest: a short, weak, or pitch-heavy conversation must receive low scores. Return ONLY valid JSON, no markdown fence, no commentary."""


EVAL_SCHEMA = """{
  "overall_score": 0-100 integer,
  "headline": "one sentence verdict on this specific conversation",
  "category_scores": [{"category": "one of the listed categories", "score": 0-100, "note": "one specific sentence citing the conversation"}],
  "strengths": [{"title": "short label", "detail": "what they did and why it worked, citing the moment", "quote": "their actual words or ''"}],
  "misses": [{"title": "short label", "detail": "what was missed and the cost", "quote": "the actual moment or ''", "better_approach": "a concrete alternative line or question they could have used"}],
  "coaching_priorities": [{"skill": "skill name", "why": "why this is the highest-impact fix for THIS rep", "drill": "a concrete practice instruction"}],
  "recommended_exercise_id": "one of: cold-call|discovery|objection-handling|closing|value-statement|commercial-30s|in-person|phone-sales",
  "recommended_difficulty": 1-5 integer,
  "recommended_reason": "one sentence explaining the recommendation",
  "metrics": {"talk_ratio": 0-100 integer percent of words spoken by the rep, "question_count": integer, "open_questions": integer, "closed_questions": integer, "filler_words": integer, "avg_response_words": integer, "longest_monologue_words": integer, "objection_count": integer, "objections_handled": integer},
  "moments": [{"tag": "one of: strong-question|missed-discovery|objection|premature-pitch|strong-value|buying-signal|closing-opportunity", "turn_index": integer index into the transcript array, "explanation": "why this moment is tagged this way and what it means"}],
  "objective_met": true or false,
  "objective_note": "one sentence on whether the stated objective was achieved"
}"""


async def evaluate_conversation(
    simulation_id: str,
    scenario: dict,
    exercise: dict,
    difficulty: dict,
    transcript: list[dict],
    duration_seconds: int,
    focus: list[str] | None = None,
    principles: list[str] | None = None,
    prior: str = "",
) -> dict[str, Any]:
    chat = _chat(f"eval-{simulation_id}", EVAL_SYSTEM)
    convo = "\n".join(
        f"[{i}] {'SALESPERSON' if t['speaker'] == 'rep' else scenario['prospect_name'].upper()}: {t['text']}"
        for i, t in enumerate(transcript)
    )
    categories = ", ".join(f'"{s}"' for s in SKILL_CATEGORIES)
    focus_line = ", ".join(focus or []) or "the categories that genuinely applied"
    taught = "\n".join(f"- {p}" for p in (principles or [])) or "- General consultative selling fundamentals"
    prompt = f"""EXERCISE: {exercise['name']} — evaluates {', '.join(exercise['skills'])}
DIFFICULTY: Level {difficulty['level']} ({difficulty['name']}) — {difficulty['behavior']}
PROSPECT: {scenario['prospect_name']}, {scenario['prospect_role']} at {scenario['company']}
REP'S OBJECTIVE: {scenario['objective']}
HIDDEN INFORMATION the rep could have discovered: {scenario['hidden']}
{("WHAT THIS PROSPECT ALREADY TOLD THE REP IN EARLIER CALLS (grade Relationship Memory: did they use it, or re-ask things they were already told?):" + chr(10) + prior + chr(10)) if prior else ""}CALL DURATION: {duration_seconds} seconds, {len(transcript)} turns.

TRANSCRIPT:
{convo}

WHAT THIS REP WAS TAUGHT before the call — grade these principles explicitly, and never penalise them for a "secret rule" outside this list or basic conversational competence:
{taught}

WEIGHTING: this is a {exercise['name']} exercise, so weight these categories most heavily and list them first: {focus_line}. Do not apply a generic template — a cold call is not graded like a close.

Two very different answers can both be excellent: judge whether the conversational objective was achieved, never whether they repeated a particular script.

Score these categories only where they genuinely apply to this exercise and conversation (include 6-10 of them, focus categories first): {categories}.

Judge how much of the hidden information the rep actually uncovered and whether they achieved the objective. Compute the metrics from the transcript itself. Return JSON matching exactly this shape:
{EVAL_SCHEMA}"""
    raw = await chat.send_message(UserMessage(text=prompt))
    return _normalize(_parse_json(raw))


def _normalize(data: dict[str, Any]) -> dict[str, Any]:
    """LLM JSON is best-effort: coerce shapes so a missing key never 502s a debrief."""
    out = dict(data)

    def as_list(key: str) -> list[dict[str, Any]]:
        value = out.get(key)
        return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []

    try:
        out["overall_score"] = max(0, min(100, int(out.get("overall_score") or 0)))
    except (TypeError, ValueError):
        out["overall_score"] = 0

    cats = []
    for c in as_list("category_scores"):
        try:
            score = max(0, min(100, int(c.get("score") or 0)))
        except (TypeError, ValueError):
            score = 0
        cats.append(
            {
                "category": str(c.get("category") or "General"),
                "score": score,
                "note": str(c.get("note") or ""),
            }
        )
    out["category_scores"] = cats

    out["strengths"] = [
        {
            "title": str(s.get("title") or "Strength"),
            "detail": str(s.get("detail") or ""),
            "quote": str(s.get("quote") or ""),
        }
        for s in as_list("strengths")
    ]
    out["misses"] = [
        {
            "title": str(s.get("title") or "Missed opportunity"),
            "detail": str(s.get("detail") or ""),
            "quote": str(s.get("quote") or ""),
            "better_approach": str(s.get("better_approach") or ""),
        }
        for s in as_list("misses")
    ]
    out["coaching_priorities"] = [
        {
            "skill": str(s.get("skill") or "Discovery"),
            "why": str(s.get("why") or s.get("reason") or ""),
            "drill": str(s.get("drill") or s.get("practice") or ""),
        }
        for s in as_list("coaching_priorities")
    ]

    moments = []
    for m in as_list("moments"):
        try:
            idx = int(m.get("turn_index") or 0)
        except (TypeError, ValueError):
            idx = 0
        moments.append(
            {
                "tag": str(m.get("tag") or "strong-question"),
                "turn_index": max(0, idx),
                "explanation": str(m.get("explanation") or ""),
            }
        )
    out["moments"] = moments

    metrics = out.get("metrics") if isinstance(out.get("metrics"), dict) else {}
    clean_metrics: dict[str, int] = {}
    for key in (
        "talk_ratio",
        "question_count",
        "open_questions",
        "closed_questions",
        "filler_words",
        "avg_response_words",
        "longest_monologue_words",
        "objection_count",
        "objections_handled",
    ):
        try:
            clean_metrics[key] = max(0, int(metrics.get(key) or 0))
        except (TypeError, ValueError):
            clean_metrics[key] = 0
    clean_metrics["talk_ratio"] = min(100, clean_metrics["talk_ratio"])
    out["metrics"] = clean_metrics

    out["headline"] = str(out.get("headline") or "")
    out["objective_note"] = str(out.get("objective_note") or "")
    out["objective_met"] = bool(out.get("objective_met"))
    out["recommended_reason"] = str(out.get("recommended_reason") or "")
    out["recommended_exercise_id"] = str(out.get("recommended_exercise_id") or "discovery")
    try:
        out["recommended_difficulty"] = max(1, min(5, int(out.get("recommended_difficulty") or 2)))
    except (TypeError, ValueError):
        out["recommended_difficulty"] = 2
    return out


def _parse_json(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            return json.loads(text[start : end + 1])
        raise


# ---------------- custom scenario generation (Practice My Business) ----------------

SCENARIO_SYSTEM = """You design realistic sales roleplay scenarios for a sales training simulator. You invent a specific prospect for the rep's REAL business, based on the business profile they give you.

Two strictly separated information sets:
- "known": what the rep legitimately knows before the call. Never put discoverable pain, budget, timeline or decision-maker detail here.
- "hidden": what only the AI prospect knows. This is the material the rep must earn through good questions. Make it specific, numeric where sensible, and include at least one reason the prospect resists change.

Prospects must be plausible for the stated customer type and industry. Never mention the simulator or coaching. Return ONLY valid JSON, no markdown fence."""

SCENARIO_SHAPE = """{
  "prospect_name": "realistic full name",
  "prospect_role": "job title",
  "company": "invented company name",
  "company_size": "e.g. '40 employees, $12M revenue'",
  "industry": "industry",
  "known": "2-3 sentences of pre-call context the rep legitimately knows",
  "hidden": "4-6 sentences of specific private detail: the real problem and what it costs, current provider/spend, budget reality, decision makers, timeline pressure, and a specific reason they resist changing",
  "objective": "one sentence stating what success on this call means",
  "mood": "short mood description",
  "personality": "one sentence on how they communicate",
  "objections": ["3-4 objections this specific prospect would actually raise"]
}"""


async def generate_scenario(
    profile: dict[str, Any],
    exercise: dict[str, Any],
    difficulty: dict[str, Any],
    variation: dict[str, str],
    preferences: str = "",
) -> dict[str, Any]:
    chat = _chat(f"scenario-{uuid_hint()}", SCENARIO_SYSTEM)
    objections = ", ".join(profile.get("common_objections") or []) or "none supplied"
    prompt = f"""THE REP'S REAL BUSINESS
Company: {profile.get('company')} ({profile.get('industry')})
Sells: {profile.get('product')} — {profile.get('product_description')}
Problems it solves: {profile.get('problems_solved')}
Benefits: {profile.get('benefits')}
Differentiators: {profile.get('differentiators')}
Sells to: {profile.get('customer_type')} in {profile.get('customer_industries')}; typical buyers: {profile.get('customer_titles')}
Ideal customer: {profile.get('ideal_customer')}
Typical call goal: {profile.get('call_goal')} · Sales cycle: {profile.get('sales_cycle')}
Pricing: {profile.get('pricing')}
Competitors: {profile.get('competitors')} — their advantages: {profile.get('competitor_advantages')}; our advantages: {profile.get('our_advantages')}
Objections the rep actually hears: {objections}
Methodology: {profile.get('methodology')}
Extra context: {profile.get('extra_context')}

EXERCISE: {exercise['name']} — {exercise['description']}
DIFFICULTY: Level {difficulty['level']} ({difficulty['name']}) — {difficulty['behavior']}

VARIATION REQUIREMENTS (make this scenario clearly different from a default one):
- Prospect personality: {variation['personality']}
- Interest level: {variation['interest']}
- Urgency: {variation['urgency']}
- Decision authority: {variation['authority']}
- Incumbent situation: {variation['incumbent']}
- Communication style: {variation['style']}
{f"- Rep's requested focus: {preferences}" if preferences else ""}

Return JSON exactly in this shape:
{SCENARIO_SHAPE}"""
    raw = await chat.send_message(UserMessage(text=prompt))
    data = _parse_json(raw)
    data["objections"] = [str(o) for o in (data.get("objections") or [])][:5]
    for key in (
        "prospect_name",
        "prospect_role",
        "company",
        "company_size",
        "industry",
        "known",
        "hidden",
        "objective",
        "mood",
        "personality",
    ):
        data[key] = str(data.get(key) or "")
    return data


def uuid_hint() -> str:
    import uuid as _uuid

    return str(_uuid.uuid4())[:8]


HINT_SYSTEM = """You are a live sales coach sitting beside a trainee during a practice call. You never speak to the prospect. You tell the trainee what to accomplish next in the conversation, based on what the prospect just said and where the conversation currently is.

Be concrete and short. Name the stage of the conversation, the immediate goal, and one example of how they could phrase it. Never invent facts about the prospect. Never tell the trainee what the prospect is secretly thinking or hiding. Return ONLY valid JSON."""


async def coaching_hint(
    simulation_id: str,
    scenario: dict,
    exercise: dict,
    difficulty: dict,
    transcript: list[dict],
    principles: list[str] | None = None,
) -> dict[str, Any]:
    chat = _chat(f"hint-{simulation_id}-{len(transcript)}", HINT_SYSTEM)
    convo = "\n".join(
        f"{'SALESPERSON' if t['speaker'] == 'rep' else scenario['prospect_name'].upper()}: {t['text']}"
        for t in transcript[-8:]
    )
    taught = ", ".join(principles or []) or "consultative selling fundamentals"
    prompt = f"""EXERCISE: {exercise['name']} — objective: {scenario['objective']}
PRINCIPLES THE TRAINEE WAS TAUGHT: {taught}
DIFFICULTY: Level {difficulty['level']} ({difficulty['name']})

CONVERSATION SO FAR:
{convo or "(the call has just connected)"}

Return JSON:
{{"stage": "2-4 word name for where the conversation is (e.g. 'Opening', 'Uncovering impact')",
 "goal": "one sentence telling the trainee what to accomplish with their next turn",
 "example": "one sentence they could actually say, in natural spoken language",
 "avoid": "one short warning about the most likely mistake right now"}}"""
    raw = await chat.send_message(UserMessage(text=prompt))
    data = _parse_json(raw)
    return {
        "stage": str(data.get("stage") or "Next move"),
        "goal": str(data.get("goal") or ""),
        "example": str(data.get("example") or ""),
        "avoid": str(data.get("avoid") or ""),
    }


async def moment_reprise(
    simulation_id: str,
    scenario: dict,
    exercise: dict,
    difficulty: dict,
    transcript: list[dict],
    miss: dict,
) -> dict:
    """Retry That Moment: rebuild the situation just before a coaching moment and
    the buyer line that re-opens it, so the rep can practise that exact beat."""
    chat = _chat(
        f"moment-{simulation_id}",
        "You are a sales-training designer. You set up a single conversational "
        "moment for a rep to practise again. You never coach inside the buyer's "
        "words and never reveal the buyer's hidden information.",
    )
    convo = "\n".join(
        f"{'SALESPERSON' if t['speaker'] == 'rep' else scenario.get('prospect_name', 'BUYER')}: {t['text']}"
        for t in transcript[-14:]
    )
    prompt = f"""BUYER: {scenario.get('prospect_name')}, {scenario.get('prospect_role')} at {scenario.get('company')}
EXERCISE: {exercise['name']} · Level {difficulty['level']} {difficulty['name']}

CONVERSATION THAT HAPPENED:
{convo}

THE COACHING MOMENT TO REPLAY:
title: {miss.get('title')}
what went wrong: {miss.get('detail')}
quoted from the call: {miss.get('quote')}
better approach: {miss.get('better_approach')}

Return JSON:
{{"situation": "1-2 sentences of neutral setup, addressed to the rep, describing where the conversation is (no coaching advice)",
 "objective": "one sentence telling the rep what to accomplish in this retry",
 "buyer_line": "the buyer's spoken line that re-opens this exact moment — 1-2 sentences, natural spoken English, in character, no stage directions"}}"""
    data = _parse_json(await chat.send_message(UserMessage(text=prompt)))
    return {
        "situation": str(data.get("situation") or ""),
        "objective": str(data.get("objective") or "Handle this moment better than last time."),
        "buyer_line": _clean(str(data.get("buyer_line") or miss.get("quote") or "")),
    }
