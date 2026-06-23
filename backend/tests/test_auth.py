async def test_register_valid_email(client):
    response = await client.post(
        "/v1/auth/register", json={"email": "alice@example.com", "password": "secret123"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body


async def test_register_duplicate_email(client):
    payload = {"email": "bob@example.com", "password": "secret123"}
    await client.post("/v1/auth/register", json=payload)
    response = await client.post("/v1/auth/register", json=payload)
    assert response.status_code == 400


async def test_register_missing_fields(client):
    response = await client.post("/v1/auth/register", json={"email": "carol@example.com"})
    assert response.status_code == 422


async def test_login_valid_credentials(client):
    payload = {"email": "dave@example.com", "password": "secret123"}
    await client.post("/v1/auth/register", json=payload)
    response = await client.post("/v1/auth/login", json=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()


async def test_login_wrong_password(client):
    payload = {"email": "erin@example.com", "password": "secret123"}
    await client.post("/v1/auth/register", json=payload)
    response = await client.post(
        "/v1/auth/login", json={"email": "erin@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401


async def test_login_unknown_email(client):
    response = await client.post(
        "/v1/auth/login", json={"email": "nobody@example.com", "password": "secret123"}
    )
    assert response.status_code == 401
