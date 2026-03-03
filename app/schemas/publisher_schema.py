from pydantic import BaseModel, ConfigDict, field_validator, Field
import re

class PublisherBase(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
    
class PublisherRead(PublisherBase):
    id: int
  
class PublisherCreate(PublisherBase):
    name: str = Field(..., min_length=1, max_length=100)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate publisher name"""
        if not v or not v.strip():
            raise ValueError('Publisher name cannot be empty or whitespace only')
        
        # Remove extra whitespace
        v = ' '.join(v.split())
        
        # Check length after stripping
        if len(v) < 1 or len(v) > 100:
            raise ValueError('Publisher name must be between 1 and 100 characters')
        
        # Check for invalid characters (allow letters, numbers, spaces, hyphens, underscores, periods, commas)
        if not re.match(r'^[\w\s\-.,&()]+$', v):
            raise ValueError('Publisher name can only contain letters, numbers, spaces, hyphens, periods, commas, ampersands, and parentheses')
        
        return v
