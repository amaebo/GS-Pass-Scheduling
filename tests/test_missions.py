def test_remove_satellite_missing_returns_404(client):
    response = client.delete("/missions/1/satellites/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Satellite not found"
