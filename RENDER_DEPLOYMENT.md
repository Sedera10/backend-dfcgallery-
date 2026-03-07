# 🚀 Guide de déploiement Render - DFC Gallery

## Étapes de déploiement sur Render

### 1. **Préparer le repository (VERSION SIMPLIFIÉE d'abord)**

```bash
# IMPORTANT: Utiliser d'abord la version simplifiée pour éviter les erreurs de build
python deploy-mode.py production

# Puis commiter et pusher
git add .
git commit -m "Deploy to Render - production mode (without ML)"
git push origin main
```

**🔧 Pourquoi en 2 étapes ?**
- Face Recognition/OCR causent des erreurs de build sur Render
- On déploie d'abord les fonctions essentielles (upload, gallery, etc.)
- Les features ML peuvent être ajoutées plus tard avec un plan payant

### 2. **Créer les services sur Render**

#### A. Base de données PostgreSQL
1. Allez sur [render.com](https://render.com) et connectez-vous
2. Cliquez **"New +"** → **"PostgreSQL"**
3. Configurez :
   - **Name**: `dfc-galery-db`
   - **Database**: `dfcgalery` 
   - **User**: `disciplesfc`
   - **Region**: Europe (Frankfurt)
   - **Plan**: Free (0$/mois)

#### B. Application Web
1. Cliquez **"New +"** → **"Web Service"**
2. Connectez votre repository GitHub
3. Configurez :
   - **Name**: `dfc-galery-api`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -c gunicorn.conf.py app.main:app`
   - **Plan**: Free (0$/mois)

### 3. **Variables d'environnement**

Dans le dashboard de votre Web Service, section **"Environment"**, ajoutez :

```bash
# Base de données (copiez l'URL interne depuis votre DB PostgreSQL)
DATABASE_URL=postgresql://disciplesfc:xxxxx@dpg-xxxxx-a.frankfurt-postgres.render.com/dfcgalery

# Cloudinary (vos vraies valeurs)
CLOUDINARY_CLOUD_NAME=dpyiqh6ll
CLOUDINARY_API_KEY=336363364894945
CLOUDINARY_API_SECRET=SNQVL9oO5-bERaxyqnZ89Q1HJY8

# ImgBB
IMGBB_API_KEY=153bb05b27d2a274541c771646e0061a

# Sécurité (générez une clé forte)
SECRET_KEY=dfcgalery-super-secret-key-production-2026
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Configuration app
DEBUG=false
CORS_ORIGINS=["https://disciplesfc.com","https://your-frontend-url.onrender.com"]
ALLOWED_HOSTS=["*"]

# Optimisations
WEB_CONCURRENCY=2
MAX_FILE_SIZE=33554432
ALLOWED_EXTENSIONS=.jpg,.jpeg,.png,.webp
```

### 4. **Obtenir DATABASE_URL**

1. Dans votre service PostgreSQL sur Render
2. Allez dans **"Info"** 
3. Copiez l'**"Internal Database URL"** 
4. Collez-la comme `DATABASE_URL` dans votre Web Service

### 5. **Déploiement**

1. **Auto-deploy** : Render redéploie automatiquement à chaque `git push`
2. **Manuel** : Cliquez **"Deploy latest commit"** dans le dashboard
3. **Logs** : Suivez les logs de build et runtime en temps réel

### 6. **Configuration du domaine personnalisé** (Optionnel)

1. Dans votre Web Service, section **"Settings"**
2. **"Custom Domains"** 
3. Ajoutez `api.disciplesfc.com` ou votre domaine
4. Configurez le CNAME chez votre registrar

## 🔧 URLs finales

- **API Backend** : `https://dfc-galery-api.onrender.com`
- **Health Check** : `https://dfc-galery-api.onrender.com/health`
- **Documentation** : `https://dfc-galery-api.onrender.com/docs`
- **Base de données** : Accessible uniquement depuis Render

## ⚡ Optimisations Render

### Performance
- **Keep-alive**: Les apps gratuites "dorment" après 15min d'inactivité
- **Cold start**: Premier démarrage peut prendre 30-60 secondes  
- **Solution**: Ping périodique ou upgrade vers plan payant

### Monitoring
```bash
# Health check automatique
curl https://dfc-galery-api.onrender.com/health

# Vérifier les logs
# Via le dashboard Render directement
```

### Scaling (Plans payants)
- **Starter ($7/mois)** : Pas de sleep, SSL gratuit
- **Standard ($25/mois)** : Scaling horizontal
- **Pro ($85/mois)** : Resources dédiées

## 🛠️ Troubleshooting

### Build échoue
```bash
# Vérifiez que requirements.txt est à jour
pip freeze > requirements.txt

# Test local de build
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

### Application ne démarre pas
```bash
# Vérifiez les logs Render
# Variables d'environnement manquantes ?
# DATABASE_URL accessible ?
```

### 500 Internal Server Error  
```bash
# Souvent : problème de DATABASE_URL ou clés API invalides
# Vérifiez les variables d'environnement dans le dashboard
```

## 🎉 Test final

Une fois déployé, testez :

1. **Health check** : `GET https://dfc-galery-api.onrender.com/health`
2. **Documentation** : `https://dfc-galery-api.onrender.com/docs`
3. **Upload d'image** : Test via l'interface Swagger

## 🤖 Réactiver Face Recognition & OCR (Plus tard)

### Étape 1: Upgrade vers plan payant
- **Starter Plan** ($7/mois) pour éviter les timeouts de build
- Plus de RAM et temps de build pour compiler `dlib`

### Étape 2: Activer les features ML
```bash
# En local
python deploy-mode.py full
git add requirements.txt
git commit -m "Activate ML features"
git push origin main
```

### Étape 3: Variables d'environnement ML
Ajoutez dans Render :
```bash
FACE_RECOGNITION_ENABLED=true
OCR_ENABLED=true
FACE_RECOGNITION_TOLERANCE=0.6
OCR_LANGUAGES=["fr","en"]
```

> 💡 **Astuce** : Votre app fonctionne déjà sans ML. Les features sont optionnelles !