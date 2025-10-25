from pydantic import BaseModel
from typing import List

# What user sends when logging in
class LoginRequest(BaseModel):
    username: str
    password: str

# What we send back after login
class Token(BaseModel):
    access_token: str  # The JWT token
    token_type: str = "bearer"

# Info about a role
class RoleSchema(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

# User info with roles
class UserWithRoles(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    is_active: bool
    roles: List[RoleSchema]
    
    class Config:
        from_attributes = True
