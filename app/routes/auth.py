# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import Token, LoginRequest, SignUpRequest
from app.schemas.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/token", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    login endpoint - give username/password, get JWT token back
    """
    # check username & password
    user = AuthService.authenticate_user(db, login_data.username, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
 
    access_token = AuthService.create_token_for_user(user)
    
    return Token(access_token=access_token, token_type="bearer")

@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(
    signup_data: SignUpRequest,
    db: Session = Depends(get_db)
):
     # DEBUG: print username and password info
    print("Username:", signup_data.username)
    print("Password (raw):", repr(signup_data.password))  # shows hidden chars
    print("Password length in bytes:", len(signup_data.password.encode('utf-8')))
    # if username exists
    existing_user=AuthService.get_user_by_username(db, signup_data.username)
    if existing_user:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "Username already registered"
        )
    
    #create new user
    try:
        user = AuthService.create_user(db, signup_data)
    except ValueError as e:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = str(e)
        )
    access_token = AuthService.create_token_for_user(user)
    return Token(access_token=access_token, token_type="bearer")

