import sys
import os
import io
from PIL import Image

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from app.main import app

def test_phase2_security_hardening():
    with TestClient(app) as client:
        # --- 1. Security Headers Check ---
        res = client.get("/api/hazards/active")
        headers = res.headers
        assert headers.get("x-frame-options") == "DENY", f"Missing or incorrect X-Frame-Options: {headers.get('x-frame-options')}"
        assert headers.get("x-content-type-options") == "nosniff", f"Missing X-Content-Type-Options: {headers.get('x-content-type-options')}"
        assert "strict-transport-security" in headers, "Missing Strict-Transport-Security"
        assert "content-security-policy" in headers, "Missing Content-Security-Policy"
        print("PASS: Security headers (CSP, X-Frame-Options, X-Content-Type-Options, HSTS) verified.")

        # --- 2. CORS Restriction Check ---
        # A. Trusted origin
        res_trusted = client.get("/api/hazards/active", headers={"Origin": "http://localhost:5173"})
        assert res_trusted.headers.get("access-control-allow-origin") == "http://localhost:5173"

        # B. Untrusted origin
        res_untrusted = client.get("/api/hazards/active", headers={"Origin": "https://malicious-external-site.com"})
        assert res_untrusted.headers.get("access-control-allow-origin") != "https://malicious-external-site.com"
        print("PASS: CORS origin whitelist strictly enforced.")

        # --- 3. Upload Validation & Magic-Byte Checks ---
        # A. Fake image with text content disguised as image/jpeg -> Reject with 400
        fake_image = io.BytesIO(b"echo 'malicious script'; rm -rf /")
        res_fake = client.post(
            "/api/predict-image",
            files={"file": ("exploit.jpg", fake_image, "image/jpeg")}
        )
        assert res_fake.status_code == 400, f"Expected 400 for fake image, got {res_fake.status_code}: {res_fake.text}"
        assert "Magic-byte verification failed" in res_fake.text

        # B. File exceeding 10MB -> Reject with 413
        oversized_data = io.BytesIO(b"\x00" * (10 * 1024 * 1024 + 1024))
        res_oversized = client.post(
            "/api/predict-image",
            files={"file": ("huge.jpg", oversized_data, "image/jpeg")}
        )
        assert res_oversized.status_code == 413, f"Expected 413 for oversized file, got {res_oversized.status_code}"

        # C. Real valid image (1x1 PNG) -> Validated
        valid_img_byte_arr = io.BytesIO()
        valid_img = Image.new("RGB", (10, 10), color="blue")
        valid_img.save(valid_img_byte_arr, format="PNG")
        valid_img_byte_arr.seek(0)
        res_valid = client.post(
            "/api/predict-image",
            files={"file": ("sample.png", valid_img_byte_arr, "image/png")}
        )
        assert res_valid.status_code == 200, f"Expected 200 for valid image, got {res_valid.status_code}: {res_valid.text}"
        print("PASS: File upload size limit (10MB) and PIL magic-byte validation verified.")

        # --- 4. Rate Limiting Check on Login ---
        # We allow 10 attempts per minute; 11th must trigger 429 Too Many Requests
        hit_429 = False
        for i in range(15):
            res_rate = client.post("/api/auth/login", json={"username": f"user_{i}", "password": "wrong"})
            if res_rate.status_code == 429:
                hit_429 = True
                break
        assert hit_429 is True, "Rate limiter did not throttle login attempts after threshold!"
        print("PASS: Rate limiting correctly throttles brute-force attempts with HTTP 429.")

        print("PHASE 2 HARDENING TESTS ALL PASSED!")

if __name__ == "__main__":
    test_phase2_security_hardening()
