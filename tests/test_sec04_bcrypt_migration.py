import sys
import os
import hashlib

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from fastapi.testclient import TestClient
from app.main import app
from app.utils.security import hash_password, verify_password, needs_rehash
from app.database.mongodb import get_users_collection

def test_sec04_bcrypt_and_migration():
    # 1. Verify bcrypt generation
    pwd = "SecureTestPassword#2026"
    b_hash = hash_password(pwd)
    assert b_hash.startswith(("$2a$", "$2b$", "$2y$")), f"Hash is not bcrypt format: {b_hash}"
    assert verify_password(pwd, b_hash) is True
    assert verify_password("WrongPassword!", b_hash) is False
    assert needs_rehash(b_hash) is False

    # 2. Verify legacy PBKDF2 hash verification
    salt = "disaster_assistance_secure_salt_2026".encode("utf-8")
    legacy_pwd = "OldLegacyPassword123!"
    legacy_hash = hashlib.pbkdf2_hmac("sha256", legacy_pwd.encode("utf-8"), salt, 100000).hex()
    assert needs_rehash(legacy_hash) is True
    assert verify_password(legacy_pwd, legacy_hash) is True
    assert verify_password("WrongLegacyPass", legacy_hash) is False

    # 3. Verify transparent migration on login via API
    with TestClient(app) as client:
        users_coll = get_users_collection()
        # Insert a user with legacy PBKDF2 hash
        users_coll.delete_one({"username": "legacy_user_migrate"})
        users_coll.insert_one({
            "username": "legacy_user_migrate",
            "email": "legacy@migrate.test",
            "password": legacy_hash,
            "role": "driver"
        })

        # Login with legacy password
        res = client.post("/api/auth/login", json={
            "username": "legacy_user_migrate",
            "password": legacy_pwd
        })
        assert res.status_code == 200, f"Login failed: {res.text}"

        # Fetch user from DB and check upgraded hash
        migrated_user = users_coll.find_one({"username": "legacy_user_migrate"})
        assert migrated_user is not None
        assert migrated_user["password"].startswith(("$2a$", "$2b$", "$2y$")), \
            f"Password was not migrated to bcrypt! Found: {migrated_user['password']}"
        assert needs_rehash(migrated_user["password"]) is False
        assert verify_password(legacy_pwd, migrated_user["password"]) is True

        print("SEC-04 TEST PASSED: Bcrypt hashing, legacy PBKDF2 verification, and transparent rehash migration verified.")

if __name__ == "__main__":
    test_sec04_bcrypt_and_migration()

