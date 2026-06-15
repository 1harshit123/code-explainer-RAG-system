import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.sse import EventSourceResponse
import time


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

@app.post("/api/chat/stream")
async def stream_rag_chat(payload: ChatPayload):
    print(f"Link: {payload.repoLink}")

    if(payload.repoLink):
        return {
            "Status": "Success",
            "repo" : payload.repoLink
        }
    
    



