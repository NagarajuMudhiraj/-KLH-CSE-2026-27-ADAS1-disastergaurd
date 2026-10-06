from fastapi import APIRouter, HTTPException, Depends, status
from app.models.schemas import UserRegister, UserLogin, Token, UserProfile, UserProfileUpdate
from app.database.mongodb import get_users_collection
from app.utils.security import hash_password, verify_password, create_access_token, get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=Token)
def register(user_data: UserRegister):
    users_coll = get_users_collection()
    
    # Check if username or email already exists
    existing_user = users_coll.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered"
        )

    hashed_pwd = hash_password(user_data.password)
    user_doc = {
        "username": user_data.username,
        "email": user_data.email,
        "password": hashed_pwd,
        "role": user_data.role or "driver",
        "createdAt": datetime.utcnow().isoformat()
    }
    
    users_coll.insert_one(user_doc)
    
    token = create_access_token(data={
        "sub": user_data.username,
        "email": user_data.email,
        "role": user_data.role or "driver"
    })
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user_data.username,
            "email": user_data.email,
            "role": user_data.role or "driver"
        }
    }

@router.post("/login", response_model=Token)
def login(credentials: UserLogin):
    users_coll = get_users_collection()
    user = users_coll.find_one({"username": credentials.username})
    
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    token = create_access_token(data={
        "sub": user["username"],
        "email": user["email"],
        "role": user.get("role", "driver")
    })

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "email": user["email"],
            "role": user.get("role", "driver")
        }
    }

@router.get("/profile", response_model=UserProfile)
def get_profile(current_user: dict = Depends(get_current_user)):
    users_coll = get_users_collection()
    user_doc = users_coll.find_one({"username": current_user["username"]})
    if user_doc:
        doc = dict(user_doc)
        doc.pop("password", None)
        doc.pop("_id", None)
        return doc
    return current_user

@router.put("/profile", response_model=UserProfile)
def update_profile(
    update_data: UserProfileUpdate,
    current_user: dict = Depends(get_current_user)
):
    users_coll = get_users_collection()
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updatedAt"] = datetime.utcnow().isoformat()
    
    users_coll.update_one(
        {"username": current_user["username"]},
        {"$set": update_dict}
    )
    
    updated_user = users_coll.find_one({"username": current_user["username"]})
    if updated_user:
        doc = dict(updated_user)
        doc.pop("password", None)
        doc.pop("_id", None)
        return doc
    return {**current_user, **update_dict}
