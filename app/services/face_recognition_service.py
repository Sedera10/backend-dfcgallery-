"""
Service de reconnaissance faciale optimisé.
Les encodages sont calculés UNE SEULE FOIS à l'upload et stockés en base.
La recherche compare simplement les vecteurs stockés (très rapide).
"""
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False

import numpy as np
from typing import List, Optional
from sqlalchemy.orm import Session
from io import BytesIO
from PIL import Image
import requests
import logging

from app.database.models import Joueur, FaceDetection, Photo, JerseyDetection
from app.config.settings import settings

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Service optimisé : encode à l'upload, compare en mémoire."""

    def __init__(self):
        if not FACE_RECOGNITION_AVAILABLE:
            logger.warning("face_recognition non disponible.")

    # ── Utilitaire ──

    def _download_image(self, url: str) -> np.ndarray:
        """Télécharge et retourne un numpy array RGB."""
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        return np.array(img)

    # ── Encodage des photos de match (appelé en background) ──

    def encode_faces_in_photo(self, photo_id: int, image_url: str, db: Session) -> int:
        """
        Détecte et stocke les encodages faciaux d'une photo de match.
        Returns: nombre de visages détectés.
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return 0
        try:
            image_array = self._download_image(image_url)
            face_locations = face_recognition.face_locations(image_array, model="hog")
            if not face_locations:
                return 0
            face_encodings = face_recognition.face_encodings(image_array, face_locations)

            count = 0
            for encoding in face_encodings:
                db.add(FaceDetection(
                    id_photo=photo_id,
                    id_joueur=None,
                    encoding=encoding.tolist()
                ))
                count += 1

            db.commit()
            logger.info("Photo %s : %d visages encodés", photo_id, count)

            # Auto-match avec joueurs connus
            self.auto_match_faces_in_photo(photo_id, db)

            return count
        except Exception as e:
            db.rollback()
            logger.error("Erreur encoding photo %s : %s", photo_id, str(e))
            return 0

    # ── Encodage de la photo de profil d'un joueur ──

    def encode_player_face(self, joueur_id: int, image_url: str, db: Session) -> bool:
        """
        Encode le visage du joueur depuis sa pdp.
        Stocke dans face_detection avec id_joueur set, id_photo NULL.
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return False
        try:
            image_array = self._download_image(image_url)
            face_locations = face_recognition.face_locations(image_array, model="hog")
            if not face_locations:
                logger.warning("Aucun visage détecté pour joueur %s", joueur_id)
                return False

            # Prendre le plus grand visage
            if len(face_locations) > 1:
                areas = [(b - t) * (r - l) for (t, r, b, l) in face_locations]
                best_idx = int(np.argmax(areas))
                face_locations = [face_locations[best_idx]]

            encoding = face_recognition.face_encodings(image_array, face_locations)[0]

            # Supprimer l'ancien encoding de référence
            db.query(FaceDetection).filter(
                FaceDetection.id_joueur == joueur_id,
                FaceDetection.id_photo.is_(None)
            ).delete()

            db.add(FaceDetection(
                id_photo=None,
                id_joueur=joueur_id,
                encoding=encoding.tolist()
            ))
            db.commit()
            logger.info("Joueur %s : visage encodé", joueur_id)
            return True
        except Exception as e:
            db.rollback()
            logger.error("Erreur encoding joueur %s : %s", joueur_id, str(e))
            return False

    # ── Trouver les photos d'un joueur (la recherche rapide) ──

    def find_player_photos(self, joueur_id: int, db: Session, tolerance: float = None) -> List[int]:
        """
        Compare l'encoding du joueur contre tous les encodings de photos,
        ET cherche les photos contenant son numéro de maillot (OCR).
        Returns: liste d'id_photo (meilleurs matchs d'abord, puis jersey matches).
        """
        if tolerance is None:
            tolerance = settings.FACE_RECOGNITION_TOLERANCE

        result_ids = []

        # ── 1. Recherche par visage ──
        if FACE_RECOGNITION_AVAILABLE:
            # Encoding de référence du joueur
            player_ref = db.query(FaceDetection).filter(
                FaceDetection.id_joueur == joueur_id,
                FaceDetection.id_photo.is_(None)
            ).first()

            if player_ref and player_ref.encoding:
                player_encoding = np.array(player_ref.encoding)

                # Tous les encodings de photos
                photo_detections = db.query(FaceDetection).filter(
                    FaceDetection.id_photo.isnot(None),
                    FaceDetection.encoding.isnot(None)
                ).all()

                if photo_detections:
                    all_encodings = np.array([d.encoding for d in photo_detections])
                    distances = face_recognition.face_distance(all_encodings, player_encoding)

                    matches = []
                    for i, dist in enumerate(distances):
                        if dist < tolerance:
                            matches.append((photo_detections[i].id_photo, float(dist)))

                    matches.sort(key=lambda x: x[1])
                    seen = set()
                    for pid, _ in matches:
                        if pid not in seen:
                            seen.add(pid)
                            result_ids.append(pid)

        # ── 2. Recherche par numéro de maillot (OCR) ──
        joueur = db.query(Joueur).filter(Joueur.id_joueur == joueur_id).first()
        if joueur and joueur.numero:
            jersey_detections = db.query(JerseyDetection).filter(
                JerseyDetection.number_detected == joueur.numero,
                JerseyDetection.confidence >= 0.5
            ).all()
            
            existing_ids = set(result_ids)
            for det in jersey_detections:
                if det.id_photo not in existing_ids:
                    result_ids.append(det.id_photo)
                    existing_ids.add(det.id_photo)
                    logger.info("Photo %s ajoutée par jersey OCR (numéro %d)", det.id_photo, joueur.numero)

        return result_ids

    # ── Auto-match des visages d'une photo ──

    def auto_match_faces_in_photo(self, photo_id: int, db: Session, tolerance: float = None) -> int:
        """Match les visages non identifiés d'une photo avec les joueurs connus."""
        if not FACE_RECOGNITION_AVAILABLE:
            return 0
        if tolerance is None:
            tolerance = settings.FACE_RECOGNITION_TOLERANCE

        unmatched = db.query(FaceDetection).filter(
            FaceDetection.id_photo == photo_id,
            FaceDetection.id_joueur.is_(None)
        ).all()
        if not unmatched:
            return 0

        player_refs = db.query(FaceDetection).filter(
            FaceDetection.id_joueur.isnot(None),
            FaceDetection.id_photo.is_(None)
        ).all()
        if not player_refs:
            return 0

        player_encodings = np.array([p.encoding for p in player_refs])
        player_ids = [p.id_joueur for p in player_refs]

        matched = 0
        for det in unmatched:
            if not det.encoding:
                continue
            distances = face_recognition.face_distance(player_encodings, np.array(det.encoding))
            min_idx = int(np.argmin(distances))
            if distances[min_idx] < tolerance:
                det.id_joueur = player_ids[min_idx]
                matched += 1

        if matched:
            db.commit()
            logger.info("Photo %s : %d visages matchés", photo_id, matched)
        return matched
