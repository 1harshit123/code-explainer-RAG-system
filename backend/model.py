from datetime import datetime, timezone
from sqlmodel import Field, Relationship, SQLModel


class RepositoryCache(SQLModel, table=True):
    __tablename__ = "repository_cache"
    
    id: int = Field(default=None, primary_key=True)
    repo_link: str = Field(unique=True, index=True) 
    vector_collection_name: str                     
    last_indexed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    sessions: list["ChatSession"] = Relationship(back_populates="repo_cache")

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: int = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str
    profile_pic:str | None = Field(default=None)
    hashed_password: str | None = Field(default=None) # Optional for Google users
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    sessions: list["ChatSession"] = Relationship(back_populates="user")


class ChatSession(SQLModel, table=True):
    __tablename__ = "chat_sessions"

    id: int = Field(default=None, primary_key=True)
    repo_link: str = Field(index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc)) # we are using default_factory because if we do not use that it gives the time when python server boots up not every time single row adds
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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    session: ChatSession = Relationship(back_populates="messages")