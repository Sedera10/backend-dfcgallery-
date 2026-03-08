from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.database.connection import get_db
from app.database.models import Photo, FaceDetection, JerseyDetection, Match
from app.schemas.photo_schema import PhotoCreate, PhotoUpdate, PhotoResponse
from app.services.imgbb_service import ImgBBService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/", response_model=List[PhotoResponse])
def get_all_photos(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer toutes les photos"""
    photos = db.query(Photo).offset(skip).limit(limit).all()
    return photos


@router.get("/{id_photo}", response_model=PhotoResponse)
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
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload une photo pour un match"""
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
    
    return new_photo


@router.post("/upload-multiple/{id_match}", response_model=List[PhotoResponse], status_code=status.HTTP_201_CREATED)
async def upload_multiple_photos(
    id_match: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload plusieurs photos pour un match"""
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
    
    if errors and not uploaded_photos:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Aucune photo uploadée. Erreurs: {'; '.join(errors)}"
        )
    
    return uploaded_photos


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
