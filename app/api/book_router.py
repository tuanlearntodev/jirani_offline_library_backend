from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import json

from app.database import get_db
from app.services.book_service import BookService
from app.repositories.book_repo import BookRepo
from app.schemas import BookUpload, BookBase
from app.schemas.tag_schema import TagCreate

router = APIRouter(prefix="/books", tags=["books"])


def get_book_service(db: Session = Depends(get_db)) -> BookService:
    book_repo = BookRepo(db)
    return BookService(book_repo)


@router.post("/upload", response_model=BookBase)
async def upload_new_book(
    title: Optional[str] = Form(None),
    tags: str = Form("[]"),  
    file: UploadFile = File(...),
    cover: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Teacher endpoint to upload a book and optional cover."""
    repo = BookRepo(db)
    service = BookService(repo)
    
    # Convert tags_json string back to list for the schema
    try:
        tag_list = []
        if tags.strip():
            # Create TagCreate objects and convert to dict for BookUpload
            tag_list = [TagCreate(name=t.strip()).model_dump() for t in tags.split(",") if t.strip()]

        metadata = BookUpload(title=title, tags=tag_list)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid tags format: {str(e)}")

    return await service.upload_book(metadata, file, cover)

@router.get("/{book_uid}", response_model=BookBase)
async def get_book_details(
    book_uid: str,
    book_service: BookService = Depends(get_book_service)
):
    """Get book details by UID."""
    book = book_service.get_book_by_uid(book_uid)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.put("/{book_uid}", response_model=BookBase)
async def update_book(
    book_uid: str,
    title: Optional[str] = Form(None),
    tags: str = Form("[]"),  
    cover: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db)
):
    """Teacher endpoint to update book metadata and optional cover."""
    repo = BookRepo(db)
    service = BookService(repo)
    
    # Convert tags_json string back to list for the schema
    try:
        tag_list = []
        if tags.strip():
            # Create TagCreate objects and convert to dict for BookUpload
            tag_list = [TagCreate(name=t.strip()).model_dump() for t in tags.split(",") if t.strip()]

        metadata = BookUpload(title=title, tags=tag_list)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid tags format: {str(e)}")

    return await service.update_book(book_uid, metadata, cover)

@router.delete("/{book_uid}", status_code=204)
async def delete_book(
    book_uid: str,
    book_service: BookService = Depends(get_book_service)
):
    """Teacher endpoint to delete a book by UID."""
    try:
        book_service.delete_book(book_uid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return

