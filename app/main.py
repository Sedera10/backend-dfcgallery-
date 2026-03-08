from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.database.connection import engine, Base
from app.routers import joueurs, clubs, matches, photos, championnats

# Créer les tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DFC Gallery API",
    description="API pour la gestion de photos de matchs de football avec reconnaissance faciale",
    version="1.0.0"
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permettre toutes les origines en développement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrer les routers
app.include_router(championnats.router, prefix="/api/championnats", tags=["Championnats"])
app.include_router(joueurs.router, prefix="/api/joueurs", tags=["Joueurs"])
app.include_router(clubs.router, prefix="/api/clubs", tags=["Clubs"])
app.include_router(matches.router, prefix="/api/matches", tags=["Matches"])
app.include_router(photos.router, prefix="/api/photos", tags=["Photos"])

@app.get("/")
def root():
    return {
        "message": "Bienvenue sur l'API DFC Gallery",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
