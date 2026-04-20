from datetime import datetime
from pydantic import BaseModel, ConfigDict
from uuid import UUID

class Message(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int | None = None
    conversation_id: str
    role: str
    content: str
    model: str | None = None
    provider: str | None = None
    created_at: datetime

class Conversation(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    created_at: datetime
    updated_at: datetime
