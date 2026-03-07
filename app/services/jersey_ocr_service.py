"""
Service de détection de numéros de maillot via OCR.
Fonctionne en synchrone pour être appelé en background tasks comme face_recognition.
"""
try:
    import easyocr
    import cv2
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

import numpy as np
from typing import List, Dict, Optional
from PIL import Image
from io import BytesIO
import requests
import logging

from sqlalchemy.orm import Session
from app.database.models import JerseyDetection, Photo, Joueur

logger = logging.getLogger(__name__)

# Singleton pour éviter de recharger le modèle à chaque appel
_reader = None


def _get_reader():
    global _reader
    if _reader is None and EASYOCR_AVAILABLE:
        logger.info("Initialisation du lecteur OCR easyocr...")
        _reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _reader


class JerseyOCRService:
    """Détecte les numéros de maillot dans les photos et les stocke en base."""

    def _download_image(self, url: str) -> np.ndarray:
        """Télécharge et retourne un numpy array BGR (format OpenCV)."""
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    def _preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Prétraite l'image pour améliorer la détection OCR."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        # Améliorer le contraste avec CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        return enhanced

    def detect_jersey_numbers(self, image_url: str) -> List[Dict]:
        """
        Détecte tous les numéros de maillot (1-99) dans une image.
        Returns: [{"number": int, "confidence": float}, ...]
        """
        if not EASYOCR_AVAILABLE:
            return []

        reader = _get_reader()
        if not reader:
            return []

        try:
            image = self._download_image(image_url)
            processed = self._preprocess_image(image)

            results = reader.readtext(processed)

            jersey_numbers = []
            seen_numbers = set()
            for (_, text, confidence) in results:
                cleaned = ''.join(filter(str.isdigit, text))
                if cleaned and len(cleaned) <= 2 and confidence > 0.4:
                    number = int(cleaned)
                    if 1 <= number <= 99 and number not in seen_numbers:
                        seen_numbers.add(number)
                        jersey_numbers.append({
                            "number": number,
                            "confidence": float(confidence)
                        })

            return jersey_numbers

        except Exception as e:
            logger.error("Erreur OCR sur %s: %s", image_url, str(e))
            return []

    def detect_and_store(self, photo_id: int, image_url: str, db: Session) -> int:
        """
        Détecte les numéros dans une photo et les stocke en base.
        Returns: nombre de numéros détectés.
        """
        try:
            # Vérifier si déjà traité
            existing = db.query(JerseyDetection).filter(
                JerseyDetection.id_photo == photo_id
            ).first()
            if existing:
                return 0

            numbers = self.detect_jersey_numbers(image_url)

            for n in numbers:
                db.add(JerseyDetection(
                    id_photo=photo_id,
                    number_detected=n["number"],
                    confidence=n["confidence"]
                ))

            if numbers:
                db.commit()
                logger.info("Photo %s: %d numéros de maillot détectés: %s",
                            photo_id, len(numbers),
                            [n["number"] for n in numbers])
            return len(numbers)

        except Exception as e:
            db.rollback()
            logger.error("Erreur stockage OCR photo %s: %s", photo_id, str(e))
            return 0

    def find_photos_by_jersey(self, joueur_id: int, db: Session) -> List[int]:
        """
        Trouve les photos contenant le numéro de maillot d'un joueur.
        Returns: liste de photo IDs.
        """
        joueur = db.query(Joueur).filter(Joueur.id_joueur == joueur_id).first()
        if not joueur or not joueur.numero:
            return []

        detections = db.query(JerseyDetection).filter(
            JerseyDetection.number_detected == joueur.numero,
            JerseyDetection.confidence >= 0.5
        ).all()

        return list(set(d.id_photo for d in detections))
