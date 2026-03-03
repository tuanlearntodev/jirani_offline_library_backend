from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.publisher_schema import PublisherCreate, PublisherRead
from app.repositories.publisher_repo import PublisherRepo
from typing import List

router = APIRouter(prefix="/publishers", tags=["publishers"])

@router.post("/", response_model=PublisherRead, status_code=status.HTTP_201_CREATED)
def create_publisher(
    publisher: PublisherCreate,
    db: Session = Depends(get_db)
):
    """Create a new publisher"""
    publisher_repo = PublisherRepo(db)
    
    try:
        new_publisher = publisher_repo.create_publisher(publisher)
        return new_publisher
    except Exception as e:
        # Handle unique constraint violation
        if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Publisher with name '{publisher.name}' already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the publisher"
        )

@router.get("/", response_model=List[PublisherRead])
def get_all_publishers(db: Session = Depends(get_db)):
    """Get all publishers"""
    publisher_repo = PublisherRepo(db)
    return publisher_repo.get_all_publishers()

@router.get("/{publisher_id}", response_model=PublisherRead)
def get_publisher_by_id(
    publisher_id: int,
    db: Session = Depends(get_db)
):
    """Get a publisher by ID"""
    publisher_repo = PublisherRepo(db)
    publisher = publisher_repo.get_publisher_by_id(publisher_id)
    
    if not publisher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Publisher with ID {publisher_id} not found"
        )
    
    return publisher
