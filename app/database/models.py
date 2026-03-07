from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey, Text, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from app.database.connection import Base


class Championnat(Base):
    __tablename__ = "championnat"
    
    id_championnat = Column(Integer, primary_key=True, index=True)
    libelle = Column(String(100), nullable=False)
    ligue = Column(String(100))
    
    # Relations
    clubs = relationship("Club", back_populates="championnat")


class TypeMatch(Base):
    __tablename__ = "type_match"
    
    id_type_match = Column(Integer, primary_key=True, index=True)
    libelle = Column(String(50), nullable=False)
    
    # Relations
    matches = relationship("Match", back_populates="type_match")


class Club(Base):
    __tablename__ = "club"
    
    id_club = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100))
    region = Column(String(100), nullable=False)
    logo = Column(String(255))
    id_championnat = Column(Integer, ForeignKey("championnat.id_championnat"), nullable=False)
    
    # Relations
    championnat = relationship("Championnat", back_populates="clubs")
    joueurs = relationship("Joueur", back_populates="club")
    matches_home = relationship("Match", foreign_keys="Match.id_club_home", back_populates="club_home")
    matches_away = relationship("Match", foreign_keys="Match.id_club_away", back_populates="club_away")


class Joueur(Base):
    __tablename__ = "joueur"
    
    id_joueur = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    dt_naissance = Column(Date)
    pdp = Column(String(255))  # photo de profil
    id_club = Column(Integer, ForeignKey("club.id_club"), nullable=False)
    poste = Column(String(50), nullable=False)
    numero = Column(Integer)
    
    # Relations
    club = relationship("Club", back_populates="joueurs")
    face_detections = relationship("FaceDetection", back_populates="joueur")


class Match(Base):
    __tablename__ = "match_"
    
    id_match = Column(Integer, primary_key=True, index=True)
    stade = Column(String(100))
    date_match = Column(Date, nullable=False)
    heure = Column(Time, nullable=False)
    id_type_match = Column(Integer, ForeignKey("type_match.id_type_match"), nullable=False)
    id_club_home = Column(Integer, ForeignKey("club.id_club"), nullable=False)
    id_club_away = Column(Integer, ForeignKey("club.id_club"), nullable=False)
    
    # Relations
    type_match = relationship("TypeMatch", back_populates="matches")
    club_home = relationship("Club", foreign_keys=[id_club_home], back_populates="matches_home")
    club_away = relationship("Club", foreign_keys=[id_club_away], back_populates="matches_away")
    result = relationship("MatchResult", back_populates="match", uselist=False)
    photos = relationship("Photo", back_populates="match")


class MatchResult(Base):
    __tablename__ = "match_result"
    
    id_result = Column(Integer, primary_key=True, index=True)
    id_match = Column(Integer, ForeignKey("match_.id_match"), nullable=False)
    score_club_1 = Column(Integer, nullable=False, default=0)
    score_club_2 = Column(Integer, nullable=False, default=0)
    date_enregistrement = Column(DateTime, server_default=func.now())
    
    # Relations
    match = relationship("Match", back_populates="result")


class Photo(Base):
    __tablename__ = "photo"
    
    id_photo = Column(Integer, primary_key=True, index=True)
    url = Column(String(255), nullable=False)
    id_match = Column(Integer, ForeignKey("match_.id_match"), nullable=False)
    
    # Relations
    match = relationship("Match", back_populates="photos")
    face_detections = relationship("FaceDetection", back_populates="photo")
    jersey_detections = relationship("JerseyDetection", back_populates="photo", cascade="all, delete-orphan")


class FaceDetection(Base):
    __tablename__ = "face_detection"
    
    id_face = Column(Integer, primary_key=True, index=True)
    id_photo = Column(Integer, ForeignKey("photo.id_photo"))
    id_joueur = Column(Integer, ForeignKey("joueur.id_joueur"))
    encoding = Column(ARRAY(Float), nullable=False)  # FLOAT8[] en PostgreSQL
    
    # Relations
    photo = relationship("Photo", back_populates="face_detections")
    joueur = relationship("Joueur", back_populates="face_detections")


class JerseyDetection(Base):
    __tablename__ = "jersey_detection"
    
    id_jersey = Column(Integer, primary_key=True, index=True)
    id_photo = Column(Integer, ForeignKey("photo.id_photo", ondelete="CASCADE"), nullable=False)
    number_detected = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False, default=0.0)
    
    # Relations
    photo = relationship("Photo", back_populates="jersey_detections")
