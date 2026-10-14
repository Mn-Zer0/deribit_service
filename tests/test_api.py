import pytest


async def test_get_latest_price(client, sample_prices):
    response = await client.get("/api/v1/prices/latest", params={"ticker": "btc_usd"})
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "btc_usd"
    assert data["price"] == 51000.0


async def test_get_latest_price_not_found(client):
    response = await client.get("/api/v1/prices/latest", params={"ticker": "xrp_usd"})
    assert response.status_code == 404


async def test_get_all_prices(client, sample_prices):
    response = await client.get("/api/v1/prices/", params={"ticker": "btc_usd"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(item["ticker"] == "btc_usd" for item in data)


async def test_get_prices_by_date(client, sample_prices):
    response = await client.get(
        "/api/v1/prices/by-date",
        params={"ticker": "btc_usd", "from_ts": 1700000000, "to_ts": 1700000050},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["price"] == 50000.0


async def test_missing_ticker(client):
    response = await client.get("/api/v1/prices/latest")
    assert response.status_code == 422