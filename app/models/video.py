from app.database import Base
from sqlalchemy import Column, String, Integer

class Video(Base):
    __table__name = "video"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable = True)
    file_path = Column(String, nullable = False)

 
   


