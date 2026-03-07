from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.database.models import Championnat
from app.schemas.club_schema import ChampionnatResponse

router = APIRouter()


@router.get("/", response_model=List[ChampionnatResponse])
def get_all_championnats(db: Session = Depends(get_db)):
    """Récupérer tous les championnats"""
    championnats = db.query(Championnat).all()
    return championnats


@router.get("/{id_championnat}", response_model=ChampionnatResponse)
def get_championnat(id_championnat: int, db: Session = Depends(get_db)):
    """Récupérer un championnat par son ID"""
    championnat = db.query(Championnat).filter(
        Championnat.id_championnat == id_championnat
    ).first()
    if not championnat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Championnat avec l'ID {id_championnat} non trouvé"
        )
    return championnat
