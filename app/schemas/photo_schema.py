from pydantic import BaseModel
from typing import Optional, List


class PhotoBase(BaseModel):
    url: str
    id_match: int


class PhotoCreate(PhotoBase):
    pass


class PhotoUpdate(BaseModel):
    url: Optional[str] = None
    id_match: Optional[int] = None


class PhotoResponse(PhotoBase):
    id_photo: int
    
    class Config:
        from_attributes = True


class PhotoWithFaces(PhotoResponse):
    face_detections: Optional[List["FaceDetectionResponse"]] = None
    
    class Config:
        from_attributes = True


# Éviter l'import circulaire
from app.schemas.face_detection_schema import FaceDetectionResponse
PhotoWithFaces.model_rebuild()
