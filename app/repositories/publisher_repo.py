from sqlalchemy.orm import Session, joinedload
from app.models import Book, Publisher
from app.schemas.publisher_schema import PublisherCreate

class PublisherRepo:
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def get_publisher_by_id(self, publisher_id: int) -> Publisher:
        return self.db_session.query(Publisher).options(joinedload(Publisher.books)).filter(Publisher.id == publisher_id).first()

    def create_publisher(self, publisher_create: PublisherCreate) -> Publisher:
        new_publisher = Publisher(**publisher_create.model_dump())
        self.db_session.add(new_publisher)
        self.db_session.commit()
        self.db_session.refresh(new_publisher)
        return new_publisher
    
    def get_all_publishers(self) -> list[Publisher]:
        return self.db_session.query(Publisher).all()
