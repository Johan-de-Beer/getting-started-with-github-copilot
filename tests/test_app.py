from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_get_activities_returns_seeded_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert "Chess Club" in response.json()
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client):
    email = "new.student@mergington.edu"

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Chess Club"}
    assert email in client.get("/activities").json()["Chess Club"]["participants"]


def test_signup_rejects_duplicate_without_changing_participants(client):
    email = "michael@mergington.edu"
    original_participants = activities["Chess Club"]["participants"].copy()

    response = client.post("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 400
    assert activities["Chess Club"]["participants"] == original_participants


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post("/activities/Unknown%20Activity/signup", params={"email": "student@example.com"})

    assert response.status_code == 404


def test_unregister_removes_participant(client):
    email = "michael@mergington.edu"

    response = client.delete("/activities/Chess%20Club/signup", params={"email": email})

    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from Chess Club"}
    assert email not in client.get("/activities").json()["Chess Club"]["participants"]


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete("/activities/Unknown%20Activity/signup", params={"email": "student@example.com"})

    assert response.status_code == 404


def test_unregister_returns_not_found_for_unregistered_participant(client):
    response = client.delete(
        "/activities/Chess%20Club/signup",
        params={"email": "not.registered@mergington.edu"},
    )

    assert response.status_code == 404


@pytest.mark.parametrize("method", ["post", "delete"])
def test_signup_routes_require_email_query_parameter(client, method):
    response = getattr(client, method)("/activities/Chess%20Club/signup")

    assert response.status_code == 422