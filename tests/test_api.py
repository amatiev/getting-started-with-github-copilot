"""
Tests for Mergington High School API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the API"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": activity["description"],
            "schedule": activity["schedule"],
            "max_participants": activity["max_participants"],
            "participants": activity["participants"].copy()
        }
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name, activity in original_activities.items():
        activities[name]["participants"] = activity["participants"].copy()


def test_root_redirect(client):
    """Test that root redirects to static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    
    # Check that we have activities
    assert len(data) > 0
    
    # Verify structure of an activity
    assert "Soccer Team" in data
    assert "description" in data["Soccer Team"]
    assert "schedule" in data["Soccer Team"]
    assert "max_participants" in data["Soccer Team"]
    assert "participants" in data["Soccer Team"]


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    response = client.post("/activities/Soccer%20Team/signup?email=test@mergington.edu")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "test@mergington.edu" in data["message"]
    assert "Soccer Team" in data["message"]
    
    # Verify participant was added
    assert "test@mergington.edu" in activities["Soccer Team"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signup for an activity that doesn't exist"""
    response = client.post("/activities/Underwater%20Basket%20Weaving/signup?email=test@mergington.edu")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_signup_duplicate_participant(client):
    """Test that a student cannot sign up twice for the same activity"""
    email = "duplicate@mergington.edu"
    
    # First signup should succeed
    response1 = client.post(f"/activities/Soccer%20Team/signup?email={email}")
    assert response1.status_code == 200
    
    # Second signup should fail
    response2 = client.post(f"/activities/Soccer%20Team/signup?email={email}")
    assert response2.status_code == 400
    data = response2.json()
    assert data["detail"] == "Student already signed up for this activity"


def test_unregister_from_activity_success(client):
    """Test successful unregistration from an activity"""
    # First, sign up a student
    email = "test@mergington.edu"
    client.post(f"/activities/Soccer%20Team/signup?email={email}")
    
    # Then unregister
    response = client.delete(f"/activities/Soccer%20Team/unregister?email={email}")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert "Soccer Team" in data["message"]
    
    # Verify participant was removed
    assert email not in activities["Soccer Team"]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistration from an activity that doesn't exist"""
    response = client.delete("/activities/Underwater%20Basket%20Weaving/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_unregister_participant_not_registered(client):
    """Test unregistering a student who is not registered"""
    response = client.delete("/activities/Soccer%20Team/unregister?email=notregistered@mergington.edu")
    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Student not registered for this activity"


def test_signup_and_unregister_workflow(client):
    """Test complete workflow of signup and unregister"""
    email = "workflow@mergington.edu"
    activity = "Math Club"
    
    # Get initial participant count
    initial_count = len(activities[activity]["participants"])
    
    # Sign up
    signup_response = client.post(f"/activities/{activity}/signup?email={email}")
    assert signup_response.status_code == 200
    assert len(activities[activity]["participants"]) == initial_count + 1
    
    # Unregister
    unregister_response = client.delete(f"/activities/{activity}/unregister?email={email}")
    assert unregister_response.status_code == 200
    assert len(activities[activity]["participants"]) == initial_count


def test_multiple_students_signup(client):
    """Test multiple students signing up for the same activity"""
    activity = "Chess Club"
    emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
    
    initial_count = len(activities[activity]["participants"])
    
    for email in emails:
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
    
    assert len(activities[activity]["participants"]) == initial_count + len(emails)
    
    for email in emails:
        assert email in activities[activity]["participants"]
