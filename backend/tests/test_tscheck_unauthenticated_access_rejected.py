"""Criterion: Unauthenticated API access is rejected.

Without the session cookie, GET /api/users/{anyId}/dashboard, GET /api/simulations/{anyId},
POST /api/voice/speak and POST /api/simulations must all return 401.
"""

import httpx

from .conftest import api_url


def test_unauthenticated_requests_return_401():
    with httpx.Client(timeout=30.0) as c:
        r1 = c.get(api_url("/users/tscheck-any-id/dashboard"))
        assert r1.status_code == 401, r1.text

        r2 = c.get(api_url("/simulations/tscheck-any-id"))
        assert r2.status_code == 401, r2.text

        r3 = c.post(
            api_url("/voice/speak"), json={"text": "hello", "persona": "default"}
        )
        assert r3.status_code == 401, r3.text

        r4 = c.post(
            api_url("/simulations"),
            json={
                "user_id": "tscheck-any-id",
                "exercise_id": "cold-call",
                "difficulty": 1,
                "scenario_id": "crm-vp-sales",
            },
        )
        assert r4.status_code == 401, r4.text
