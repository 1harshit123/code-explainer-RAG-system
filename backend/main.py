import asyncio
import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.sse import EventSourceResponse
import time, json
from pathlib import Path   
from model import ChatMessage, ChatSession
from database import init_db, engine
from contextlib import asynccontextmanager
from sqlmodel import Session, select

current_file = Path(__file__).resolve()

parent_dir = current_file.parent.parent

if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from pipline.src.RAG.retrival import stream_query_pipeline
from pipline.main import processing_repo

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield 


app = FastAPI(lifespan=lifespan)



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
async def repo_vectorization(payload: ChatPayload):
    print(f"Link: {payload.repoLink}")

    repoLink = payload.repoLink

    if(payload.repoLink):
        try:
            processing_repo(repoLink)
        except Exception as e:
            print(f"[Backend]: error in processing repository.")

        return {
            "Status": "Success",
            "repo" : payload.repoLink
        }
    

@app.post("/api/chat/session") 
async def storing_chat_session(payload: ChatPayload):
    try:
        with Session(engine) as session:
            chat_session = ChatSession(repo_link=payload.repoLink)
            print(chat_session) # debuggin
            session.add(chat_session)
            session.commit()
            session.refresh(chat_session)
            return {"status": "Success", "session_id": chat_session.id}

    except Exception as e:
        print("Error while creating the chatsession", e)

@app.get("/api/chat/history/{session_id}")
async def get_history(session_id: int):
    with Session(engine) as session:
        statement = select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.timestamp)
        print(f"statement variable{statement}\n\n")
        records = session.exec(statement).all()
        print(f"records variable{records}\n\n")
        return {
            "session_id": session_id,
            "raw_records": records,
            "all_messages": [{"sender": r.sender, "content": r.content} for r in records]
        }
 
    
@app.post("/api/chat/stream")
async def stream_from_chatbox(payload: QueryPayload):
    with Session(engine) as session:
        user_entry = ChatMessage(session_id = payload.session_id, sender = "user", content=payload.message)
        print(f"User entry from the streaming api{user_entry}\n\n")
        session.add(user_entry)
        session.commit()
        session.refresh(user_entry)

        async def steaming_from_pipeline():
            full_response_text = ""
            try:
                for token in stream_query_pipeline(payload.message):
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




    



