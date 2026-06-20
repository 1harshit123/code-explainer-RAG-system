from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel

class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    id: int = Field(default=None, primary_key=True)
    repo_link: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now(datetime.timezone.utc))
    messages: list["ChatMessage"] = Relationship(
        back_populates="session", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

class ChatMessage(SQLModel, table=True):
    __tablename__ = "chat_messages"

    id: int = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chat_sessions.id", index=True)
    sender: str = Field(description="Must be 'user' or 'assistant'")
    content: str
    timestamp: datetime = Field(default_factory=datetime.now(datetime.timezone.utc))

    session: ChatSession = Relationship(back_populates="messages")