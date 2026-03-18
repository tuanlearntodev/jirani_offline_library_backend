from app.database import Base
from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime, timezone

class Video(Base):
    __tablename__ = "video"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable = True)
    file_path = Column(String, nullable = False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc)) # sets it automatically at insert
    deleted_at = Column(DateTime, nullable = True, default = None )
    
   


