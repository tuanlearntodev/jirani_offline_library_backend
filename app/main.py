from fastapi import FastAPI
from app.database import engine, Base
from app import models  # Import models so they're registered with Base

app = FastAPI(
    title="Jirani Offline Library Backend",
    description="A FastAPI backend for offline library management",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)

@app.get("/")
async def root():
    return {"message": "Welcome to Jirani Offline Library Backend"}