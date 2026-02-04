# Pydantic Schemas
# This package contains request/response schemas using Pydantic

from .auth_schema import LoginRequest, SignUpRequest, Token, RoleSchema, UserWithRoles
from .book_schema import BookBase, BookCreate, BookRead, BookDetail, BookUpload
from .tag_schema import TagBase, TagRead, TagCreate

__all__ = [
    # Auth schemas
    "LoginRequest",
    "SignUpRequest",
    "Token",
    "RoleSchema",
    "UserWithRoles",
    # Book schemas
    "BookBase",
    "BookCreate",
    "BookRead",
    "BookDetail",
    "BookUpload",
    "TagBase",
    "TagRead",
    "TagCreate",
]