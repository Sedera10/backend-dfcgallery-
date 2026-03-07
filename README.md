# DFC Gallery Backend API

API FastAPI pour la gestion de photos de matchs de football avec reconnaissance faciale automatique.

## 🚀 Fonctionnalités

- **Gestion des joueurs, clubs et matchs** : CRUD complet
- **Upload de photos** : Intégration Cloudinary
- **Reconnaissance faciale** : Détection et identification automatique des joueurs
- **OCR de maillots** : Détection des numéros de maillot
- **Traitement d'images** : Redimensionnement, compression, miniatures

## 📋 Prérequis

- Python 3.9+
- PostgreSQL avec extension pgvector
- Compte Cloudinary
- CMake et dlib (pour face_recognition)

## 🔧 Installation

### 1. Installer PostgreSQL et pgvector

```bash
# Installer PostgreSQL
# Puis installer pgvector
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install
```

### 2. Créer la base de données

```bash
psql -U postgres
CREATE DATABASE dfcgalery;
\c dfcgalery
CREATE EXTENSION vector;
```

### 3. Installer les dépendances Python

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Configuration

Copier `.env` et modifier les valeurs :

```bash
cp .env .env.local
# Éditer .env.local avec vos vraies valeurs
```

### 5. Créer les tables

```bash
# Les tables seront créées automatiquement au démarrage
# Ou exécuter le script SQL fourni :
psql -U postgres -d dfcgalery -f ../tables.sql
```

## 🏃 Lancement

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

L'API sera accessible sur : http://localhost:8000

Documentation interactive : http://localhost:8000/docs

## 📁 Structure du projet

```
backend/
├── app/
│   ├── main.py                 # Point d'entrée
│   ├── config/
│   │   └── settings.py         # Configuration
│   ├── database/
│   │   ├── connection.py       # Connexion DB
│   │   └── models.py           # Modèles SQLAlchemy
│   ├── schemas/
│   │   ├── joueur_schema.py    # Schémas Pydantic
│   │   ├── club_schema.py
│   │   ├── match_schema.py
│   │   ├── photo_schema.py
│   │   └── face_detection_schema.py
│   ├── routers/
│   │   ├── joueurs.py          # Endpoints joueurs
│   │   ├── clubs.py
│   │   ├── matches.py
│   │   └── photos.py
│   ├── services/
│   │   ├── cloudinary_service.py      # Upload images
│   │   ├── face_recognition_service.py # Reconnaissance faciale
│   │   └── jersey_ocr_service.py      # Détection numéros
│   └── utils/
│       └── image_utils.py      # Traitement d'images
├── requirements.txt
├── .env
└── README.md
```

## 🔌 Endpoints principaux

### Joueurs
- `GET /api/joueurs` - Liste tous les joueurs
- `GET /api/joueurs/{id}` - Détails d'un joueur
- `POST /api/joueurs` - Créer un joueur
- `PUT /api/joueurs/{id}` - Modifier un joueur
- `DELETE /api/joueurs/{id}` - Supprimer un joueur

### Clubs
- `GET /api/clubs` - Liste tous les clubs
- `GET /api/clubs/{id}` - Détails d'un club
- `POST /api/clubs` - Créer un club

### Matches
- `GET /api/matches` - Liste tous les matches
- `GET /api/matches/{id}` - Détails d'un match
- `POST /api/matches` - Créer un match

### Photos
- `GET /api/photos` - Liste toutes les photos
- `POST /api/photos/upload/{id_match}` - Upload une photo
- `POST /api/photos/{id_photo}/detect-faces` - Détecter les visages
- `DELETE /api/photos/{id}` - Supprimer une photo

## 🧪 Tests

```bash
pytest
```

## 📝 Notes

- La reconnaissance faciale nécessite l'enregistrement préalable des visages des joueurs
- L'OCR des maillots fonctionne mieux avec des images de bonne qualité
- Cloudinary gère automatiquement l'optimisation des images

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou une pull request.

## 📄 Licence

MIT
