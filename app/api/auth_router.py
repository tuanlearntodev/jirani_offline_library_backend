import random
import time
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth_schema import Token, LoginRequest, SignUpRequest, ResetPasswordRequest, ChangePasswordRequest
from app.services.auth_service import AuthService
from app.models.account import Account
from app.models.role import Role
from app.dependencies.auth import get_current_user, RoleChecker

router = APIRouter(prefix="/auth", tags=["authentication"])

# In-memory OTP store
otp_store: dict = {}


@router.post("/seed-roles", tags=["setup"])
def seed_roles(db: Session = Depends(get_db)):
    for name in ["admin", "teacher", "student"]:
        if not db.query(Role).filter(Role.name == name).first():
            db.add(Role(name=name))
    db.commit()
    return {"message": "Roles seeded"}


@router.post("/make-admin/{username}", tags=["setup"])
def make_admin(username: str, db: Session = Depends(get_db)):
    user = AuthService.get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    admin_role = db.query(Role).filter(Role.name == "admin").first()
    if not admin_role:
        raise HTTPException(status_code=400, detail="Seed roles first")
    if admin_role not in user.roles:
        user.roles.append(admin_role)
        db.commit()
    return {"message": f"{username} is now admin"}


@router.post("/token", response_model=Token, status_code=status.HTTP_200_OK)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    user = AuthService.authenticate_user(db, login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    access_token = AuthService.create_token_for_user(user)
    return Token(access_token=access_token, token_type="bearer", username=user.username, roles=[r.name for r in user.roles])


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
async def signup(signup_data: SignUpRequest, db: Session = Depends(get_db)):
    existing = AuthService.get_user_by_username(db, signup_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    try:
        user = AuthService.create_user(db, signup_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    access_token = AuthService.create_token_for_user(user)
    return Token(access_token=access_token, token_type="bearer", username=user.username, roles=[r.name for r in user.roles])


@router.post("/forgot-password/send-otp")
async def send_otp(db: Session = Depends(get_db)):
    admin = db.query(Account).filter(
        Account.roles.any(Role.name == "admin"),
        Account.is_active == True
    ).first()

    if not admin or not admin.phone_number:
        raise HTTPException(status_code=400, detail="Admin phone number not set — update your profile first")

    otp = str(random.randint(100000, 999999))
    otp_store["admin"] = {"otp": otp, "expires": time.time() + 300}

    try:
        from twilio.rest import Client
        from app.config import settings
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=f"Jirani Library — your reset code is: {otp}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=admin.phone_number
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send SMS: {str(e)}")

    return {"message": "OTP sent to admin phone"}


@router.post("/forgot-password/verify-otp")
async def verify_otp(otp: str, new_password: str, db: Session = Depends(get_db)):
    stored = otp_store.get("admin")
    if not stored:
        raise HTTPException(status_code=400, detail="No OTP requested")
    if time.time() > stored["expires"]:
        otp_store.pop("admin", None)
        raise HTTPException(status_code=400, detail="OTP expired — request a new one")
    if stored["otp"] != otp:
        raise HTTPException(status_code=400, detail="Invalid code")

    admin = db.query(Account).filter(
        Account.roles.any(Role.name == "admin"),
        Account.is_active == True
    ).first()
    if not admin:
        raise HTTPException(status_code=404, detail="Admin not found")

    admin.hashed_password = AuthService.get_password_hash(new_password)
    db.commit()
    otp_store.pop("admin", None)
    return {"message": "Password reset successfully"}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(reset_data: ResetPasswordRequest, db: Session = Depends(get_db), current_user: Account = Depends(RoleChecker(["admin"]))):
    try:
        updated = AuthService.reset_password(db, reset_data.username, reset_data.new_password)
        return {"message": f"Password reset for {updated.username}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_own_password(change_data: ChangePasswordRequest, db: Session = Depends(get_db), current_user: Account = Depends(RoleChecker(["admin"]))):
    if not AuthService.verify_password(change_data.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect current password")
    current_user.hashed_password = AuthService.get_password_hash(change_data.new_password)
    db.commit()
    return {"message": "Password changed successfully"}