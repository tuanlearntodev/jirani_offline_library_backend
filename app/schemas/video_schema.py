from pydantic import BaseModel, Field
from typing import Optional, Literal

class Video_Create(BaseModel): # for server, from client
    title: str 
    description: Optional[str] = None # optional fields require default value, here it is none
    file_path: str

class Video_View(BaseModel): # for client, from server
    id: int
    title: str
    description: Optional[str] = None
    video_url: str

    


