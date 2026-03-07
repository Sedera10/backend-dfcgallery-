from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db, SessionLocal
from app.database.models import Photo, FaceDetection, JerseyDetection, Match
from app.schemas.photo_schema import PhotoCreate, PhotoUpdate, PhotoResponse, PhotoWithFaces
from app.services.imgbb_service import ImgBBService
from app.services.face_recognition_service import FaceRecognitionService
from app.services.jersey_ocr_service import JerseyOCRService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


def _encode_photo_faces_bg(photo_id: int, image_url: str):
    """Background task : encode les visages + détecte les numéros de maillot."""
    db = SessionLocal()
    try:
        # 1. Encodage facial
        svc = FaceRecognitionService()
        svc.encode_faces_in_photo(photo_id, image_url, db)
        
        # 2. Détection numéros de maillot (OCR)
        ocr = JerseyOCRService()
        ocr.detect_and_store(photo_id, image_url, db)
    except Exception as e:
        logger.error("BG encoding error photo %s: %s", photo_id, e)
    finally:
        db.close()


@router.get("/", response_model=List[PhotoResponse])
def get_all_photos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer toutes les photos"""
    photos = db.query(Photo).offset(skip).limit(limit).all()
    return photos


@router.get("/{id_photo}", response_model=PhotoWithFaces)
def get_photo(id_photo: int, db: Session = Depends(get_db)):
    """Récupérer une photo par son ID"""
    photo = db.query(Photo).filter(Photo.id_photo == id_photo).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo avec l'ID {id_photo} non trouvée"
        )
    return photo


@router.post("/upload/{id_match}", response_model=PhotoResponse, status_code=status.HTTP_201_CREATED)
async def upload_photo(
    id_match: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload une photo et lance l'encodage facial en background"""
    match = db.query(Match).filter(Match.id_match == id_match).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match avec l'ID {id_match} non trouvé"
        )
    
    imgbb_service = ImgBBService()
    upload_result = await imgbb_service.upload_image(file, folder=f"matches_{id_match}")
    
    new_photo = Photo(url=upload_result["secure_url"], id_match=id_match)
    db.add(new_photo)
    db.commit()
    db.refresh(new_photo)
    
    # Encodage facial en background
    background_tasks.add_task(_encode_photo_faces_bg, new_photo.id_photo, new_photo.url)
    
    return new_photo


@router.post("/upload-multiple/{id_match}", response_model=List[PhotoResponse], status_code=status.HTTP_201_CREATED)
async def upload_multiple_photos(
    id_match: int,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload plusieurs photos et lance l'encodage facial en background"""
    match = db.query(Match).filter(Match.id_match == id_match).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match avec l'ID {id_match} non trouvé"
        )
    
    MAX_FILES = 20
    if len(files) > MAX_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum {MAX_FILES} fichiers par upload. Vous en avez envoyé {len(files)}."
        )
    
    imgbb_service = ImgBBService()
    uploaded_photos = []
    errors = []
    
    for i, file in enumerate(files):
        try:
            upload_result = await imgbb_service.upload_image(file, folder=f"matches_{id_match}")
            new_photo = Photo(url=upload_result["secure_url"], id_match=id_match)
            db.add(new_photo)
            db.flush()
            uploaded_photos.append(new_photo)
        except Exception as e:
            errors.append(f"Fichier {i+1} ({file.filename}): {str(e)}")
    
    if uploaded_photos:
        db.commit()
        for photo in uploaded_photos:
            db.refresh(photo)
            # Encodage facial en background pour chaque photo
            background_tasks.add_task(_encode_photo_faces_bg, photo.id_photo, photo.url)
    
    if errors and not uploaded_photos:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Aucune photo uploadée. Erreurs: {'; '.join(errors)}"
        )
    
    return uploaded_photos


@router.post("/{id_photo}/detect-faces", response_model=PhotoWithFaces)
async def detect_faces_in_photo(
    id_photo: int,
    db: Session = Depends(get_db)
):
    """Détecter les visages dans une photo et les enregistrer"""
    photo = db.query(Photo).filter(Photo.id_photo == id_photo).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo avec l'ID {id_photo} non trouvée"
        )
    
    # Détection des visages
    face_service = FaceRecognitionService()
    faces = await face_service.detect_faces(photo.url, db)
    
    # Enregistrer les détections en base
    for face_data in faces:
        face_detection = FaceDetection(
            id_photo=id_photo,
            id_joueur=face_data.get("id_joueur"),
            encoding=face_data.get("encoding")
        )
        db.add(face_detection)
    
    db.commit()
    db.refresh(photo)
    
    return photo


@router.delete("/{id_photo}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_photo(id_photo: int, db: Session = Depends(get_db)):
    """Supprimer une photo et ses détections faciales"""
    photo = db.query(Photo).filter(Photo.id_photo == id_photo).first()
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Photo avec l'ID {id_photo} non trouvée"
        )
    
    # Supprimer les détections faciales et jersey liées
    db.query(FaceDetection).filter(FaceDetection.id_photo == id_photo).delete()
    db.query(JerseyDetection).filter(JerseyDetection.id_photo == id_photo).delete()
    
    # Supprimer de ImgBB (best effort)
    imgbb_service = ImgBBService()
    await imgbb_service.delete_image(photo.url)
    
    db.delete(photo)
    db.commit()
    return None


@router.get("/match/{id_match}", response_model=List[PhotoResponse])
def get_photos_by_match(id_match: int, db: Session = Depends(get_db)):
    """Récupérer toutes les photos d'un match"""
    photos = db.query(Photo).filter(Photo.id_match == id_match).all()
    return photos
