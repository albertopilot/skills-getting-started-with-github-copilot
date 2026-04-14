import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


def test_root_redirect():
    """Test that GET / redirects to static HTML"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect
    assert response.headers["location"] == "/static/index.html"


def test_get_activities():
    """Test GET /activities returns all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0  # Should have activities

    # Check structure of first activity
    first_activity = next(iter(data.values()))
    assert "description" in first_activity
    assert "schedule" in first_activity
    assert "max_participants" in first_activity
    assert "participants" in first_activity
    assert isinstance(first_activity["participants"], list)


def test_signup_success():
    """Test successful signup for an activity"""
    # Use an activity that exists
    activity_name = "Chess Club"
    email = "test@example.com"

    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]

    # Verify the participant was added
    response = client.get("/activities")
    activities = response.json()
    assert email in activities[activity_name]["participants"]


def test_signup_duplicate():
    """Test signing up twice for the same activity fails"""
    activity_name = "Programming Class"
    email = "duplicate@example.com"

    # First signup
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200

    # Second signup should fail
    response = client.post(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"]


def test_signup_invalid_activity():
    """Test signup for non-existent activity fails"""
    response = client.post("/activities/NonExistent/signup?email=test@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_remove_participant_success():
    """Test successful removal of a participant"""
    activity_name = "Gym Class"
    email = "remove@example.com"

    # First signup
    client.post(f"/activities/{activity_name}/signup?email={email}")

    # Then remove
    response = client.delete(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Removed" in data["message"]

    # Verify removed
    response = client.get("/activities")
    activities = response.json()
    assert email not in activities[activity_name]["participants"]


def test_remove_participant_not_found():
    """Test removing a participant who is not signed up"""
    activity_name = "Chess Club"
    email = "notsigned@example.com"

    response = client.delete(f"/activities/{activity_name}/signup?email={email}")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Participant not found" in data["detail"]


def test_remove_invalid_activity():
    """Test removing from non-existent activity fails"""
    response = client.delete("/activities/NonExistent/signup?email=test@example.com")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "Activity not found" in data["detail"]


def test_integration_signup_remove():
    """Integration test: signup, verify, remove, verify"""
    activity_name = "Art Club"
    email = "integration@example.com"

    # Initial state
    response = client.get("/activities")
    activities = response.json()
    initial_count = len(activities[activity_name]["participants"])

    # Signup
    client.post(f"/activities/{activity_name}/signup?email={email}")
    response = client.get("/activities")
    activities = response.json()
    assert len(activities[activity_name]["participants"]) == initial_count + 1
    assert email in activities[activity_name]["participants"]

    # Remove
    client.delete(f"/activities/{activity_name}/signup?email={email}")
    response = client.get("/activities")
    activities = response.json()
    assert len(activities[activity_name]["participants"]) == initial_count
    assert email not in activities[activity_name]["participants"]