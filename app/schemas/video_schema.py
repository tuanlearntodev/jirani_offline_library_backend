from pydantic import BaseModel, Field
from typing import Optional, Literal

class Video_Create(BaseModel): # for server, from client
    title: str 
    description: Optional[str] = None # optional fields require default value, here it is none
    video_type: Literal["mp4"] # just testing mp4 right now
    file_path: str

class Video_View(BaseModel): # for client, from server
    id: int
    title: str
    description: Optional[str] = None
    video_type: Literal["mp4"]
    video_url: str

    


