"""Criterion: no regression in the refactored analytics/insights hot paths.

- GET /api/users/{me}/dashboard returns a readiness score + label +
  recommendation + badges (build_readiness / earned_badges rule table).
- GET /api/teams/{org} returns members, skill_gaps, leaderboard,
  manager_hours_saved and lapsed_members (team_view / _team_member /
  _scores / _improvement / _lapsed_names helpers).
"""

import pytest

from .conftest import api_url, signup_user


@pytest.fixture
def rep_user():
    c, user_id, _ = signup_user("tscheck-dashboard-team-rep")
    yield c, user_id
    c.close()


def test_dashboard_returns_readiness_shape(rep_user):
    c, user_id = rep_user
    r = c.get(api_url(f"/users/{user_id}/dashboard"))
    assert r.status_code == 200, r.text
    body = r.json()

    assert "readiness" in body
    readiness = body["readiness"]
    assert isinstance(readiness["score"], (int, float))
    assert 0 <= readiness["score"] <= 100
    assert isinstance(readiness["label"], str) and readiness["label"]
    assert isinstance(readiness["recommendation"], str) and readiness["recommendation"]

    assert "user" in body
    assert "badges" in body["user"]
    assert isinstance(body["user"]["badges"], list)


def test_dashboard_rejects_cross_user_access(rep_user):
    c, _ = rep_user
    other_c, other_id, _ = signup_user("tscheck-dashboard-team-other")
    try:
        r = c.get(api_url(f"/users/{other_id}/dashboard"))
        assert r.status_code in (403, 404), r.text
    finally:
        other_c.close()


def test_team_view_returns_expected_shape_for_org(rep_user):
    c, user_id = rep_user
    # Guest/self-signup users land in the "Personal" org per seed facts; use
    # the caller's own org to guarantee a permitted, non-empty view.
    me = c.get(api_url(f"/users/{user_id}")).json()
    org = me.get("org") or "Personal"

    r = c.get(api_url(f"/teams/{org}"))
    assert r.status_code == 200, r.text
    body = r.json()

    for key in ("members", "skill_gaps", "leaderboard", "manager_hours_saved", "lapsed_members"):
        assert key in body, body

    assert isinstance(body["members"], list)
    assert isinstance(body["skill_gaps"], list)
    assert isinstance(body["leaderboard"], list)
    assert isinstance(body["manager_hours_saved"], (int, float))
    assert isinstance(body["lapsed_members"], list)
