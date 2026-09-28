"""Entry point - OncoPet API v3."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import engine, Base
from .mongodb import connect_mongodb, close_mongodb
from .routers import auth, tutors, vets, pets, sessions, records, documents, clinics, reminders, exams, uploads

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia lifecycle: conecta MongoDB no startup, fecha no shutdown."""
    await connect_mongodb()
    yield
    await close_mongodb()


app = FastAPI(title="OncoPet API", version="3.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(clinics.router)
app.include_router(tutors.router)
app.include_router(vets.router)
app.include_router(pets.router)
app.include_router(sessions.router)
app.include_router(records.router)
app.include_router(documents.router)
app.include_router(reminders.router)
app.include_router(exams.router)
app.include_router(uploads.router)


@app.get("/")
def root():
    return {"message": "OncoPet API v3.1", "docs": "/docs"}
