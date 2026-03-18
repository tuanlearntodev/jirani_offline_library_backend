from pydantic import BaseModel, Field
from typing import Optional, Literal

class Video_Create(BaseModel): #  from client, to server
    title: str 
    description: Optional[str] = None # optional fields require default value, here it is none
    file_path: str

class Video_View(BaseModel): # from server, to client
    id: int
    title: str
    description: Optional[str] = None
    video_url: str

    


