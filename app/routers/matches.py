from fastapi import APIRouter, Depends, HTTPException, status, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date, time, datetime
from app.database.connection import get_db
from app.database.models import Match, MatchResult
from app.schemas.match_schema import MatchCreate, MatchUpdate, MatchResponse, MatchWithDetails, MatchResultCreate, MatchResultUpdate, MatchResultResponse

router = APIRouter()


@router.get("/", response_model=List[MatchWithDetails])
def get_all_matches(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Récupérer tous les matches avec détails"""
    matches = db.query(Match).offset(skip).limit(limit).all()
    return matches


@router.get("/{id_match}", response_model=MatchWithDetails)
def get_match(id_match: int, db: Session = Depends(get_db)):
    """Récupérer un match par son ID"""
    match = db.query(Match).filter(Match.id_match == id_match).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match avec l'ID {id_match} non trouvé"
        )
    return match


@router.post("/", response_model=MatchResponse, status_code=status.HTTP_201_CREATED)
def create_match(match: MatchCreate, db: Session = Depends(get_db)):
    """Créer un nouveau match"""
    new_match = Match(**match.model_dump())
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    return new_match


@router.put("/{id_match}", response_model=MatchResponse)
def update_match(
    id_match: int,
    match_update: MatchUpdate,
    db: Session = Depends(get_db)
):
    """Mettre à jour un match"""
    match = db.query(Match).filter(Match.id_match == id_match).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match avec l'ID {id_match} non trouvé"
        )
    
    update_data = match_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(match, key, value)
    
    db.commit()
    db.refresh(match)
    return match


@router.delete("/{id_match}", status_code=status.HTTP_204_NO_CONTENT)
def delete_match(id_match: int, db: Session = Depends(get_db)):
    """Supprimer un match"""
    match = db.query(Match).filter(Match.id_match == id_match).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match avec l'ID {id_match} non trouvé"
        )
    
    db.delete(match)
    db.commit()
    return None


@router.get("/club/{id_club}", response_model=List[MatchResponse])
def get_matches_by_club(id_club: int, db: Session = Depends(get_db)):
    """Récupérer tous les matches d'un club (domicile ou extérieur)"""
    matches = db.query(Match).filter(
        (Match.id_club_home == id_club) | (Match.id_club_away == id_club)
    ).all()
    return matches


@router.get("/date/{match_date}", response_model=List[MatchResponse])
def get_matches_by_date(match_date: date, db: Session = Depends(get_db)):
    """Récupérer tous les matches d'une date"""
    matches = db.query(Match).filter(Match.date_match == match_date).all()
    return matches


# ========== ENDPOINTS POUR LES RÉSULTATS ==========

@router.post("/with-result", response_model=MatchWithDetails, status_code=status.HTTP_201_CREATED)
async def create_match_with_result(
    stade: Optional[str] = Form(None),
    date_match: date = Form(...),
    heure: time = Form(...),
    id_type_match: int = Form(...),
    id_club_home: int = Form(...),
    id_club_away: int = Form(...),
    score_club_1: Optional[int] = Form(None),
    score_club_2: Optional[int] = Form(None),
    db: Session = Depends(get_db)
):
    """Créer un match avec résultat (si la date est passée)"""
    try:
        # Créer le match
        new_match = Match(
            stade=stade,
            date_match=date_match,
            heure=heure,
            id_type_match=id_type_match,
            id_club_home=id_club_home,
            id_club_away=id_club_away
        )
        db.add(new_match)
        db.flush()  # Pour obtenir l'ID sans commit
        
        # Vérifier si la date est passée ou aujourd'hui et si des scores sont fournis
        match_datetime = datetime.combine(date_match, heure)
        if match_datetime.date() <= datetime.now().date() and score_club_1 is not None and score_club_2 is not None:
            # Ajouter le résultat
            result = MatchResult(
                id_match=new_match.id_match,
                score_club_1=score_club_1,
                score_club_2=score_club_2
            )
            db.add(result)
        
        db.commit()
        db.refresh(new_match)
        return new_match
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erreur lors de la création du match: {str(e)}"
        )


@router.post("/{id_match}/result", response_model=MatchResultResponse, status_code=status.HTTP_201_CREATED)
def add_match_result(
    id_match: int,
    result_data: MatchResultCreate,
    db: Session = Depends(get_db)
):
    """Ajouter un résultat à un match"""
    # Vérifier que le match existe
    match = db.query(Match).filter(Match.id_match == id_match).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match avec l'ID {id_match} non trouvé"
        )
    
    # Vérifier que le match est passé ou aujourd'hui
    if match.date_match > datetime.now().date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible d'ajouter un résultat pour un match à venir"
        )
    
    # Vérifier qu'un résultat n'existe pas déjà
    existing_result = db.query(MatchResult).filter(MatchResult.id_match == id_match).first()
    if existing_result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un résultat existe déjà pour ce match. Utilisez PUT pour le modifier."
        )
    
    # Créer le résultat
    new_result = MatchResult(
        id_match=id_match,
        score_club_1=result_data.score_club_1,
        score_club_2=result_data.score_club_2
    )
    db.add(new_result)
    db.commit()
    db.refresh(new_result)
    return new_result


@router.put("/{id_match}/result", response_model=MatchResultResponse)
def update_match_result(
    id_match: int,
    result_update: MatchResultUpdate,
    db: Session = Depends(get_db)
):
    """Modifier le résultat d'un match"""
    # Vérifier que le match existe
    match = db.query(Match).filter(Match.id_match == id_match).first()
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match avec l'ID {id_match} non trouvé"
        )
    
    # Vérifier que le match est passé ou aujourd'hui
    if match.date_match > datetime.now().date():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Impossible de modifier le résultat d'un match à venir"
        )
    
    # Récupérer le résultat existant
    result = db.query(MatchResult).filter(MatchResult.id_match == id_match).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun résultat trouvé pour ce match"
        )
    
    # Mettre à jour
    update_data = result_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(result, key, value)
    
    db.commit()
    db.refresh(result)
    return result

