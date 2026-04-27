from pydantic import BaseModel
from typing import Optional

class Audio_Create(BaseModel):
    title: str
    description: Optional[str] = None
    file_path: str

class Audio_View(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    audio_url: str

    class Config:
        from_attributes = True