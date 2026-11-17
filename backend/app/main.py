
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.bugs import router as bugs_router
from app.api.comments import router as comments_router


app = FastAPI(
    title="Bug Tracker API",
    description="A Jira-like Bug and Issue Tracking System",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(bugs_router)
app.include_router(comments_router)


@app.get("/")
def home():
    return {
        "message": "Bug Tracker API is running successfully!",
        "project": "Bug Tracker",
        "version": "1.0.0",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }
