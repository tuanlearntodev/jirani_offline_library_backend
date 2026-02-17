from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from app.schemas.video_schema import Video_Create, Video_View
from app.repositories.video_repo import Video_Repo
from sqlalchemy.orm import Session
from app.models.video import Video
import os, shutil
from fastapi.responses import StreamingResponse
from app.database import get_db
import uuid

router = APIRouter(prefix="videos", tags=["videos"])

@router.post("/upload", response_model = Video_View) #response_model sends back data in form
async def upload_file(
    file: UploadFile = File (...), 
    title: str=Form (...), description: str | None=Form(None),
    file_path: str=Form(...),
    video_type: str = Form(...),
    db: Session = Depends(get_db)
    ):# parameters are everything needed from client to create a correct SQLAlchemy object and store it in the database

    upload_directory = "uploads" # folder where uploaded videos will be stored
    os.makedirs(upload_directory, exist_ok=True)
    file_location = f"{upload_directory}/{uuid.uuid4()}_{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    video = Video_Create(
        title=title,
        description = description,
        video_type = "mp4",
        file_path = file_location
    )

    repo = Video_Repo(db)
    video_db = repo.create_video(video)

    video_url = f"http://raspberrypi/{file_location}" 

    return Video_View(
        id = video_db.id,
        title = video_db.title,
        description = video_db.description,
        video_url = video_url,
        video_type = video_db.video_type
    )

@router.get("/stream/{video_id}")
def stream_video(video_id: int, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    def iterfile():
        with open(video.file_path, "rb") as f: #read file in binary mode = necessary for videos
            while True: 
                chunk = f.read(1024*1024) # this is 1MB
                if not chunk: 
                    break
                yield chunk

    return StreamingResponse(iterfile(), media_type=f"video/{video.video_type}")

