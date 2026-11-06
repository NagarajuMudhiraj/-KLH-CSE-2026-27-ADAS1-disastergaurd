import os
import hashlib
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.database.mongodb import get_users_collection

from dotenv import load_dotenv
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "FATAL SECURITY CONFIG ERROR: JWT_SECRET_KEY environment variable is not set! "
        "Application startup aborted to prevent insecure fallback secrets."
    )
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password: str) -> str:
    """Robust password hashing using bcrypt with per-user salted cost factor 12."""
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')

def _verify_legacy_pbkdf2(plain_password: str, hashed_password: str) -> bool:
    """Legacy verifier for pre-existing PBKDF2-HMAC-SHA256 hashes."""
    try:
        salt = "disaster_assistance_secure_salt_2026".encode('utf-8')
        pwd_bytes = plain_password.encode('utf-8')
        computed = hashlib.pbkdf2_hmac('sha256', pwd_bytes, salt, 100000).hex()
        return computed == hashed_password
    except Exception:
        return False

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password supporting bcrypt with PBKDF2 legacy fallback."""
    if not hashed_password or not plain_password:
        return False
    # Check if bcrypt hash ($2a$, $2b$, or $2y$)
    if hashed_password.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
        except Exception:
            return False
    # Fallback to legacy PBKDF2 verifier
    return _verify_legacy_pbkdf2(plain_password, hashed_password)

def needs_rehash(hashed_password: str) -> bool:
    """Identifies legacy PBKDF2 or non-bcrypt hashes that require rehashing upon successful login."""
    return not (hashed_password and hashed_password.startswith(("$2a$", "$2b$", "$2y$")))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def get_current_user(token: str = Depends(oauth2_scheme)) -> Dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
        
    users_coll = get_users_collection()
    user = users_coll.find_one({"username": username})
    if user is None:
        return {"username": username, "email": payload.get("email", ""), "role": payload.get("role", "driver")}
    
    return {
        "username": user["username"],
        "email": user["email"],
        "role": user.get("role", "driver")
    }

optional_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

def get_optional_user(token: Optional[str] = Depends(optional_oauth2_scheme)) -> Dict[str, Any]:
    """Retrieves user if valid token provided; falls back gracefully to driver identity."""
    if not token:
        return {"username": "driver_in_field", "email": "telemetry@adas.local", "role": "driver"}
    payload = decode_token(token)
    if payload is None or not payload.get("sub"):
        return {"username": "driver_in_field", "email": "telemetry@adas.local", "role": "driver"}
    users_coll = get_users_collection()
    user = users_coll.find_one({"username": payload.get("sub")})
    if user is None:
        return {"username": payload.get("sub"), "email": payload.get("email", ""), "role": payload.get("role", "driver")}
    return {
        "username": user["username"],
        "email": user["email"],
        "role": user.get("role", "driver")
    }

def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """Dependency that ensures the authenticated user possesses the 'admin' role."""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrative privileges required to access this resource."
        )
    return current_user


