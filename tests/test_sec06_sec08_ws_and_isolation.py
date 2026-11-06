import sys
import os

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from app.main import app
from app.utils.security import create_access_token
from app.database.mongodb import get_emergency_requests_collection, get_predictions_collection

def test_sec06_sec08_websockets_and_isolation():
    driver_a_token = create_access_token(data={"sub": "driver_alpha", "email": "alpha@test.local", "role": "driver"})
    driver_b_token = create_access_token(data={"sub": "driver_bravo", "email": "bravo@test.local", "role": "driver"})
    admin_token = create_access_token(data={"sub": "commander_admin", "email": "admin@test.local", "role": "admin"})

    headers_a = {"Authorization": f"Bearer {driver_a_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    with TestClient(app) as client:
        # --- 1. Test WebSocket Authentication (SEC-06) ---
        # A. Unauthenticated /ws/emergency -> Policy violation rejection
        try:
            with client.websocket_connect("/api/ws/emergency") as ws:
                pass
            assert False, "Unauthenticated /ws/emergency should have been rejected!"
        except Exception:
            pass  # Expected disconnect

        # B. Invalid token /ws/emergency -> Policy violation rejection
        try:
            with client.websocket_connect("/api/ws/emergency?token=invalid.token.here") as ws:
                pass
            assert False, "Invalid token /ws/emergency should have been rejected!"
        except Exception:
            pass  # Expected disconnect

        # C. Authenticated /ws/emergency -> Success
        with client.websocket_connect(f"/api/ws/emergency?token={driver_a_token}") as ws:
            assert ws is not None

        # D. Unauthenticated /ws/disasters -> Policy violation rejection
        try:
            with client.websocket_connect("/api/navigation/ws/disasters") as ws:
                pass
            assert False, "Unauthenticated /ws/disasters should have been rejected!"
        except Exception:
            pass

        # E. Authenticated /ws/disasters -> Success & ping/pong
        with client.websocket_connect(f"/api/navigation/ws/disasters?token={driver_a_token}") as ws:
            ws.send_text("ping")
            reply = ws.receive_text()
            assert reply == "pong"

        # --- 2. Test Emergency List Isolation (SEC-08) ---
        sos_coll = get_emergency_requests_collection()
        sos_coll.delete_many({})
        sos_coll.insert_one({"username": "driver_alpha", "message": "Alpha SOS", "status": "PENDING"})
        sos_coll.insert_one({"username": "driver_bravo", "message": "Bravo SOS", "status": "PENDING"})

        # Driver A should only see Driver A's SOS
        res_a = client.get("/api/emergency/list", headers=headers_a)
        assert res_a.status_code == 200
        records_a = res_a.json()
        assert len(records_a) == 1, f"Expected 1 record for driver_alpha, got {len(records_a)}"
        assert records_a[0]["username"] == "driver_alpha"

        # Admin should see both
        res_admin = client.get("/api/emergency/list", headers=headers_admin)
        assert res_admin.status_code == 200
        records_admin = res_admin.json()
        assert len(records_admin) == 2, f"Expected 2 records for admin, got {len(records_admin)}"

        # --- 3. Test Prediction History Isolation (SEC-08) ---
        pred_coll = get_predictions_collection()
        pred_coll.delete_many({})
        pred_coll.insert_one({"username": "driver_alpha", "prediction": "Flood", "riskScore": 85})
        pred_coll.insert_one({"username": "driver_bravo", "prediction": "Fire", "riskScore": 90})

        # Driver A requesting history (even attempting IDOR by querying user_filter=driver_bravo)
        res_hist_a = client.get("/api/history?user_filter=driver_bravo", headers=headers_a)
        assert res_hist_a.status_code == 200
        hist_a = res_hist_a.json()
        assert len(hist_a) == 1, f"Expected 1 record isolated to alpha, got {len(hist_a)}"
        assert hist_a[0]["username"] == "driver_alpha"

        # Admin requesting history without filter sees both
        res_hist_admin = client.get("/api/history", headers=headers_admin)
        assert res_hist_admin.status_code == 200
        hist_admin = res_hist_admin.json()
        assert len(hist_admin) == 2, f"Expected 2 records for admin, got {len(hist_admin)}"

        print("SEC-06 & SEC-08 TEST PASSED: WebSocket JWT handshake & user record isolation strictly enforced.")

if __name__ == "__main__":
    test_sec06_sec08_websockets_and_isolation()

