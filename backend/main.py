import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from fastapi.sse import EventSourceResponse
import time


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatPayload(BaseModel):
    message: str

@app.post("/api/chat/stream")
async def stream_rag_chat(payload: ChatPayload):

    async def event_stream():
        yield "Hello! This is the testing response"

    return EventSourceResponse(event_stream())
