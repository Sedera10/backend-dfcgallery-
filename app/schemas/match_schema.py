from pydantic import BaseModel
from typing import Optional
from datetime import date, time, datetime


class TypeMatchBase(BaseModel):
    libelle: str


class TypeMatchResponse(TypeMatchBase):
    id_type_match: int
    
    class Config:
        from_attributes = True


class MatchBase(BaseModel):
    stade: Optional[str] = None
    date_match: date
    heure: time
    id_type_match: int
    id_club_home: int
    id_club_away: int


class MatchCreate(MatchBase):
    pass


class MatchUpdate(BaseModel):
    stade: Optional[str] = None
    date_match: Optional[date] = None
    heure: Optional[time] = None
    id_type_match: Optional[int] = None
    id_club_home: Optional[int] = None
    id_club_away: Optional[int] = None


class MatchResponse(MatchBase):
    id_match: int
    
    class Config:
        from_attributes = True


class MatchWithDetails(MatchResponse):
    type_match: Optional[TypeMatchResponse] = None
    club_home: Optional["ClubResponse"] = None
    club_away: Optional["ClubResponse"] = None
    result: Optional["MatchResultResponse"] = None
    
    class Config:
        from_attributes = True


# Schémas pour MatchResult
class MatchResultBase(BaseModel):
    score_club_1: int = 0
    score_club_2: int = 0


class MatchResultCreate(MatchResultBase):
    id_match: int


class MatchResultUpdate(BaseModel):
    score_club_1: Optional[int] = None
    score_club_2: Optional[int] = None


class MatchResultResponse(MatchResultBase):
    id_result: int
    id_match: int
    date_enregistrement: datetime
    
    class Config:
        from_attributes = True


# Éviter l'import circulaire
from app.schemas.club_schema import ClubResponse
MatchWithDetails.model_rebuild()
