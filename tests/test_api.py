"""
Test API Endpoints
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    """Test health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data
    assert "version" in data
    
    print("✅ test_health_check passed")


def test_parse_text():
    """Test parse endpoint."""
    response = client.post(
        "/api/v1/parse",
        json={
            "text": "The living room is at the north corner. It is approximately 15 feet wide by 20 feet deep, for a total square footage of 300."
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "json" in data
    assert "confidence" in data
    assert data["json"]["total_rooms"] > 0
    
    print("✅ test_parse_text passed")


def test_generate_svg():
    """Test generate endpoint."""
    response = client.post(
        "/api/v1/generate",
        json={
            "json": {
                "rooms": [
                    {
                        "room": "living room",
                        "position": "north",
                        "dimensions": {
                            "width": 15,
                            "depth": 20,
                            "square_footage": 300
                        }
                    }
                ],
                "total_rooms": 1,
                "total_square_footage": 300
            }
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert "svg" in data
    assert "id" in data
    assert "<svg" in data["svg"]
    
    print("✅ test_generate_svg passed")


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "name" in data
    assert "version" in data
    
    print("✅ test_root_endpoint passed")


if __name__ == "__main__":
    print("🧪 Running API tests...\n")
    
    test_health_check()
    test_root_endpoint()
    test_parse_text()
    test_generate_svg()
    
    print("\n✅ All API tests passed!")

