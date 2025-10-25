from app.database import Base
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    roles = relationship("Role", secondary="account_roles", back_populates="accounts")

    '''
    this represents users, such as kids, teachers, admins, etc. roles relationship connects to
    account <--> role through account role join table.

    used by auth service for authentication & jwt
    
    
    '''