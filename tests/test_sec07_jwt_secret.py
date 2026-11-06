import sys
import os
import importlib

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

def test_sec07_missing_jwt_secret_fails_startup():
    import app.utils.security as sec
    # Verify standard behavior when SECRET_KEY is set
    assert sec.SECRET_KEY is not None and len(sec.SECRET_KEY) > 0
    token = sec.create_access_token({"sub": "admin", "role": "admin"})
    payload = sec.decode_token(token)
    assert payload["sub"] == "admin"

    # Now verify fail-fast behavior when JWT_SECRET_KEY is removed
    saved_key = os.environ.pop("JWT_SECRET_KEY", None)
    try:
        # Unset in environment and reload module
        os.environ.pop("JWT_SECRET_KEY", None)
        # Suppress dotenv auto-reloading inside the module by mocking dotenv.load_dotenv
        import dotenv
        orig_load = dotenv.load_dotenv
        dotenv.load_dotenv = lambda *args, **kwargs: None
        try:
            threw = False
            try:
                importlib.reload(sec)
            except RuntimeError as exc:
                threw = True
                assert "JWT_SECRET_KEY environment variable is not set" in str(exc)
            assert threw, "Expected RuntimeError when JWT_SECRET_KEY is absent, but reload succeeded!"
            print("SEC-07 TEST PASSED: Application strictly fails startup when JWT_SECRET_KEY is missing.")
        finally:
            dotenv.load_dotenv = orig_load
    finally:
        if saved_key is not None:
            os.environ["JWT_SECRET_KEY"] = saved_key
            importlib.reload(sec)

if __name__ == "__main__":
    test_sec07_missing_jwt_secret_fails_startup()
