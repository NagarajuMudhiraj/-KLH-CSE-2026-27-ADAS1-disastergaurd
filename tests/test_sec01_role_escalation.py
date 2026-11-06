import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.database.mongodb import get_users_collection

def test_sec01_registration_privilege_escalation():
    with TestClient(app) as client:
        # Attempt privilege escalation by injecting role='admin'
        payload = {
            "username": "attacker_sec01",
            "email": "attacker01@adas.test",
            "password": "StrongPassword123!",
            "role": "admin"
        }
        res = client.post("/api/auth/register", json=payload)
        assert res.status_code == 200, f"Registration failed: {res.text}"
        data = res.json()
        
        # 1. Returned user payload MUST have role == 'driver'
        assert data["user"]["role"] == "driver", f"Role was not driver: {data['user']['role']}"
        
        # 2. Database record MUST have role == 'driver'
        users_coll = get_users_collection()
        user_in_db = users_coll.find_one({"username": "attacker_sec01"})
        assert user_in_db is not None, "User not found in DB"
        assert user_in_db["role"] == "driver", f"DB record role is {user_in_db['role']}, expected 'driver'"
        
        print("SEC-01 TEST PASSED: Registration strictly forces role='driver' even when role='admin' is supplied.")

if __name__ == "__main__":
    test_sec01_registration_privilege_escalation()

