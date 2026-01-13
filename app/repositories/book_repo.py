from sqlalchemy.orm import Session, joinedload
from app.models import Book, Tag
from app.schemas.book_schema import BookCreate

class BookRepo:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_book_by_uid(self, book_uid: str) -> Book:
        return self.db_session.query(Book).options(joinedload(Book.tags)).filter(Book.uid == book_uid).first()

    def create_book(self, book_create: BookCreate) -> Book:
        tag_data = book_create.tags
        book_dict = book_create.model_dump(exclude={"tags"})
        
        existing = self.db_session.query(Book).filter(Book.uid == book_create.uid).first()
        if existing:
            raise ValueError(f"Book with UID {book_create.uid} already exists")
        
        new_book = Book(**book_dict)
        
        if tag_data:
            for tag_in in tag_data:
                tag = self.db_session.query(Tag).filter(Tag.name.ilike(tag_in.name)).first()
                if not tag:
                    tag = Tag(name=tag_in.name.strip().tolower())
                new_book.tags.append(tag)

        try:
            self.db_session.add(new_book)
            self.db_session.commit()
            self.db_session.refresh(new_book)
            return new_book
        except Exception as e:
            self.db_session.rollback()
            raise Exception(f"Failed to create book in database: {str(e)}")
    
    def get_all_books(self) -> list[Book]:
        return self.db_session.query(Book).all()
    
    