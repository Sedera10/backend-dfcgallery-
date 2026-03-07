from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator
import os
from pathlib import Path

# Chemin absolu vers le dossier backend
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/dfcgalery"
    
    # Cloudinary (optional, kept for backward compatibility)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    # ImgBB
    IMGBB_API_KEY: str
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:5173", "http://192.168.137.1:5173"]
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def split_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v
    
    # File Upload (limite ImgBB: 32 MB)
    MAX_FILE_SIZE: int = 32 * 1024 * 1024  # 32 MB
    ALLOWED_EXTENSIONS: Union[List[str], str] = [".jpg", ".jpeg", ".png", ".webp"]
    
    @field_validator('ALLOWED_EXTENSIONS', mode='before')
    @classmethod
    def split_extensions(cls, v):
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(',')]
        return v
    
    # Face Recognition
    FACE_DETECTION_THRESHOLD: float = 0.6
    FACE_RECOGNITION_TOLERANCE: float = 0.45  # Plus strict pour éviter les faux positifs (défaut face_recognition: 0.6)
    
    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = True


settings = Settings()
