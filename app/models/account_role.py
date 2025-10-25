from app.database import Base
from sqlalchemy import Column, Integer, ForeignKey,UniqueConstraint, Boolean

class AccountRole(Base):
    __tablename__ = "account_roles"
    
    id = Column(Integer, primary_key=True) 
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    
    __table_args__ = (UniqueConstraint('account_id', 'role_id'),)

    '''
    This is the join table for the many-to-many relationship between account & role!

    id: primary key of this table (unique identifier for each row).
    account_id: foreign key referencing accounts.id. Links a role to a specific account.
    role_id: foreign key referencing roles.id. Links a specific role to an account.
    is_active: boolean flag indicating whether this role assignment is currently active (default True).
    '''