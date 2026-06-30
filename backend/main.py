import asyncio
import sys
import hashlib
import os
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.sse import EventSourceResponse
import time, json
from pathlib import Path   
from model import ChatMessage, ChatSession, User, RepositoryCache
from database import init_db, engine
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from datetime import datetime, timedelta, timezone
from typing import Annotated
from dotenv import load_dotenv
from auth import router as auth_router
from auth import get_current_user


current_file = Path(__file__).resolve()

parent_dir = current_file.parent.parent

if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Have to stream line this flow of getting the directory

from pipline.src.RAG.retrival import stream_query_pipeline
from pipline.main import processing_repo

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield 



app = FastAPI(lifespan=lifespan)
app.include_router(auth_router)



origins = [
    "http://localhost:5173",    # Default Vite local development port
    "http://127.0.0.1:5173",    # Loopback IP alternative for Vite
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatPayload(BaseModel):
    repoLink: str

class QueryPayload(BaseModel):
    session_id: int
    message: str






@app.post("/api/repo")
async def repo_vectorization(payload: ChatPayload, current_user: User = Depends(get_current_user)):
    print(f"User {current_user.username} is requesting: {payload.repoLink}")
    repoLink = payload.repoLink.strip()

    if not repoLink:
        return {"Status": "Failed", "Reason": "Empty link"}

    with Session(engine) as session:
        cache_record = session.exec(
            select(RepositoryCache).where(RepositoryCache.repo_link == repoLink)
        ).first()

        if cache_record:
            print("Cache Hit! Skipping ingestion.")
            return {"Status": "Success", "repo": repoLink, "cached": True}
        try:
            # processing_repo(repoLink) # Would work on single setup but can create issues when two or more users use it at the same time, 
            collection_slug = f"repo_{hashlib.md5(repoLink.encode()).hexdigest()}"
            await asyncio.to_thread(processing_repo, repoLink, collection_slug)
            new_cache = RepositoryCache(repo_link=repoLink, vector_collection_name=collection_slug)
            session.add(new_cache)
            session.commit()
            
            return {"Status": "Success", "repo": repoLink, "cached": False}
            
        except Exception as e:
            print(f"[Backend Error]: {e}")
            return {"Status": "Failed", "Reason": str(e)}
    

@app.post("/api/chat/session") 
async def storing_chat_session(payload: ChatPayload, current_user: User = Depends(get_current_user)):
        with Session(engine) as session:
            cache_record = session.exec(select(RepositoryCache).where(RepositoryCache.repo_link == payload.repoLink)).first()
            if not cache_record:
                raise HTTPException(status_code=404, detail="Repo not indexed yet")
            
            try:
                chat_session = ChatSession(
                user_id=current_user.id, 
                repo_cache_id=cache_record.id
            )
            except Exception as e:
                print("exception in creating the chat_session from current_user", e)

            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)

            if not chat_session.id:
                raise HTTPException(status_code=500, detail="Failed to create chat session")
            else:
                return {
                    "session_id": chat_session.id
                }
            

@app.get("/api/chat/history/{session_id}")
async def get_history(session_id: int,  current_user: User = Depends(get_current_user)):
   with Session(engine) as session:
        chat_session = session.get(ChatSession, session_id)
        if not chat_session or chat_session.user_id != current_user.id:
            return {"error": "Unauthorized access to this session"}
        
        statement = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp)
        records = session.exec(statement).all()
        
        return {
            "session_id": session_id,
            "raw_records": [r.id for r in records],
            "all_messages": [{"sender": r.sender, "content": r.content} for r in records]
        }
 
    
@app.post("/api/chat/stream")
async def stream_from_chatbox(payload: QueryPayload, current_user: User = Depends(get_current_user)):
    with Session(engine) as session:
        chat_session = session.get(ChatSession, payload.session_id)
        if not chat_session:
            raise HTTPException(404, "Session not found")
        
        if chat_session.user_id != current_user.id:
            raise HTTPException(403, 'Unauthorized')
        cache = session.get(
            RepositoryCache,
            chat_session.repo_cache_id
        )
        collection_name = cache.vector_collection_name
        
        user_entry = ChatMessage(session_id = payload.session_id, sender = "user", content=payload.message)
        print(f"User entry from the streaming api{user_entry}\n\n")
        session.add(user_entry)
        session.commit()
        session.refresh(user_entry)

        async def steaming_from_pipeline():
            
            full_response_text = ""
            try:
                for token in stream_query_pipeline(payload.message, collection_name):
                    full_response_text += token
                    yield f"data: {json.dumps({'token': token})}"
                    await asyncio.sleep(0.01)  # Important for the end of streaming event

                with Session(engine) as session:
                    bot_entry = ChatMessage(
                        session_id=payload.session_id, 
                        sender="bot", 
                        content=full_response_text
                    )
                    print(f"Bot entry vaiable from the inner loop of the streaming{bot_entry}\n\n")
                    session.add(bot_entry)
                    session.commit()
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(
            steaming_from_pipeline(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no" 
            }

        )




    



