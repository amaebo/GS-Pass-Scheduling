from fastapi.testclient import TestClient

from src.API import app


client = TestClient(app)


def test_register_satellite_success():
    payload = {"norad_id": 25544, "s_name": "ISS"}
    response = client.post("/satellites/register", json=payload)
    assert response.status_code == 200
    assert response.json() == {
        "message": "Satellite registered",
        "satellite": payload,
    }


def test_register_satellite_missing_field():
    payload = {"norad_id": 25544}
    response = client.post("/satellites/register", json=payload)
    assert response.status_code == 422
