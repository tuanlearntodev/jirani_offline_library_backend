from pydantic import BaseModel, Field
from typing import List

# What user sends when logging in (username & password must be strings)
class LoginRequest(BaseModel):
    username: str 
    password: str

class SignUpRequest(BaseModel):
    username:str = Field(..., min_length = 4, max_length=50)
    password: str = Field(..., min_length = 15)

class ResetPasswordRequest(BaseModel):
    username: str
    new_password: str = Field(..., min_length=15)

class ChangePasswordRequest(BaseModel):
    username: str
    new_password: str = Field(..., min_length=15)
    
class Token(BaseModel):
    access_token: str  # returns jwt token
    token_type: str = "bearer" #scheme for sending a token in HTTP requests

class RoleSchema(BaseModel):
    id: int
    name: str
    
    class Config:
        from_attributes = True

class UserWithRoles(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    is_active: bool
    roles: List[RoleSchema]
    
    class Config:
        from_attributes = True
