import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "healthy"
    assert "project" in json_data
    assert "active_captures" in json_data

def test_get_interfaces():
    response = client.get("/capture/interfaces")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_statistics():
    response = client.get("/statistics")
    assert response.status_code == 200
    data = response.json()
    assert "total_packets" in data
    assert "total_bytes" in data
    assert "packets_per_second" in data

def test_get_protocols():
    response = client.get("/protocols")
    assert response.status_code == 200
    assert isinstance(response.json(), dict)

def test_get_top_ips():
    response = client.get("/top-ips")
    assert response.status_code == 200
    data = response.json()
    assert "sources" in data
    assert "destinations" in data

def test_get_top_domains():
    response = client.get("/top-domains")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
