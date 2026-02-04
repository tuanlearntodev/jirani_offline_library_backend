from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.database import engine, Base
from app.api import auth_router, book_router
from app import settings  # Import models to register them with Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.COVER_DIR.mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown (if needed)
    engine.dispose()


app = FastAPI(
    title="Jirani Offline Library Backend",
    description="A FastAPI backend for offline library management",
    version="1.0.0",
    lifespan=lifespan
)

# Mount covers directory for public access (books require auth)
app.mount("/static", StaticFiles(directory=settings.COVER_DIR), name="static")

app.include_router(auth_router.router)
app.include_router(book_router.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Jirani Offline Library Backend"}