def test_delete_groundstation_response_shape(client):
    response = client.delete("/groundstations/3")
    assert response.status_code == 200
    data = response.json()
    assert "deleted_reservations" in data
    assert "deleted_reservations_count" not in data
