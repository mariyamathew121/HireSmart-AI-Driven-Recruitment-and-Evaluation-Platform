from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .auth import router as auth_router
from .questions import router as questions_router
from .proctoring import router as proctoring_router
from contextlib import asynccontextmanager
from aiortc import RTCPeerConnection


# Initialize FastAPI with lifespan
app = FastAPI()

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow requests from React frontend
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth_router)
app.include_router(questions_router)
app.include_router(proctoring_router)

# Run with: uvicorn app.main:app --reload
