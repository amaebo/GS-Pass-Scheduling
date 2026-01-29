import pytest
from fastapi.testclient import TestClient

import src.API as api


@pytest.fixture()
def api_client(monkeypatch):
    # Avoid hitting the real DB during tests.
    monkeypatch.setattr(api, "insert_new_satellite", lambda norad_id, s_name: 1)
    return TestClient(api.app)


def test_register_satellite_success(api_client):
    payload = {"norad_id": 25544, "s_name": "ISS"}
    response = api_client.post("/satellites/register", json=payload)
    assert response.status_code == 200
    assert response.json() == {
        "message": "Satellite registered",
        "satellite": payload,
    }


def test_register_satellite_missing_field(api_client):
    payload = {"norad_id": 25544}
    response = api_client.post("/satellites/register", json=payload)
    assert response.status_code == 422
