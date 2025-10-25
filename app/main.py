from fastapi import FastAPI
from app.database import engine, Base
from app import models
from app.routes import auth  

app = FastAPI(
    title="Jirani Offline Library Backend",
    description="A FastAPI backend for offline library management",
    version="1.0.0"
)

Base.metadata.create_all(bind=engine)


app.include_router(auth.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Jirani Offline Library Backend"}