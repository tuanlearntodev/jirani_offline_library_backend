from app.database import Base
from sqlalchemy import Column, Integer, String, CheckConstraint
from sqlalchemy.orm import relationship


class Publisher(Base):
    __tablename__ = "publishers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    books = relationship("Book", back_populates="publisher")