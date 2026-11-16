"""Entry point - OncoPet API v3."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from .config import INSTANCE_NAME
from .database import engine, Base
from .mongodb import connect_mongodb, close_mongodb
from .routers import analytics, auth, palliative, reports, tutors, vets, pets, protocols, sessions, records, documents, clinics, reminders, exams, uploads

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


@app.middleware("http")
async def add_instance_header(request: Request, call_next):
    """Diz qual copia do backend respondeu (para ver o load balancer funcionando)."""
    response = await call_next(request)
    response.headers["X-Backend-Instance"] = INSTANCE_NAME
    return response


app.include_router(auth.router)
app.include_router(clinics.router)
app.include_router(tutors.router)
app.include_router(vets.router)
app.include_router(pets.router)
app.include_router(protocols.router)
app.include_router(analytics.router)
app.include_router(palliative.router)
app.include_router(reports.router)
app.include_router(sessions.router)
app.include_router(records.router)
app.include_router(documents.router)
app.include_router(reminders.router)
app.include_router(exams.router)
app.include_router(uploads.router)


@app.get("/api/health", tags=["saude"])
def health():
    """Usada pelo load balancer (Caddy) para saber se esta copia esta no ar. Nao exige login."""
    return {"status": "ok", "instance": INSTANCE_NAME}


@app.get("/")
def root():
    return {"message": "OncoPet API v3.1", "docs": "/docs"}
