from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import UserRegister, UserLogin, UserResponse, TokenResponse
from app.db.mongodb import get_database
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from datetime import datetime, timezone
import uuid

router = APIRouter(prefix="/api/auth", tags=["auth"])
security_scheme = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    email = payload["sub"]
    db = get_database()
    user = await db.users.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    # Map MongoDB fields
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "created_at": user.get("created_at", datetime.now(timezone.utc))
    }

@router.post("/signup", response_model=TokenResponse)
async def signup(user_data: UserRegister):
    db = get_database()
    
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address already registered"
        )
    
    # Hash password and insert
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    new_user = {
        "_id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "created_at": datetime.now(timezone.utc)
    }
    
    await db.users.insert_one(new_user)
    
    # Create Access Token
    access_token = create_access_token(subject=user_data.email)
    
    user_response = UserResponse(
        id=user_id,
        name=new_user["name"],
        email=new_user["email"],
        created_at=new_user["created_at"]
    )
    
    return TokenResponse(access_token=access_token, user=user_response)

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    db = get_database()
    
    # Find user by email
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create Access Token
    access_token = create_access_token(subject=user["email"])
    
    user_response = UserResponse(
        id=str(user["_id"]),
        name=user["name"],
        email=user["email"],
        created_at=user.get("created_at", datetime.now(timezone.utc))
    )
    
    return TokenResponse(access_token=access_token, user=user_response)

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(
        id=current_user["id"],
        name=current_user["name"],
        email=current_user["email"],
        created_at=current_user["created_at"]
    )
