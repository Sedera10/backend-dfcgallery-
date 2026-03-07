from pydantic import BaseModel
from typing import Optional, List


class FaceDetectionBase(BaseModel):
    id_photo: Optional[int] = None
    id_joueur: Optional[int] = None


class FaceDetectionCreate(FaceDetectionBase):
    encoding: Optional[List[float]] = None


class FaceDetectionUpdate(BaseModel):
    id_photo: Optional[int] = None
    id_joueur: Optional[int] = None


class FaceDetectionResponse(FaceDetectionBase):
    id_face: int
    
    class Config:
        from_attributes = True


class FaceDetectionWithDetails(FaceDetectionResponse):
    joueur: Optional["JoueurResponse"] = None
    photo: Optional["PhotoResponse"] = None
    
    class Config:
        from_attributes = True


# Éviter l'import circulaire
from app.schemas.joueur_schema import JoueurResponse
from app.schemas.photo_schema import PhotoResponse
FaceDetectionWithDetails.model_rebuild()
