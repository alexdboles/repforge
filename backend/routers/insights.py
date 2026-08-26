"""Attempt comparison and the org-level team view."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from lib.analytics import build_skills, build_exercise_stats
from lib.catalog import difficulty_by_level, exercise_by_id
from lib.auth import current_user, require_org, require_self
from lib.db import db
from models.schemas import (
    Assignment,
    AssignmentCreate,
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
async def mark_trained(user_id: str, exercise_id: str, me: dict = Depends(current_user)):
    require_self(user_id, me)
    if not exercise_by_id(exercise_id):
        raise HTTPException(status_code=404, detail="Unknown exercise")
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await db.users.update_one({"id": user_id}, {"$addToSet": {"trained_skills": exercise_id}})
    trained = sorted(set(user.get("trained_skills") or []) | {exercise_id})
    return {"trained_skills": trained}


@router.get("/users/{user_id}/attempts/{exercise_id}", response_model=AttemptSeries)
async def attempt_series(user_id: str, exercise_id: str, me: dict = Depends(current_user)):
    require_self(user_id, me)
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


def _scores(sims: list[dict]) -> list[int]:
    return [
        int((s.get("evaluation") or {}).get("overall_score", 0))
        for s in sims
        if s.get("evaluation")
    ]


def _improvement(scores: list[int]) -> int:
    """Second half average minus first half average — the simplest honest trend."""
    if len(scores) < 2:
        return 0
    half = max(1, len(scores) // 2)
    return round(sum(scores[half:]) / len(scores[half:])) - round(
        sum(scores[:half]) / len(scores[:half])
    )


def _team_member(user: dict, sims: list[dict]) -> TeamMember:
    scores = _scores(sims)
    skills = build_skills(sims)
    return TeamMember(
        user_id=user["id"],
        name=user["name"],
        experience_level=user.get("experience_level", "New"),
        reps=len(sims),
        average_score=round(sum(scores) / len(scores)) if scores else None,
        latest_score=scores[-1] if scores else None,
        improvement=_improvement(scores),
        practice_seconds=sum(s.get("duration_seconds", 0) for s in sims),
        last_practice_date=user.get("last_practice_date"),
        weakest_skill=skills[-1]["category"] if skills else None,
        level=user.get("level", 1),
        xp=user.get("xp", 0),
    )


def _lapsed_names(members: list[TeamMember], days: int = 3) -> list[str]:
    """Reps a manager should nudge: never practised, or idle for `days`+."""
    out: list[str] = []
    for member in members:
        if not member.last_practice_date:
            out.append(member.name)
            continue
        try:
            if (date.today() - date.fromisoformat(member.last_practice_date)).days >= days:
                out.append(member.name)
        except ValueError:
            continue
    return out


@router.get("/teams/{org}", response_model=TeamView)
async def team_view(org: str, me: dict = Depends(current_user)):
    require_org(org, me)
    users = await db.users.find({"org": org}, {"_id": 0, "password": 0}).to_list(200)
    if not users:
        raise HTTPException(status_code=404, detail="No reps in this organisation yet")

    members: list[TeamMember] = []
    all_sims: list[dict] = []
    for user in users:
        sims = await _completed({"user_id": user["id"]})
        all_sims.extend(sims)
        members.append(_team_member(user, sims))

    team_scores = _scores(all_sims)
    assignments = (
        await db.assignments.find({"org": org}, {"_id": 0}).sort("created_at", -1).to_list(200)
    )
    return TeamView(
        org=org,
        members=sorted(members, key=lambda m: -m.reps),
        total_reps=len(all_sims),
        total_practice_seconds=sum(s.get("duration_seconds", 0) for s in all_sims),
        team_average=round(sum(team_scores) / len(team_scores)) if team_scores else None,
        team_improvement=_improvement(team_scores),
        skill_gaps=[SkillStat(**s) for s in build_skills(all_sims)][::-1][:6],
        exercise_coverage=build_exercise_stats(all_sims),
        leaderboard=sorted(
            [m for m in members if m.average_score is not None],
            key=lambda m: -(m.average_score or 0),
        )[:10],
        manager_hours_saved=round(len(all_sims) * MANAGER_MINUTES_PER_ROLEPLAY / 60, 1),
        assignments=[Assignment(**a) for a in assignments],
        lapsed_members=_lapsed_names(members),
    )


# ---------------- assigned training ----------------


@router.post("/assignments", response_model=Assignment)
async def create_assignment(payload: AssignmentCreate, me: dict = Depends(current_user)):
    user = await db.users.find_one({"id": payload.user_id}, {"_id": 0, "password": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Rep not found")
    # Tenant boundary: you may only assign training inside your own organisation.
    require_org(user.get("org", ""), me)
    if payload.org:
        require_org(payload.org, me)
    exercise = exercise_by_id(payload.exercise_id)
    if not exercise:
        raise HTTPException(status_code=404, detail="Unknown exercise")
    difficulty = difficulty_by_level(payload.difficulty)
    if not difficulty:
        raise HTTPException(status_code=422, detail="Difficulty must be 1-5")
    assignment = Assignment(
        user_id=payload.user_id,
        user_name=user["name"],
        org=payload.org or user.get("org", ""),
        exercise_id=exercise["id"],
        exercise_name=exercise["name"],
        difficulty=difficulty["level"],
        difficulty_name=difficulty["name"],
        note=payload.note,
        assigned_by=payload.assigned_by,
    )
    await db.assignments.insert_one(assignment.model_dump())
    return assignment


@router.get("/users/{user_id}/assignments", response_model=list[Assignment])
async def list_user_assignments(user_id: str, me: dict = Depends(current_user)):
    require_self(user_id, me)
    docs = (
        await db.assignments.find({"user_id": user_id}, {"_id": 0})
        .sort("created_at", -1)
        .to_list(100)
    )
    return [Assignment(**d) for d in docs]


@router.get("/teams/{org}/assignments", response_model=list[Assignment])
async def list_team_assignments(org: str, me: dict = Depends(current_user)):
    require_org(org, me)
    docs = (
        await db.assignments.find({"org": org}, {"_id": 0}).sort("created_at", -1).to_list(200)
    )
    return [Assignment(**d) for d in docs]


@router.delete("/assignments/{assignment_id}")
async def delete_assignment(assignment_id: str, me: dict = Depends(current_user)):
    doc = await db.assignments.find_one({"id": assignment_id}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Assignment not found")
    require_org(doc.get("org", ""), me)
    res = await db.assignments.delete_one({"id": assignment_id})
    if not res.deleted_count:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return {"deleted": True}
