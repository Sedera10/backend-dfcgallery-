from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.database.connection import get_db, SessionLocal
from app.database.models import Joueur, FaceDetection, Photo
from app.schemas.joueur_schema import JoueurCreate, JoueurUpdate, JoueurResponse, JoueurWithClub
from app.services.imgbb_service import ImgBBService
from app.services.face_recognition_service import FaceRecognitionService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def _encode_player_face_bg(joueur_id: int, image_url: str):
    """Background task : encode le visage du joueur."""
    db = SessionLocal()
    try:
        svc = FaceRecognitionService()
        svc.encode_player_face(joueur_id, image_url, db)
    except Exception as e:
        logger.error("BG face encoding error joueur %s: %s", joueur_id, e)
    finally:
        db.close()


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
    background_tasks: BackgroundTasks,
    nom: str = Form(...),
    prenom: str = Form(...),
    dt_naissance: Optional[str] = Form(None),
    id_club: int = Form(...),
    poste: str = Form(...),
    numero: Optional[int] = Form(None),
    photo_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Créer un nouveau joueur avec upload de la photo de profil + encodage facial"""
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
        
        # Encodage facial en background
        background_tasks.add_task(_encode_player_face_bg, new_joueur.id_joueur, new_joueur.pdp)
        
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
    """Trouver toutes les photos contenant le visage d'un joueur"""
    joueur = db.query(Joueur).filter(Joueur.id_joueur == id_joueur).first()
    if not joueur:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Joueur avec l'ID {id_joueur} non trouvé"
        )
    
    svc = FaceRecognitionService()
    photo_ids = svc.find_player_photos(id_joueur, db)
    
    if not photo_ids:
        return {"joueur": JoueurResponse.model_validate(joueur), "photos": [], "count": 0}
    
    # Récupérer les photos dans l'ordre des matchs
    photos = db.query(Photo).filter(Photo.id_photo.in_(photo_ids)).all()
    
    # Garder l'ordre de pertinence (distance faciale)
    photo_map = {p.id_photo: p for p in photos}
    ordered_photos = [photo_map[pid] for pid in photo_ids if pid in photo_map]
    
    from app.schemas.photo_schema import PhotoResponse
    return {
        "joueur": JoueurResponse.model_validate(joueur),
        "photos": [PhotoResponse.model_validate(p) for p in ordered_photos],
        "count": len(ordered_photos)
    }


@router.get("/{id_joueur}/face-status")
def get_joueur_face_status(id_joueur: int, db: Session = Depends(get_db)):
    """Vérifier si le visage d'un joueur est encodé"""
    has_encoding = db.query(FaceDetection).filter(
        FaceDetection.id_joueur == id_joueur,
        FaceDetection.id_photo.is_(None)
    ).first() is not None
    return {"id_joueur": id_joueur, "face_encoded": has_encoding}


@router.post("/{id_joueur}/encode-face")
def encode_joueur_face(id_joueur: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Déclencher manuellement l'encodage du visage d'un joueur existant"""
    joueur = db.query(Joueur).filter(Joueur.id_joueur == id_joueur).first()
    if not joueur:
        raise HTTPException(status_code=404, detail="Joueur non trouvé")
    if not joueur.pdp:
        raise HTTPException(status_code=400, detail="Le joueur n'a pas de photo de profil")
    
    background_tasks.add_task(_encode_player_face_bg, joueur.id_joueur, joueur.pdp)
    return {"message": "Encodage lancé en background", "id_joueur": id_joueur}


@router.post("/encode-all-faces")
def encode_all_joueur_faces(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Encoder le visage de tous les joueurs qui n'ont pas encore d'encodage"""
    joueurs = db.query(Joueur).filter(Joueur.pdp.isnot(None)).all()
    count = 0
    for j in joueurs:
        has = db.query(FaceDetection).filter(
            FaceDetection.id_joueur == j.id_joueur,
            FaceDetection.id_photo.is_(None)
        ).first()
        if not has:
            background_tasks.add_task(_encode_player_face_bg, j.id_joueur, j.pdp)
            count += 1
    return {"message": f"Encodage lancé pour {count} joueur(s)", "count": count}


@router.post("/encode-all-photos")
def encode_all_photos(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Encoder les visages de toutes les photos qui n'ont pas encore d'encodage"""
    from app.database.connection import SessionLocal
    # Photos sans aucune détection
    photos_with_detections = db.query(FaceDetection.id_photo).filter(
        FaceDetection.id_photo.isnot(None)
    ).distinct().subquery()
    
    photos_without = db.query(Photo).filter(
        ~Photo.id_photo.in_(db.query(photos_with_detections))
    ).all()
    
    count = len(photos_without)
    for photo in photos_without:
        def _bg(pid=photo.id_photo, purl=photo.url):
            dbs = SessionLocal()
            try:
                svc = FaceRecognitionService()
                svc.encode_faces_in_photo(pid, purl, dbs)
            except Exception as e:
                logger.error("BG encode photo %s: %s", pid, e)
            finally:
                dbs.close()
        background_tasks.add_task(_bg)
    
    return {"message": f"Encodage lancé pour {count} photo(s)", "count": count}


@router.post("/detect-all-jerseys")
def detect_all_jerseys(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Détecter les numéros de maillot (OCR) dans toutes les photos non encore traitées"""
    from app.database.connection import SessionLocal
    from app.database.models import JerseyDetection
    from app.services.jersey_ocr_service import JerseyOCRService
    
    # Photos déjà traitées par OCR
    photos_with_jersey = db.query(JerseyDetection.id_photo).distinct().subquery()
    
    photos_without = db.query(Photo).filter(
        ~Photo.id_photo.in_(db.query(photos_with_jersey))
    ).all()
    
    count = len(photos_without)
    for photo in photos_without:
        def _bg(pid=photo.id_photo, purl=photo.url):
            dbs = SessionLocal()
            try:
                ocr = JerseyOCRService()
                ocr.detect_and_store(pid, purl, dbs)
            except Exception as e:
                logger.error("BG jersey OCR photo %s: %s", pid, e)
            finally:
                dbs.close()
        background_tasks.add_task(_bg)
    
    return {"message": f"Détection OCR lancée pour {count} photo(s)", "count": count}
