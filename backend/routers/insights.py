"""Attempt comparison and the org-level team view."""
from fastapi import APIRouter, HTTPException

from lib.analytics import build_skills, build_exercise_stats
from lib.catalog import exercise_by_id
from lib.db import db
from models.schemas import (
    Attempt,
    AttemptSeries,
    SkillStat,
    TeamMember,
    TeamView,
)

router = APIRouter(tags=["insights"])

# Assumed manager time per role-play, used to quantify coaching hours displaced.
MANAGER_MINUTES_PER_ROLEPLAY = 30


async def _completed(query: dict) -> list[dict]:
    return (
        await db.simulations.find({**query, "status": "completed"}, {"_id": 0})
        .sort("started_at", 1)
        .to_list(500)
    )


@router.post("/users/{user_id}/trained/{exercise_id}")
async def mark_trained(user_id: str, exercise_id: str):
    if not exercise_by_id(exercise_id):
        raise HTTPException(status_code=404, detail="Unknown exercise")
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.users.update_one({"id": user_id}, {"$addToSet": {"trained_skills": exercise_id}})
    trained = sorted(set(user.get("trained_skills") or []) | {exercise_id})
    return {"trained_skills": trained}


@router.get("/users/{user_id}/attempts/{exercise_id}", response_model=AttemptSeries)
async def attempt_series(user_id: str, exercise_id: str):
    exercise = exercise_by_id(exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Unknown exercise")
    sims = await _completed({"user_id": user_id, "exercise_id": exercise_id})

    attempts: list[Attempt] = []
    for i, s in enumerate(sims):
        ev = s.get("evaluation") or {}
        metrics = ev.get("metrics") or {}
        attempts.append(
            Attempt(
                index=i + 1,
                simulation_id=s["id"],
                started_at=s["started_at"],
                difficulty=s["difficulty"],
                difficulty_name=s["difficulty_name"],
                mode=s.get("mode", "guided"),
                prospect_name=s["scenario"].get("prospect_name", ""),
                overall_score=int(ev.get("overall_score") or 0),
                categories={
                    c["category"]: int(c["score"]) for c in ev.get("category_scores", [])
                },
                talk_ratio=int(metrics.get("talk_ratio") or 0),
                question_count=int(metrics.get("question_count") or 0),
            )
        )

    series = AttemptSeries(exercise_id=exercise_id, exercise_name=exercise["name"], attempts=attempts)
    if attempts:
        series.first_score = attempts[0].overall_score
        series.latest_score = attempts[-1].overall_score
        series.best_score = max(a.overall_score for a in attempts)
        series.delta = attempts[-1].overall_score - attempts[0].overall_score
    if len(attempts) >= 2:
        first, last = attempts[0].categories, attempts[-1].categories
        deltas = {c: last[c] - first[c] for c in last if c in first}
        series.category_deltas = deltas
        if deltas:
            series.most_improved = max(deltas, key=lambda k: deltas[k])
        if last:
            series.still_weakest = min(last, key=lambda k: last[k])
    return series


@router.get("/teams/{org}", response_model=TeamView)
async def team_view(org: str):
    users = await db.users.find({"org": org}, {"_id": 0}).to_list(200)
    if not users:
        raise HTTPException(status_code=404, detail="No reps in this organisation yet")

    members: list[TeamMember] = []
    all_sims: list[dict] = []
    for u in users:
        sims = await _completed({"user_id": u["id"]})
        all_sims.extend(sims)
        scores = [int((s.get("evaluation") or {}).get("overall_score", 0)) for s in sims if s.get("evaluation")]
        improvement = 0
        if len(scores) >= 2:
            half = max(1, len(scores) // 2)
            improvement = round(sum(scores[half:]) / len(scores[half:])) - round(
                sum(scores[:half]) / len(scores[:half])
            )
        skills = build_skills(sims)
        members.append(
            TeamMember(
                user_id=u["id"],
                name=u["name"],
                experience_level=u.get("experience_level", "New"),
                reps=len(sims),
                average_score=round(sum(scores) / len(scores)) if scores else None,
                latest_score=scores[-1] if scores else None,
                improvement=improvement,
                practice_seconds=sum(s.get("duration_seconds", 0) for s in sims),
                last_practice_date=u.get("last_practice_date"),
                weakest_skill=skills[-1]["category"] if skills else None,
                level=u.get("level", 1),
                xp=u.get("xp", 0),
            )
        )

    team_scores = [
        int((s.get("evaluation") or {}).get("overall_score", 0)) for s in all_sims if s.get("evaluation")
    ]
    team_improvement = 0
    if len(team_scores) >= 2:
        half = max(1, len(team_scores) // 2)
        team_improvement = round(sum(team_scores[half:]) / len(team_scores[half:])) - round(
            sum(team_scores[:half]) / len(team_scores[:half])
        )

    gaps = [SkillStat(**s) for s in build_skills(all_sims)][::-1][:6]
    return TeamView(
        org=org,
        members=sorted(members, key=lambda m: -m.reps),
        total_reps=len(all_sims),
        total_practice_seconds=sum(s.get("duration_seconds", 0) for s in all_sims),
        team_average=round(sum(team_scores) / len(team_scores)) if team_scores else None,
        team_improvement=team_improvement,
        skill_gaps=gaps,
        exercise_coverage=build_exercise_stats(all_sims),
        leaderboard=sorted(
            [m for m in members if m.average_score is not None],
            key=lambda m: -(m.average_score or 0),
        )[:10],
        manager_hours_saved=round(len(all_sims) * MANAGER_MINUTES_PER_ROLEPLAY / 60, 1),
    )
