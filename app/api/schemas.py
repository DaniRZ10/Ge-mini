from pydantic import BaseModel

class ChatRequest(BaseModel):
    message: str
    model: str
    conversation_id: str | None = None

class ChatResponse(BaseModel):
    response: str
    provider: str
    conversation_id: str

class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    model: str | None
    provider: str | None
    created_at: str
