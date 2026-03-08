from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database.connection import get_db
from app.database.models import Joueur, Photo
from app.schemas.joueur_schema import JoueurCreate, JoueurUpdate, JoueurResponse, JoueurWithClub
from app.services.imgbb_service import ImgBBService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[JoueurResponse])
def get_all_joueurs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer tous les joueurs"""
    joueurs = db.query(Joueur).offset(skip).limit(limit).all()
    return joueurs


@router.get("/{id_joueur}", response_model=JoueurWithClub)
def get_joueur(id_joueur: int, db: Session = Depends(get_db)):
    """Récupérer un joueur par son ID"""
    joueur = db.query(Joueur).filter(Joueur.id_joueur == id_joueur).first()
    if not joueur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Joueur avec l'ID {id_joueur} non trouvé"
        )
    return joueur


@router.post("/", response_model=JoueurResponse, status_code=status.HTTP_201_CREATED)
def create_joueur(joueur: JoueurCreate, db: Session = Depends(get_db)):
    """Créer un nouveau joueur"""
    new_joueur = Joueur(**joueur.model_dump())
    db.add(new_joueur)
    db.commit()
    db.refresh(new_joueur)
    return new_joueur


@router.post("/with-photo", response_model=JoueurResponse, status_code=status.HTTP_201_CREATED)
async def create_joueur_with_photo(
    nom: str = Form(...),
    prenom: str = Form(...),
    dt_naissance: Optional[str] = Form(None),
    id_club: int = Form(...),
    poste: str = Form(...),
    numero: Optional[int] = Form(None),
    photo_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Créer un nouveau joueur avec upload de la photo de profil"""
    try:
        imgbb_service = ImgBBService()
        upload_result = await imgbb_service.upload_image(
            file=photo_file,
            folder="dfc_gallery_players"
        )
        
        dt_naissance_obj = None
        if dt_naissance:
            from datetime import datetime
            dt_naissance_obj = datetime.strptime(dt_naissance, "%Y-%m-%d").date()
        
        new_joueur = Joueur(
            nom=nom,
            prenom=prenom,
            dt_naissance=dt_naissance_obj,
            pdp=upload_result['secure_url'],
            id_club=id_club,
            poste=poste,
            numero=numero
        )
        
        db.add(new_joueur)
        db.commit()
        db.refresh(new_joueur)
        
        return new_joueur
        
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du joueur: {str(e)}"
        )


@router.put("/{id_joueur}", response_model=JoueurResponse)
def update_joueur(
    id_joueur: int,
    joueur_update: JoueurUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un joueur"""
    joueur = db.query(Joueur).filter(Joueur.id_joueur == id_joueur).first()
    if not joueur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Joueur avec l'ID {id_joueur} non trouvé"
        )
    
    update_data = joueur_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(joueur, key, value)
    
    db.commit()
    db.refresh(joueur)
    return joueur


@router.delete("/{id_joueur}", status_code=status.HTTP_204_NO_CONTENT)
def delete_joueur(id_joueur: int, db: Session = Depends(get_db)):
    """Supprimer un joueur"""
    joueur = db.query(Joueur).filter(Joueur.id_joueur == id_joueur).first()
    if not joueur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Joueur avec l'ID {id_joueur} non trouvé"
        )
    
    db.delete(joueur)
    db.commit()
    return None


@router.get("/club/{id_club}", response_model=List[JoueurResponse])
def get_joueurs_by_club(id_club: int, db: Session = Depends(get_db)):
    """Récupérer tous les joueurs d'un club"""
    joueurs = db.query(Joueur).filter(Joueur.id_club == id_club).all()
    return joueurs


@router.get("/search/", response_model=List[JoueurResponse])
def search_joueurs(q: str, db: Session = Depends(get_db)):
    """Rechercher des joueurs par mot-clé (nom ou prénom)"""
    if not q or len(q.strip()) < 2:
        return []
    keyword = f"%{q.strip()}%"
    joueurs = db.query(Joueur).filter(
        (Joueur.nom.ilike(keyword)) | (Joueur.prenom.ilike(keyword))
    ).limit(20).all()
    return joueurs


@router.get("/{id_joueur}/photos")
def get_joueur_photos(id_joueur: int, db: Session = Depends(get_db)):
    """Trouver toutes les photos contenant un joueur (fonctionnalité à venir)"""
    joueur = db.query(Joueur).filter(Joueur.id_joueur == id_joueur).first()
    if not joueur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Joueur avec l'ID {id_joueur} non trouvé"
        )
    
    return {"joueur": JoueurResponse.model_validate(joueur), "photos": [], "count": 0}


@router.get("/{id_joueur}/face-status")
def get_joueur_face_status(id_joueur: int, db: Session = Depends(get_db)):
    """Vérifier si le visage d'un joueur est encodé (fonctionnalité à venir)"""
    return {"id_joueur": id_joueur, "face_encoded": False}


@router.post("/{id_joueur}/encode-face")
def encode_joueur_face(id_joueur: int, db: Session = Depends(get_db)):
    """Encodage facial (fonctionnalité à venir)"""
    return {"message": "Fonctionnalité non disponible pour le moment", "id_joueur": id_joueur}


@router.post("/encode-all-faces")
def encode_all_joueur_faces(db: Session = Depends(get_db)):
    """Encoder tous les visages (fonctionnalité à venir)"""
    return {"message": "Fonctionnalité non disponible pour le moment", "count": 0}


@router.post("/encode-all-photos")
def encode_all_photos(db: Session = Depends(get_db)):
    """Encoder les visages des photos (fonctionnalité à venir)"""
    return {"message": "Fonctionnalité non disponible pour le moment", "count": 0}


@router.post("/detect-all-jerseys")
def detect_all_jerseys(db: Session = Depends(get_db)):
    """Détection OCR des maillots (fonctionnalité à venir)"""
    return {"message": "Fonctionnalité non disponible pour le moment", "count": 0}
