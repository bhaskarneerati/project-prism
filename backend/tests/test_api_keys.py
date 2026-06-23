async def test_create_api_key(client, auth_headers):
    response = await client.post("/v1/api-keys", json={"name": "My Key"}, headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "My Key"
    assert body["is_active"] is True
    assert body["raw_key"].startswith("prism_")


async def test_list_api_keys_excludes_raw_key(client, auth_headers):
    await client.post("/v1/api-keys", json={"name": "My Key"}, headers=auth_headers)
    response = await client.get("/v1/api-keys", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert "raw_key" not in body[0]


async def test_revoke_api_key(client, auth_headers):
    create_response = await client.post(
        "/v1/api-keys", json={"name": "My Key"}, headers=auth_headers
    )
    key_id = create_response.json()["id"]
    response = await client.delete(f"/v1/api-keys/{key_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["is_active"] is False


async def test_api_keys_require_auth(client):
    response = await client.get("/v1/api-keys")
    assert response.status_code in (401, 403)
