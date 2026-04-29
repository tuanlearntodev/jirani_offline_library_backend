# app/api/audio_router.py
from fastapi import APIRouter, File, UploadFile, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.schemas.audio_schema import Audio_Create, Audio_View
from app.repositories.audio_repo import Audio_Repo
from app.models.audio import Audio
from app.database import get_db
import os, shutil, uuid, asyncio

router = APIRouter(prefix="/audio", tags=["audio"])

ALLOWED_AUDIO = {"mp3", "mp4", "wav", "ogg", "m4a", "aac", "flac"}

def validate_audio(filename: str):
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_AUDIO:
        raise HTTPException(status_code=400, detail=f"File type .{ext} not allowed")

@router.get("/", response_model=list[Audio_View])
def get_audio(db: Session = Depends(get_db)):
    tracks = db.query(Audio).filter(Audio.deleted_at == None).all()
    return [
        Audio_View(
            id=a.id,
            title=a.title,
            description=a.description,
            audio_url=f"http://raspberrypi/{a.file_path}"
        ) for a in tracks
    ]

@router.post("/upload", response_model=Audio_View)
async def upload_audio(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    validate_audio(file.filename)
    upload_directory = "uploads/audio"
    os.makedirs(upload_directory, exist_ok=True)
    file_location = f"{upload_directory}/{uuid.uuid4()}_{file.filename}"
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    title = file.filename.rsplit(".", 1)[0]
    repo = Audio_Repo(db)
    audio_db = repo.create_audio(Audio_Create(
        title=title,
        description=None,
        file_path=file_location
    ))
    return Audio_View(
        id=audio_db.id,
        title=audio_db.title,
        description=audio_db.description,
        audio_url=f"http://raspberrypi/{audio_db.file_path}"
    )

@router.post("/upload_multiple", response_model=list[Audio_View])
async def upload_multiple(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    upload_directory = "uploads/audio"
    os.makedirs(upload_directory, exist_ok=True)
    repo = Audio_Repo(db)

    async def save_single(file):
        validate_audio(file.filename)
        file_location = f"{upload_directory}/{uuid.uuid4()}_{file.filename}"
        with open(file_location, "wb") as f:
            shutil.copyfileobj(file.file, f)
        title = file.filename.rsplit(".", 1)[0]
        audio_db = repo.create_audio(Audio_Create(
            title=title,
            description=None,
            file_path=file_location
        ))
        return Audio_View(
            id=audio_db.id,
            title=audio_db.title,
            description=audio_db.description,
            audio_url=f"http://raspberrypi/{audio_db.file_path}"
        )

    return await asyncio.gather(*[save_single(f) for f in files])

@router.patch("/{audio_id}", response_model=Audio_View)
def update_audio(
    audio_id: int,
    title: str | None = None,
    description: str | None = None,
    db: Session = Depends(get_db)
):
    repo = Audio_Repo(db)
    audio = repo.update_audio(audio_id, title, description)
    return Audio_View(
        id=audio.id,
        title=audio.title,
        description=audio.description,
        audio_url=f"http://raspberrypi/{audio.file_path}"
    )

@router.delete("/{audio_id}")
def delete_audio(audio_id: int, db: Session = Depends(get_db)):
    repo = Audio_Repo(db)
    return repo.delete_audio(audio_id)

@router.get("/stream/{audio_id}")
def stream_audio(audio_id: int, db: Session = Depends(get_db)):
    audio = db.query(Audio).filter(Audio.id == audio_id).first()
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found")

    ext = audio.file_path.rsplit(".", 1)[-1].lower()
    media_types = {
        "mp3": "audio/mpeg",
        "mp4": "audio/mp4",
        "wav": "audio/wav",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
        "aac": "audio/aac",
        "flac": "audio/flac"
    }
    media_type = media_types.get(ext, "audio/mpeg")

    def iterfile():
        with open(audio.file_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk

    return StreamingResponse(iterfile(), media_type=media_type)