# app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.models.account import Account

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour

class AuthService:
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        return pwd_context.hash(password)
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[Account]:
        account = db.query(Account).filter(
            Account.username == username,
            Account.is_active == True
        ).first()
        
        if not account:
            return None
        
        if not AuthService.verify_password(password, account.hashed_password):
            return None
        
        return account
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_token_for_user(account: Account) -> str:
        role_names = [role.name for role in account.roles]
        
        token_data = {
            "sub": account.username,
            "user_id": account.id,
            "roles": role_names
        }
        
        return AuthService.create_access_token(token_data)