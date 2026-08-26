"""Dashboard / progress aggregation over completed simulations."""
from collections.abc import Callable
from typing import Any

from lib.catalog import (
    BADGES,
    READINESS_WEIGHTS,
    DIFFICULTIES,
    EXERCISES,
    difficulty_by_level,
    exercise_by_id,
)


def _completed_scores(sims: list[dict]) -> list[int]:
    return [s["evaluation"]["overall_score"] for s in sims if s.get("evaluation")]


def build_skills(sims: list[dict]) -> list[dict[str, Any]]:
    buckets: dict[str, list[int]] = {}
    for s in sims:
        for cs in (s.get("evaluation") or {}).get("category_scores", []):
            buckets.setdefault(cs["category"], []).append(int(cs["score"]))
    out = []
    for cat, scores in buckets.items():
        avg = round(sum(scores) / len(scores))
        trend = 0
        if len(scores) >= 2:
            half = max(1, len(scores) // 2)
            trend = round(sum(scores[half:]) / len(scores[half:])) - round(
                sum(scores[:half]) / len(scores[:half])
            )
        out.append(
            {"category": cat, "average": avg, "attempts": len(scores), "trend": trend}
        )
    return sorted(out, key=lambda x: -x["average"])


def build_exercise_stats(sims: list[dict]) -> list[dict[str, Any]]:
    buckets: dict[str, list[int]] = {}
    for s in sims:
        ev = s.get("evaluation")
        if ev:
            buckets.setdefault(s["exercise_id"], []).append(int(ev["overall_score"]))
    stats = []
    for eid, scores in buckets.items():
        ex = exercise_by_id(eid)
        stats.append(
            {
                "exercise_id": eid,
                "exercise_name": ex["name"] if ex else eid,
                "attempts": len(scores),
                "average": round(sum(scores) / len(scores)),
                "best": max(scores),
            }
        )
    return sorted(stats, key=lambda x: -x["attempts"])


def recommend(sims: list[dict], skills: list[dict], unlocked: int) -> dict[str, Any]:
    if not sims:
        ex = exercise_by_id("cold-call")
        return {
            "exercise_id": "cold-call",
            "exercise_name": ex["name"],
            "difficulty": 2,
            "difficulty_name": difficulty_by_level(2)["name"],
            "reason": "Start with a Developing-level cold call — it exercises your opening, "
            "objection handling and ability to earn a next step in under five minutes.",
        }
    last = sims[-1]
    ev = last.get("evaluation") or {}
    rec_eid = ev.get("recommended_exercise_id") or "discovery"
    if not exercise_by_id(rec_eid):
        rec_eid = "discovery"
    rec_diff = int(ev.get("recommended_difficulty") or 2)
    rec_diff = max(1, min(unlocked, rec_diff))
    reason = ev.get("recommended_reason") or ""
    if skills:
        weakest = skills[-1]
        reason = (
            reason
            or f"{weakest['category']} is your lowest-scoring category at {weakest['average']}/100 "
            f"across {weakest['attempts']} scored simulations. Target it next."
        )
    ex = exercise_by_id(rec_eid)
    return {
        "exercise_id": rec_eid,
        "exercise_name": ex["name"],
        "difficulty": rec_diff,
        "difficulty_name": difficulty_by_level(rec_diff)["name"],
        "reason": reason,
    }


def unlocked_difficulty(xp: int, sims: list[dict]) -> int:
    unlocked = 1
    for d in DIFFICULTIES:
        if xp >= d["unlock_xp"]:
            unlocked = d["level"]
    return max(2, unlocked)


# Badge rules as data: one predicate per badge, so adding a badge is a one-line
# change and each rule stays independently readable.
BADGE_RULES: dict[str, Callable[[dict, list[dict], list[int]], bool]] = {
    "first-flight": lambda user, sims, scores: bool(sims),
    "committed": lambda user, sims, scores: len(sims) >= 5,
    "relentless": lambda user, sims, scores: len(sims) >= 15,
    "high-scorer": lambda user, sims, scores: any(s >= 80 for s in scores),
    "expert-tier": lambda user, sims, scores: any(s["difficulty"] >= 5 for s in sims),
    "streak-3": lambda user, sims, scores: (user.get("streak") or 0) >= 3,
}

# Category badges: badge id -> (category, minimum score in any single call)
CATEGORY_BADGES: dict[str, tuple[str, int]] = {
    "discovery-pro": ("Discovery", 85),
    "objection-slayer": ("Objection Handling", 80),
}


def _best_category_score(sims: list[dict], category: str) -> int:
    best = 0
    for sim in sims:
        for cs in (sim.get("evaluation") or {}).get("category_scores", []):
            if cs["category"] == category:
                best = max(best, int(cs["score"]))
    return best


def earned_badges(user: dict, sims: list[dict]) -> list[str]:
    ids: set[str] = set(user.get("badges") or [])
    scores = _completed_scores(sims)
    ids.update(bid for bid, rule in BADGE_RULES.items() if rule(user, sims, scores))
    ids.update(
        bid
        for bid, (category, minimum) in CATEGORY_BADGES.items()
        if _best_category_score(sims, category) >= minimum
    )
    return sorted(ids)


def badge_list(earned: list[str]) -> list[dict[str, Any]]:
    return [{**b, "earned": b["id"] in earned} for b in BADGES]


def summarize(sim: dict) -> dict[str, Any]:
    ev = sim.get("evaluation")
    return {
        "id": sim["id"],
        "exercise_id": sim["exercise_id"],
        "exercise_name": sim["exercise_name"],
        "difficulty": sim["difficulty"],
        "difficulty_name": sim["difficulty_name"],
        "prospect_name": sim["scenario"]["prospect_name"],
        "company": sim["scenario"]["company"],
        "status": sim["status"],
        "started_at": sim["started_at"],
        "duration_seconds": sim.get("duration_seconds", 0),
        "overall_score": ev["overall_score"] if ev else None,
        "turns": len(sim.get("transcript") or []),
    }


def build_nudge(user: dict, sims: list[dict]) -> dict[str, Any]:
    """Streak keeper: reps improve by repetition, so surface the gap explicitly."""
    from datetime import date

    last = user.get("last_practice_date")
    if not last or not sims:
        return {
            "level": "never",
            "days_since": None,
            "headline": "Start your first rep",
            "detail": "One five-minute call is enough to get a baseline score you can improve on.",
        }
    try:
        days = (date.today() - date.fromisoformat(last)).days
    except ValueError:
        days = 0
    streak = user.get("streak", 0)
    if days <= 1:
        return {
            "level": "fresh",
            "days_since": days,
            "headline": f"{streak}-day streak alive",
            "detail": "You practised today. Another rep at a higher difficulty compounds it.",
        }
    if days < 3:
        return {
            "level": "due",
            "days_since": days,
            "headline": f"You're due — {days} days since your last call",
            "detail": "Run one rep today to keep your streak and hold on to what you learned.",
        }
    return {
        "level": "lapsed",
        "days_since": days,
        "headline": f"{days} days without practice",
        "detail": (
            "Skills decay faster than most reps expect. One call on your weakest "
            "category restarts the streak."
        ),
    }


def _readiness_label(score: int, assessed: bool) -> str:
    if not assessed:
        return "Not assessed"
    if score >= 75:
        return "Customer ready"
    if score >= 55:
        return "Nearly ready"
    return "Keep practising"


def _readiness_recommendation(weakest: dict | None, assessed: bool) -> str:
    if weakest:
        return (
            f"{weakest['category']} is your weakest weighted competency at "
            f"{weakest['score']}/100 — practise it next."
        )
    if assessed:
        return "Broaden your coverage: several weighted competencies have no score yet."
    return "Complete your first simulation to generate a readiness score."


def _readiness_categories(skills: list[dict]) -> tuple[list[dict], float, float]:
    """Per-competency rows plus the weighted total and the weight actually covered."""
    by_cat = {s["category"]: s for s in skills}
    cats: list[dict] = []
    weighted_sum = 0.0
    covered_weight = 0.0
    for cat, weight in READINESS_WEIGHTS.items():
        stat = by_cat.get(cat)
        if stat:
            covered_weight += weight
            weighted_sum += stat["average"] * weight
        cats.append(
            {
                "category": cat,
                "score": stat["average"] if stat else 0,
                "weight": round(weight * 100),
                "attempts": stat["attempts"] if stat else 0,
            }
        )
    return cats, weighted_sum, covered_weight


def build_readiness(skills: list[dict], sims: list[dict]) -> dict[str, Any]:
    """Weighted 'can this rep talk to a real customer yet' score. Uncovered
    competencies are not silently ignored — they cap the achievable score."""
    cats, weighted_sum, covered_weight = _readiness_categories(skills)
    # Unpractised competencies count as zero, so breadth matters as much as depth.
    score = round(weighted_sum) if sims else 0
    scored = [c for c in cats if c["attempts"]]
    weakest = min(scored, key=lambda c: c["score"]) if scored else None
    label = _readiness_label(score, bool(sims))
    rec = _readiness_recommendation(weakest, bool(sims))
    return {
        "score": score,
        "label": label,
        "categories": cats,
        "biggest_opportunity": weakest["category"] if weakest else None,
        "recommendation": rec,
        "covered": len(scored),
        "total_weighted": len(READINESS_WEIGHTS),
    }


def score_improvement(scores: list[int]) -> int:
    """Second-half average minus first-half average — the simplest honest trend."""
    if len(scores) < 2:
        return 0
    half = max(1, len(scores) // 2)
    return round(sum(scores[half:]) / len(scores[half:])) - round(
        sum(scores[:half]) / len(scores[:half])
    )


def build_trend(sims: list[dict]) -> list[dict[str, Any]]:
    """Score-per-attempt series for the dashboard chart."""
    return [
        {
            "index": i + 1,
            "label": f"#{i + 1}",
            "score": int((s.get("evaluation") or {}).get("overall_score", 0)),
            "exercise_name": s["exercise_name"],
        }
        for i, s in enumerate(sims)
        if s.get("evaluation")
    ]


def build_headline_stats(scores: list[int], skills: list[dict]) -> dict[str, Any]:
    """The "how am I doing" block: averages, personal best, strongest/weakest."""
    return {
        "average_score": round(sum(scores) / len(scores)) if scores else 0,
        "recent_score": scores[-1] if scores else None,
        "improvement": score_improvement(scores),
        "personal_best": max(scores) if scores else None,
        "strongest_skill": skills[0] if skills else None,
        "weakest_skill": skills[-1] if len(skills) > 1 else None,
    }


def build_dashboard(user: dict, sims: list[dict]) -> dict[str, Any]:
    """sims: completed simulations, oldest first."""
    scores = _completed_scores(sims)
    skills = build_skills(sims)
    unlocked = unlocked_difficulty(user.get("xp", 0), sims)
    earned = earned_badges(user, sims)
    return {
        "user": {**user, "badges": earned},
        "completed": len(sims),
        **build_headline_stats(scores, skills),
        "trend": build_trend(sims),
        "skills": skills,
        "exercise_stats": build_exercise_stats(sims),
        "difficulty_reached": max([s["difficulty"] for s in sims], default=1),
        "unlocked_difficulty": unlocked,
        "recommendation": recommend(sims, skills, unlocked),
        "recent": [summarize(s) for s in reversed(sims)][:6],
        "total_practice_seconds": sum(s.get("duration_seconds", 0) for s in sims),
        "badges": badge_list(earned),
        "nudge": build_nudge(user, sims),
        "readiness": build_readiness(skills, sims),
    }


ALL_EXERCISES: list[dict] = EXERCISES
