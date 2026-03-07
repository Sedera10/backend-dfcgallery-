from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database.connection import get_db
from app.database.models import Club
from app.schemas.club_schema import ClubCreate, ClubUpdate, ClubResponse, ClubWithDetails
from app.services.imgbb_service import ImgBBService

router = APIRouter()
# Ne pas instancier au niveau module pour éviter le cache de configuration


@router.get("/", response_model=List[ClubResponse])
def get_all_clubs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer tous les clubs"""
    clubs = db.query(Club).offset(skip).limit(limit).all()
    return clubs


@router.get("/{id_club}", response_model=ClubWithDetails)
def get_club(id_club: int, db: Session = Depends(get_db)):
    """Récupérer un club par son ID"""
    club = db.query(Club).filter(Club.id_club == id_club).first()
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club avec l'ID {id_club} non trouvé"
        )
    return club


@router.post("/", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
def create_club(club: ClubCreate, db: Session = Depends(get_db)):
    """Créer un nouveau club"""
    new_club = Club(**club.model_dump())
    db.add(new_club)
    db.commit()
    db.refresh(new_club)
    return new_club


@router.post("/with-logo", response_model=ClubResponse, status_code=status.HTTP_201_CREATED)
async def create_club_with_logo(
    nom: Optional[str] = Form(None),
    region: str = Form(...),
    id_championnat: int = Form(...),
    logo_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Créer un nouveau club avec upload du logo"""
    try:
        # Upload du logo sur ImgBB
        imgbb_service = ImgBBService()
        upload_result = await imgbb_service.upload_image(
            file=logo_file,
            folder="dfc_gallery_clubs"
        )
        
        # Créer le club avec l'URL du logo
        new_club = Club(
            nom=nom,
            region=region,
            logo=upload_result['secure_url'],
            id_championnat=id_championnat
        )
        
        db.add(new_club)
        db.commit()
        db.refresh(new_club)
        return new_club
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du club: {str(e)}"
        )


@router.put("/{id_club}", response_model=ClubResponse)
def update_club(
    id_club: int,
    club_update: ClubUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un club"""
    club = db.query(Club).filter(Club.id_club == id_club).first()
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club avec l'ID {id_club} non trouvé"
        )
    
    update_data = club_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(club, key, value)
    
    db.commit()
    db.refresh(club)
    return club


@router.delete("/{id_club}", status_code=status.HTTP_204_NO_CONTENT)
def delete_club(id_club: int, db: Session = Depends(get_db)):
    """Supprimer un club"""
    club = db.query(Club).filter(Club.id_club == id_club).first()
    if not club:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Club avec l'ID {id_club} non trouvé"
        )
    
    db.delete(club)
    db.commit()
    return None


@router.get("/championnat/{id_championnat}", response_model=List[ClubResponse])
def get_clubs_by_championnat(id_championnat: int, db: Session = Depends(get_db)):
    """Récupérer tous les clubs d'un championnat"""
    clubs = db.query(Club).filter(Club.id_championnat == id_championnat).all()
    return clubs
