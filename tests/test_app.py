import pytest
from httpx import AsyncClient
from httpx import ASGITransport
from src.app import app


@pytest.mark.asyncio
async def test_get_activities():
    """Test getting all activities"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data

        # Check structure
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)


@pytest.mark.asyncio
async def test_signup_for_activity():
    """Test signing up for an activity"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # First, get initial participants count
        response = await client.get("/activities")
        initial_data = response.json()
        initial_count = len(initial_data["Chess Club"]["participants"])

        # Sign up a new participant
        response = await client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up test@mergington.edu for Chess Club" in data["message"]

        # Verify the participant was added
        response = await client.get("/activities")
        updated_data = response.json()
        updated_count = len(updated_data["Chess Club"]["participants"])
        assert updated_count == initial_count + 1
        assert "test@mergington.edu" in updated_data["Chess Club"]["participants"]


@pytest.mark.asyncio
async def test_signup_nonexistent_activity():
    """Test signing up for a non-existent activity"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.post(
            "/activities/Nonexistent%20Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


@pytest.mark.asyncio
async def test_unregister_from_activity():
    """Test unregistering from an activity"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # First, sign up a participant
        await client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "removeme@mergington.edu"}
        )

        # Get initial count
        response = await client.get("/activities")
        initial_data = response.json()
        initial_count = len(initial_data["Programming Class"]["participants"])

        # Unregister the participant
        response = await client.delete(
            "/activities/Programming%20Class/unregister",
            params={"email": "removeme@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered removeme@mergington.edu from Programming Class" in data["message"]

        # Verify the participant was removed
        response = await client.get("/activities")
        updated_data = response.json()
        updated_count = len(updated_data["Programming Class"]["participants"])
        assert updated_count == initial_count - 1
        assert "removeme@mergington.edu" not in updated_data["Programming Class"]["participants"]


@pytest.mark.asyncio
async def test_unregister_nonexistent_activity():
    """Test unregistering from a non-existent activity"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.delete(
            "/activities/Nonexistent%20Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]


@pytest.mark.asyncio
async def test_unregister_not_registered_participant():
    """Test unregistering a participant who is not registered"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.delete(
            "/activities/Chess%20Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 404
        data = response.json()
        assert "Student not registered for this activity" in data["detail"]


@pytest.mark.asyncio
async def test_root_redirect():
    """Test root endpoint redirects to static/index.html"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        response = await client.get("/")
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/static/index.html"