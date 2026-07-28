from app.db.models import User
from app.core.security import verify_password


def test_register_user_success(client, db_session):
    """Test successful user registration and password hashing."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "trader_john",
            "email": "john@proflo.ai",
            "password": "SecurePassword123!"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["message"] == "User created successfully"

    # Verify user saved to DB with hashed password
    user = db_session.query(User).filter(User.username == "trader_john").first()
    assert user is not None
    assert user.email == "john@proflo.ai"
    assert user.hashed_password != "SecurePassword123!"  # Never store raw password
    assert verify_password("SecurePassword123!", user.hashed_password) is True


def test_register_duplicate_user_fails(client):
    """Test that registering duplicate username or email returns 400."""
    payload = {
        "username": "trader_jane",
        "email": "jane@proflo.ai",
        "password": "Password123!"
    }
    # Initial registration
    client.post("/api/v1/auth/register", json=payload)

    # Duplicate registration attempt
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Username or Email already registered"


def test_login_success(client):
    """Test login with correct credentials yields valid Bearer token."""
    # 1. Register user
    client.post(
        "/api/v1/auth/register",
        json={"username": "alex", "email": "alex@proflo.ai", "password": "AlexPassword123"}
    )

    # 2. Login (FastAPI OAuth2 expects form-encoded data)
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "alex", "password": "AlexPassword123"}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"


def test_login_wrong_password_fails(client):
    """Test login with incorrect password returns error."""
    client.post(
        "/api/v1/auth/register",
        json={"username": "alex", "email": "alex@proflo.ai", "password": "AlexPassword123"}
    )

    response = client.post(
        "/api/v1/auth/login",
        data={"username": "alex", "password": "WrongPassword!"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect username or password"


def test_protected_route_access(client):
    """Test access to /auth/me with valid and invalid JWT tokens."""
    # 1. Register & Login
    client.post(
        "/api/v1/auth/register",
        json={"username": "sam", "email": "sam@proflo.ai", "password": "SamPassword123"}
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "sam", "password": "SamPassword123"}
    )
    token = login_res.json()["access_token"]

    # 2. Attempt access without token -> Should fail 401
    unauth_response = client.get("/api/v1/auth/me")
    assert unauth_response.status_code == 401

    # 3. Attempt access with valid token -> Should succeed 200
    headers = {"Authorization": f"Bearer {token}"}
    auth_response = client.get("/api/v1/auth/me", headers=headers)
    assert auth_response.status_code == 200
    user_data = auth_response.json()
    assert user_data["username"] == "sam"
    assert user_data["email"] == "sam@proflo.ai"