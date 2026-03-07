from pydantic import BaseModel
from typing import Optional
from datetime import date


class JoueurBase(BaseModel):
    nom: str
    prenom: str
    dt_naissance: Optional[date] = None
    pdp: Optional[str] = None
    id_club: int
    poste: str
    numero: Optional[int] = None


class JoueurCreate(JoueurBase):
    pass


class JoueurUpdate(BaseModel):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    dt_naissance: Optional[date] = None
    pdp: Optional[str] = None
    id_club: Optional[int] = None
    poste: Optional[str] = None
    numero: Optional[int] = None


class JoueurResponse(JoueurBase):
    id_joueur: int
    
    class Config:
        from_attributes = True


class JoueurWithClub(JoueurResponse):
    club: Optional["ClubResponse"] = None
    
    class Config:
        from_attributes = True


# Éviter l'import circulaire
from app.schemas.club_schema import ClubResponse
JoueurWithClub.model_rebuild()
