from pydantic import BaseModel
from typing import Optional, List


class ChampionnatBase(BaseModel):
    libelle: str
    ligue: Optional[str] = None


class ChampionnatResponse(ChampionnatBase):
    id_championnat: int
    
    class Config:
        from_attributes = True


class ClubBase(BaseModel):
    nom: Optional[str] = None
    region: str
    logo: Optional[str] = None
    id_championnat: int


class ClubCreate(ClubBase):
    pass


class ClubUpdate(BaseModel):
    nom: Optional[str] = None
    region: Optional[str] = None
    logo: Optional[str] = None
    id_championnat: Optional[int] = None


class ClubResponse(ClubBase):
    id_club: int
    
    class Config:
        from_attributes = True


class ClubWithDetails(ClubResponse):
    championnat: Optional[ChampionnatResponse] = None
    joueurs: Optional[List["JoueurResponse"]] = None
    
    class Config:
        from_attributes = True


# Éviter l'import circulaire
from app.schemas.joueur_schema import JoueurResponse
ClubWithDetails.model_rebuild()
