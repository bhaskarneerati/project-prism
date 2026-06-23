import uuid
from datetime import datetime, timezone

from app.db.models.request_log import RequestLog


async def _setup_user_route_key(client, auth_headers):
    me_response = await client.get("/v1/auth/me", headers=auth_headers)
    user_id = me_response.json()["id"]

    route_response = await client.post(
        "/v1/routes",
        json={"slug": "analytics-route", "target_url": "https://example.com/get"},
        headers=auth_headers,
    )
    route_id = route_response.json()["id"]

    key_response = await client.post(
        "/v1/api-keys", json={"name": "Analytics Key"}, headers=auth_headers
    )
    api_key_id = key_response.json()["id"]

    return user_id, route_id, api_key_id


async def test_analytics_overview_counts(client, auth_headers, db_session):
    _, route_id, api_key_id = await _setup_user_route_key(client, auth_headers)

    logs = [
        RequestLog(
            route_id=uuid.UUID(route_id),
            api_key_id=uuid.UUID(api_key_id),
            latency_ms=latency,
            status_code=status_code,
            request_method="GET",
            timestamp=datetime.now(timezone.utc),
        )
        for latency, status_code in [(100, 200), (200, 200), (300, 500)]
    ]
    db_session.add_all(logs)
    await db_session.commit()

    response = await client.get("/v1/analytics/overview", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["total_requests"] == 3
    assert body["avg_latency_ms"] == 200.0
    assert round(body["error_rate"], 2) == round(1 / 3 * 100, 2)


async def test_analytics_top_routes(client, auth_headers, db_session):
    _, route_id, api_key_id = await _setup_user_route_key(client, auth_headers)

    db_session.add_all(
        [
            RequestLog(
                route_id=uuid.UUID(route_id),
                api_key_id=uuid.UUID(api_key_id),
                latency_ms=100,
                status_code=200,
                request_method="GET",
                timestamp=datetime.now(timezone.utc),
            )
            for _ in range(4)
        ]
    )
    await db_session.commit()

    response = await client.get("/v1/analytics/top-routes", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["slug"] == "analytics-route"
    assert body[0]["request_count"] == 4


async def test_analytics_logs_pagination(client, auth_headers, db_session):
    _, route_id, api_key_id = await _setup_user_route_key(client, auth_headers)

    db_session.add_all(
        [
            RequestLog(
                route_id=uuid.UUID(route_id),
                api_key_id=uuid.UUID(api_key_id),
                latency_ms=100,
                status_code=200,
                request_method="GET",
                timestamp=datetime.now(timezone.utc),
            )
            for _ in range(5)
        ]
    )
    await db_session.commit()

    page1 = await client.get(
        "/v1/analytics/logs", params={"page": 1, "page_size": 2}, headers=auth_headers
    )
    page2 = await client.get(
        "/v1/analytics/logs", params={"page": 2, "page_size": 2}, headers=auth_headers
    )
    assert page1.json()["total"] == 5
    assert len(page1.json()["logs"]) == 2
    assert len(page2.json()["logs"]) == 2
    page1_ids = {log["id"] for log in page1.json()["logs"]}
    page2_ids = {log["id"] for log in page2.json()["logs"]}
    assert page1_ids.isdisjoint(page2_ids)
