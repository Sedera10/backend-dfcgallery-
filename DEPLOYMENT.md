# Guide d'hébergement DFC Gallery

## 📋 Prérequis
- Python 3.12+
- Base de données PostgreSQL
- Variables d'environnement configurées

## 🚀 Plateformes d'hébergement supportées

### 1. **Railway** (Recommandé) 
```bash
# 1. Connectez votre repo GitHub à Railway
# 2. Railway détecte automatiquement:
#    - requirements.txt 
#    - Procfile
#    - runtime.txt
# 3. Ajoutez les variables d'environnement dans le dashboard
# 4. Railway déploie automatiquement
```

### 2. **Heroku**
```bash
# Installation Heroku CLI puis :
git add .
git commit -m "Ready for deployment"
heroku create your-app-name
heroku addons:create heroku-postgresql:mini

# Variables d'environnement (voir .env.example)
heroku config:set DATABASE_URL="postgresql://..."
heroku config:set CLOUDINARY_CLOUD_NAME="..."
heroku config:set SECRET_KEY="your-secret-key"

git push heroku main
```

### 3. **Docker (VPS/Cloud)**
```bash
# Construction locale
docker build -t dfc-gallery .

# Avec Docker Compose
docker-compose up -d

# Pour production
docker-compose -f docker-compose.prod.yml up -d
```

### 4. **Render**
```bash
# 1. Connectez le repo 
# 2. Render détecte automatiquement Python
# 3. Commande de build: pip install -r requirements.txt
# 4. Commande de start: gunicorn -c gunicorn.conf.py app.main:app
```

## ⚙️ Variables d'environnement requises

Consultez `.env.example` pour la liste complète. Minimales :
```
DATABASE_URL=postgresql://user:pass@host:5432/db
SECRET_KEY=your-super-secret-key
CLOUDINARY_CLOUD_NAME=your-cloud
CLOUDINARY_API_KEY=your-key  
CLOUDINARY_API_SECRET=your-secret
```

## 🔧 Configuration des services

### Base de données
- **Développement** : PostgreSQL local ou Docker
- **Production** : Service cloud (Railway PostgreSQL, Heroku PostgreSQL, etc.)
- Extensions requises : `pgvector` (pour la recherche de similarité d'images)

### Upload d'images  
- **Cloudinary** : Service principal recommandé
- **ImgBB** : Alternative/backup

### Face Recognition (Optionnel)
⚠️ **Attention** : `dlib` et `face-recognition` nécessitent :
- Build tools (Windows: Visual Studio Build Tools)  
- RAM importante (>1GB)
- Temps d'installation long

Pour désactiver :
```python
# Commentez dans requirements.txt :
# face-recognition==1.3.0
# dlib==19.24.2
```

## 🛠️ Troubleshooting

### Erreur build `dlib`
```bash
# Sur Windows
pip install cmake
pip install dlib

# Sur Linux (Dockerfile gère ça automatiquement)
apt-get install build-essential cmake
```

### Timeout d'installation
```bash
# Augmentez le timeout
pip install --timeout 1000 -r requirements.txt
```

### Variables d'environnement
```bash
# Vérifiez que toutes les variables sont définies
python -c "import os; print([k for k in os.environ.keys() if 'DATABASE' in k or 'CLOUDINARY' in k])"
```

## 📊 Monitoring

### Health Check
- Endpoint : `GET /health`
- Docker health check intégré
- Compatible Kubernetes liveness/readiness probes

### Logs
```bash
# Voir les logs (Docker)
docker logs dfc_backend -f

# Voir les logs (Railway/Heroku)  
# Via le dashboard web
```