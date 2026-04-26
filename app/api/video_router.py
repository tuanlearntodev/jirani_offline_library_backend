from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from app.schemas.video_schema import Video_Create, Video_View
from app.repositories.video_repo import Video_Repo
from sqlalchemy.orm import Session
from app.models.video import Video
import os, shutil
from fastapi.responses import StreamingResponse
from app.database import get_db
import uuid
import asyncio
from pathlib import Path

router = APIRouter(prefix="/videos", tags=["videos"])
VIDS_DIR = Path("uploads") / "vids"

@router.get("/", response_model=list[Video_View])
def get_videos(db: Session = Depends(get_db)):
    videos = db.query(Video).filter(Video.deleted_at==None).all()
    result = []
    for vid in videos:
        result.append(
            Video_View(
                id=vid.id,
                title=vid.title,
                description=vid.description,
                video_url=f"http://raspberrypi/{vid.file_path}"
            ))
    return result

@router.delete("/{video_id}")
def delete_videos(video_id: int, db: Session = Depends(get_db)):
    repo = Video_Repo(db)
    return repo.delete_video(video_id)

@router.post("/upload", response_model=Video_View)
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str | None = Form(None),
    db: Session = Depends(get_db)
):
    VIDS_DIR.mkdir(parents=True, exist_ok=True)
    file_location = VIDS_DIR / f"{uuid.uuid4()}_{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    video = Video_Create(
        title=title,
        description=description,
        file_path=str(file_location)
    )

    repo = Video_Repo(db)  # ← this line was missing
    video_db = repo.create_video(video)

    return Video_View(
        id=video_db.id,
        title=video_db.title,
        description=video_db.description,
        video_url=f"http://raspberrypi/{video_db.file_path}"
    )

@router.post("/upload_multiple", response_model=list[Video_View])
async def upload_multiple(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    VIDS_DIR.mkdir(parents=True, exist_ok=True)
    repo = Video_Repo(db)

    async def save_single_file(file):
        file_location = VIDS_DIR / f"{uuid.uuid4()}_{file.filename}"
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        video = Video_Create(
            title=file.filename.rsplit(".", 1)[0],  # strip extension
            description=None,
            file_path=str(file_location)
        )
        video_db = repo.create_video(video)
        return Video_View(
            id=video_db.id,
            title=video_db.title,
            description=video_db.description,
            video_url=f"http://raspberrypi/{video_db.file_path}"
        )

    return await asyncio.gather(*[save_single_file(f) for f in files])



@router.patch("/{video_id}", response_model=Video_View)
def update_video(video_id: int, title: str | None = None, description: str | None = None, db: Session = Depends(get_db)):
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if title is not None:
        video.title = title
    if description is not None:
        video.description = description
    db.commit()
    db.refresh(video)
    return Video_View(
        id=video.id,
        title=video.title,
        description=video.description,
        video_url=f"http://raspberrypi/{video.file_path}"
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

    return StreamingResponse(iterfile(), media_type="video/mp4")

