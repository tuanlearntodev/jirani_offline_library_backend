from fastapi import APIRouter, File, UploadFile, Form, Depends
from app.schemas.video_schema import Video_Create, Video_View
from app.repositories.video_repo import Video_Repo
from sqlalchemy.orm import Session
import os, shutil
from app.database import get_db

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
    file_location = f"{upload_directory}/{file.filename}"
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
        video_type = video_db.video_typed
    )