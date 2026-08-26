"""Dashboard / progress aggregation over completed simulations."""
from typing import Any

from lib.catalog import (
    BADGES,
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


def earned_badges(user: dict, sims: list[dict]) -> list[str]:
    ids: set[str] = set(user.get("badges") or [])
    scores = _completed_scores(sims)
    if sims:
        ids.add("first-flight")
    if len(sims) >= 5:
        ids.add("committed")
    if len(sims) >= 15:
        ids.add("relentless")
    if any(s >= 80 for s in scores):
        ids.add("high-scorer")
    if any(s["difficulty"] >= 5 for s in sims):
        ids.add("expert-tier")
    if (user.get("streak") or 0) >= 3:
        ids.add("streak-3")
    for s in sims:
        for cs in (s.get("evaluation") or {}).get("category_scores", []):
            if cs["category"] == "Discovery" and cs["score"] >= 85:
                ids.add("discovery-pro")
            if cs["category"] == "Objection Handling" and cs["score"] >= 80:
                ids.add("objection-slayer")
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


def build_dashboard(user: dict, sims: list[dict]) -> dict[str, Any]:
    """sims: completed simulations, oldest first."""
    scores = _completed_scores(sims)
    skills = build_skills(sims)
    unlocked = unlocked_difficulty(user.get("xp", 0), sims)
    improvement = 0
    if len(scores) >= 2:
        half = max(1, len(scores) // 2)
        improvement = round(sum(scores[half:]) / len(scores[half:])) - round(
            sum(scores[:half]) / len(scores[:half])
        )
    trend = [
        {
            "index": i + 1,
            "label": f"#{i + 1}",
            "score": int((s.get("evaluation") or {}).get("overall_score", 0)),
            "exercise_name": s["exercise_name"],
        }
        for i, s in enumerate(sims)
        if s.get("evaluation")
    ]
    earned = earned_badges(user, sims)
    return {
        "user": {**user, "badges": earned},
        "completed": len(sims),
        "average_score": round(sum(scores) / len(scores)) if scores else 0,
        "recent_score": scores[-1] if scores else None,
        "improvement": improvement,
        "personal_best": max(scores) if scores else None,
        "strongest_skill": skills[0] if skills else None,
        "weakest_skill": skills[-1] if len(skills) > 1 else None,
        "trend": trend,
        "skills": skills,
        "exercise_stats": build_exercise_stats(sims),
        "difficulty_reached": max([s["difficulty"] for s in sims], default=1),
        "unlocked_difficulty": unlocked,
        "recommendation": recommend(sims, skills, unlocked),
        "recent": [summarize(s) for s in reversed(sims)][:6],
        "total_practice_seconds": sum(s.get("duration_seconds", 0) for s in sims),
        "badges": badge_list(earned),
        "nudge": build_nudge(user, sims),
    }


ALL_EXERCISES: list[dict] = EXERCISES
