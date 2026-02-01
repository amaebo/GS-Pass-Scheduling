def test_list_satellites_seeded(client):
    response = client.get("/satellites")
    assert response.status_code == 200
    satellites = response.json()["satellites"]
    assert len(satellites) >= 1


def test_register_satellite_then_list(client):
    payload = {"norad_id": 99999, "s_name": "TEST SAT"}
    response = client.post("/satellites/register", json=payload)
    assert response.status_code == 201

    response = client.get("/satellites")
    assert response.status_code == 200
    satellites = response.json()["satellites"]
    assert any(
        sat["norad_id"] == 99999 and sat["s_name"] == "TEST SAT" for sat in satellites
    )
    assert all("s_id" not in sat for sat in satellites)


def test_register_satellite_duplicate_norad_id(client):
    payload = {"norad_id": 88888, "s_name": "DUP TEST SAT"}
    first = client.post("/satellites/register", json=payload)
    assert first.status_code == 201

    second = client.post("/satellites/register", json=payload)
    assert second.status_code == 409
