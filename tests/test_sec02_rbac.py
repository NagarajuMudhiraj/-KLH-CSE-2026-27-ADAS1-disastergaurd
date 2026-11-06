import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.utils.security import create_access_token

def test_sec02_admin_rbac_enforcement():
    with TestClient(app) as client:
        # 1. Driver token & Admin token
        driver_token = create_access_token(data={"sub": "test_driver", "email": "driver@test.local", "role": "driver"})
        admin_token = create_access_token(data={"sub": "test_admin", "email": "admin@test.local", "role": "admin"})

        driver_headers = {"Authorization": f"Bearer {driver_token}"}
        admin_headers = {"Authorization": f"Bearer {admin_token}"}

        # --- Test 1: POST /api/hazards/admin/create ---
        hazard_payload = {
            "type": "Flood",
            "latitude": 17.44,
            "longitude": 78.38,
            "address": "Admin Test Road",
            "severity": "HIGH",
            "description": "Admin test flood"
        }
        # Unauthenticated -> 401
        res_unauth = client.post("/api/hazards/admin/create", json=hazard_payload)
        assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"

        # Driver -> 403 Forbidden
        res_driver = client.post("/api/hazards/admin/create", json=hazard_payload, headers=driver_headers)
        assert res_driver.status_code == 403, f"Expected 403, got {res_driver.status_code}: {res_driver.text}"

        # Admin -> 200 OK
        res_admin = client.post("/api/hazards/admin/create", json=hazard_payload, headers=admin_headers)
        assert res_admin.status_code == 200, f"Expected 200, got {res_admin.status_code}: {res_admin.text}"
        created_hazard_id = res_admin.json().get("id")

        # --- Test 2: PUT /api/hazards/admin/{id} ---
        edit_payload = {"severity": "CRITICAL"}
        res_edit_driver = client.put(f"/api/hazards/admin/{created_hazard_id}", json=edit_payload, headers=driver_headers)
        assert res_edit_driver.status_code == 403, f"Expected 403, got {res_edit_driver.status_code}"
        res_edit_admin = client.put(f"/api/hazards/admin/{created_hazard_id}", json=edit_payload, headers=admin_headers)
        assert res_edit_admin.status_code == 200, f"Expected 200, got {res_edit_admin.status_code}"

        # --- Test 3: POST /api/hazards/verify ---
        verify_payload = {"hazard_id": created_hazard_id, "action": "approve"}
        res_ver_unauth = client.post("/api/hazards/verify", json=verify_payload)
        assert res_ver_unauth.status_code == 401, f"Expected 401, got {res_ver_unauth.status_code}"
        res_ver_driver = client.post("/api/hazards/verify", json=verify_payload, headers=driver_headers)
        assert res_ver_driver.status_code == 403, f"Expected 403, got {res_ver_driver.status_code}"
        res_ver_admin = client.post("/api/hazards/verify", json=verify_payload, headers=admin_headers)
        assert res_ver_admin.status_code == 200, f"Expected 200, got {res_ver_admin.status_code}"

        # --- Test 4: POST /api/navigation/disaster-zones ---
        zone_payload = {
            "name": "Flooded Sector 4",
            "lat": 17.45,
            "lng": 78.39,
            "radius_meters": 500,
            "risk_level": "Red",
            "reason": "Flash Flood Test"
        }
        res_zone_unauth = client.post("/api/navigation/disaster-zones", json=zone_payload)
        assert res_zone_unauth.status_code == 401, f"Expected 401, got {res_zone_unauth.status_code}"
        res_zone_driver = client.post("/api/navigation/disaster-zones", json=zone_payload, headers=driver_headers)
        assert res_zone_driver.status_code == 403, f"Expected 403, got {res_zone_driver.status_code}"
        res_zone_admin = client.post("/api/navigation/disaster-zones", json=zone_payload, headers=admin_headers)
        assert res_zone_admin.status_code == 200, f"Expected 200, got {res_zone_admin.status_code}"

        # --- Test 5: DELETE /api/hazards/admin/{id} ---
        res_del_driver = client.delete(f"/api/hazards/admin/{created_hazard_id}", headers=driver_headers)
        assert res_del_driver.status_code == 403, f"Expected 403, got {res_del_driver.status_code}"
        res_del_admin = client.delete(f"/api/hazards/admin/{created_hazard_id}", headers=admin_headers)
        assert res_del_admin.status_code == 200, f"Expected 200, got {res_del_admin.status_code}"

        print("SEC-02 TEST PASSED: All admin hazard endpoints & disaster-zones strictly enforce require_admin RBAC.")

if __name__ == "__main__":
    test_sec02_admin_rbac_enforcement()

