import asyncio
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.sse import EventSourceResponse
import time, json
from pathlib import Path   

ROOT_DIR = str(Path(__file__).resolve().parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
from pipline.main import processing_repo
from pipline.src.RAG.retrival import stream_query_pipeline
from database import checking_database


app = FastAPI()



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
    
@app.post("/api/chat/stream")
async def stream_from_chatbox(payload: QueryPayload):
    print(f"User Query Target Received: {payload.message}")

    async def sse_event_generator():
        try:
            # Directly loop through the sync generator from retrival.py
            for token in stream_query_pipeline(payload.message):
                yield f"data: {json.dumps({'token': token})}\n\n"
                await asyncio.sleep(0.01)  # Keeps event loop unblocked
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" 
        }
    )

@app.get("/api/chat/test")
async def database_checking():
    result = checking_database()
    actual_value = next(result)

    if actual_value:
        return {
            "Status": "Success",
            "Comment": "Database is well connected"

        }
    else:
        return {
            "Status": "Failure",
            "Comment": "Database is not connected",
            "actual_value": {actual_value}

        }


    



