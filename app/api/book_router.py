from fastapi import APIRouter, Depends, File, UploadFile, Form, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
import json
from fastapi.responses import FileResponse

from app.database import get_db
from app.services.book_service import BookService
from app.repositories.book_repo import BookRepo
from app.schemas import BookUpload, BookBase
from app.schemas.tag_schema import TagCreate

router = APIRouter(prefix="/books", tags=["books"])

def get_book_service(db: Session = Depends(get_db)) -> BookService:
    book_repo = BookRepo(db)
    return BookService(book_repo)

from fastapi.responses import FileResponse

@router.post("/upload", response_model=BookBase)
async def upload_new_book(
    title: Optional[str] = Form(None),
    tags: str = Form(""),          # ← was "[]", now empty string
    publisher_id: Optional[int] = Form(None),   # ← add this
    file: UploadFile = File(...),
    book_service: BookService = Depends(get_book_service)
):
    try:
        tag_list = []
        if tags.strip():
            tag_list = [TagCreate(name=t.strip()).model_dump() for t in tags.split(",") if t.strip()]
        metadata = BookUpload(title=title, tags=tag_list)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid tags format: {str(e)}")

    return await book_service.upload_book(metadata, file, publisher_id)

@router.get("/search/", response_model=list[BookBase])
async def search_books(
    title: Optional[str] = Query(None, description="Search by book title (case-insensitive, partial match)"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
    file_type: Optional[str] = Query(None, description="Filter by file type (e.g., epub, pdf)"),
    extension: Optional[str] = Query(None, description="Filter by file extension"),
    book_service: BookService = Depends(get_book_service)
):
    """
    Dynamic search endpoint for books with multiple optional filters.
    All parameters are optional - if none provided, returns all books.
    """
    # Parse tags if provided
    tag_list = None
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    return book_service.search_books(
        title=title,
        tags=tag_list,
        file_type=file_type,
        extension=extension
    )

@router.get("/{book_uid}/read")
async def read_book(
    book_uid: str,
    db: Session = Depends(get_db)
):
    from app.repositories.book_repo import BookRepo
    from app import settings

    book = BookRepo(db).get_book_by_uid(book_uid)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    file_path = settings.UPLOAD_DIR / book.file_path
    print(f"DEBUG: looking for file at {file_path}")
    print(f"DEBUG: exists = {file_path.exists()}")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found at {file_path}")

    return FileResponse(path=file_path, media_type="application/pdf")

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
     publisher_id: Optional[int] = Form(None),
    book_service: BookService = Depends(get_book_service)
):
    """Teacher endpoint to update book metadata and optional cover."""
    # Convert tags_json string back to list for the schema
    try:
        tag_list = []
        if tags.strip():
            # Create TagCreate objects and convert to dict for BookUpload
            tag_list = [TagCreate(name=t.strip()).model_dump() for t in tags.split(",") if t.strip()]

        metadata = BookUpload(title=title, tags=tag_list)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid tags format: {str(e)}")

    return await book_service.update_book(book_uid, metadata, cover, publisher_id)

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



