# app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from app.config import settings
from app.models.account import Account

# password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# token expires after 1 hour
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class AuthService:
    """handles password checking and JWT creation"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """check if password is correct"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """hash a password """
        return pwd_context.hash(password)
    
    @staticmethod
    def authenticate_user(db: Session, username: str, password: str) -> Optional[Account]:
        """
        check username and password.
        returns the user if correct, none if wrong.
        """
        # Find user
        account = db.query(Account).filter(
            Account.username == username,
            Account.is_active == True
        ).first()
        
        if not account:
            return None  # User doesn't exist
        
        if not AuthService.verify_password(password, account.hashed_password):
            return None  # Wrong password
        
        return account  # Success!
    
    @staticmethod
    def create_access_token(data: dict) -> str:
        """
        create a JWT token that expires in 1 hour.
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        
        # Sign the token
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.SECRET_KEY, 
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_token_for_user(account: Account) -> str:
        """
        create a JWT for a logged-in user.
        includes their ID, username, and roles.
        """
        role_names = [role.name for role in account.roles]
        
        token_data = {
            "sub": account.username,      # Username
            "user_id": account.id,         # User ID
            "roles": role_names            # Their roles
        }
        
        return AuthService.create_access_token(token_data)