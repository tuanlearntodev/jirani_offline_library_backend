# app/routes/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import Token, LoginRequest, SignUpRequest, ResetPasswordRequest, ChangePasswordRequest
from app.schemas.auth_service import AuthService
from app.models.account import Account
from app.dependencies.auth import get_current_user, RoleChecker

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/token", response_model=Token, status_code = status.HTTP_200_OK, summary = "User login", description="Authenticates user and returns a JWT token")
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

# this is only for students, where teachers or admin can only reset their passwords
@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    reset_password_data: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: Account = Depends(RoleChecker(["admin", "teacher"]))  
):
    try:
     
        updated_user = AuthService.reset_password(
            db,
            reset_password_data.username,      
            reset_password_data.new_password  
        )
        
        return {
            "message": f"password reset for user: {updated_user.username}"
        }
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

# teachers & admin resetting their own passwords
@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_own_password(
    change_data: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: Account = Depends(RoleChecker(["admin", "teacher"]))
):
    is_correct = AuthService.verify_password(
        change_data.old_password,
        current_user.hashed_password
    )

    if not is_correct:
        raise HTTPException(
            status_code = status.HTTP_400_BAD_REQUEST,
            detail = "incorrect current password"
        )

    current_user.hashed_password = AuthService.get_password_hash(change_data.new_password)
    db.commit()
    
    return {"message": "password has been changed successfully"}
        