"""Criterion: no regression in scenario generation / dashboard after helper
extraction (lib.llm.generate_scenario -> _variation_brief + _normalize_scenario;
lib.analytics.build_dashboard -> build_headline_stats/build_trend/score_improvement).

- 'Practice My Business' can save a profile and generate a custom scenario
  that starts a simulation.
- GET /api/users/{me}/dashboard returns completed, average_score,
  improvement, personal_best, trend[], skills[], readiness and badges
  consistent with the user's completed calls.
"""

import pytest

from .conftest import api_url, signup_user

TIMEOUT = 60.0


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-scenario-dashboard", timeout=TIMEOUT)
    yield c, user_id
    c.close()


def test_custom_scenario_generation_starts_simulation(rep_user):
    c, user_id = rep_user
    profile_payload = {
        "label": "tscheck-scenario-dashboard profile",
        "company": "Acme Robotics",
        "industry": "Manufacturing",
        "product": "Warehouse automation software",
        "product_description": "Software that schedules and tracks warehouse robots",
        "customer_type": "Mid-market logistics companies",
        "call_goal": "Book a demo",
        "common_objections": ["Too expensive", "Already have a vendor"],
    }
    profile_r = c.post(api_url(f"/users/{user_id}/sales-profiles"), json=profile_payload)
    assert profile_r.status_code == 200, profile_r.text
    profile = profile_r.json()

    scenario_r = c.post(
        api_url("/custom-scenarios"),
        json={"profile_id": profile["id"], "exercise_id": "cold-call", "difficulty": 2},
    )
    assert scenario_r.status_code == 200, scenario_r.text
    scenario = scenario_r.json()
    assert scenario["profile_id"] == profile["id"]
    assert scenario["prospect_name"], scenario
    assert scenario["company"], scenario

    sim_r = c.post(
        api_url("/simulations"),
        json={
            "user_id": user_id,
            "exercise_id": "cold-call",
            "difficulty": 2,
            "custom_scenario_id": scenario["id"],
        },
    )
    assert sim_r.status_code == 200, sim_r.text
    sim = sim_r.json()
    assert sim["status"] == "active"
    assert sim["scenario"]["company"] == scenario["company"]


def test_dashboard_fields_consistent_with_completed_calls(rep_user):
    c, user_id = rep_user

    # Zero completed calls yet -> completed should be 0 and shape must still
    # be fully present.
    empty = c.get(api_url(f"/users/{user_id}/dashboard"))
    assert empty.status_code == 200, empty.text
    empty_body = empty.json()
    for key in (
        "completed",
        "average_score",
        "improvement",
        "personal_best",
        "trend",
        "skills",
        "readiness",
    ):
        assert key in empty_body, empty_body
    assert empty_body["completed"] == 0, empty_body

    # Complete one simulation, then re-check the dashboard reflects it.
    start = c.post(
        api_url("/simulations"),
        json={
            "user_id": user_id,
            "exercise_id": "cold-call",
            "difficulty": 1,
            "scenario_id": "crm-vp-sales",
        },
    )
    assert start.status_code == 200, start.text
    sim_id = start.json()["id"]
    turn = c.post(
        api_url(f"/simulations/{sim_id}/turns"),
        json={"text": "Hi, do you have a minute to chat about your CRM setup?", "at": 1.0},
    )
    assert turn.status_code == 200, turn.text
    complete = c.post(api_url(f"/simulations/{sim_id}/complete"))
    assert complete.status_code == 200, complete.text
    overall_score = complete.json()["evaluation"]["overall_score"]

    after = c.get(api_url(f"/users/{user_id}/dashboard"))
    assert after.status_code == 200, after.text
    after_body = after.json()
    assert after_body["completed"] == 1, after_body
    assert after_body["average_score"] == pytest.approx(overall_score, abs=0.51), after_body
    assert after_body["personal_best"] == pytest.approx(overall_score, abs=0.51), after_body
    assert isinstance(after_body["trend"], list) and len(after_body["trend"]) >= 1, after_body
    assert isinstance(after_body["skills"], list), after_body
    assert "user" in after_body and "badges" in after_body["user"]
