# 🪟 Installation sur Windows

## Problème avec dlib et face_recognition

Sur Windows, `dlib` nécessite une compilation C++ qui peut échouer. Voici les solutions :

## ✅ Solution 1 : Installation avec wheel pré-compilée (RECOMMANDÉ)

### Étape 1 : Installer les dépendances de base
```bash
pip install -r requirements.txt
```

### Étape 2 : Installer dlib depuis une wheel
```bash
# Télécharger la wheel depuis : https://github.com/z-mahmud22/Dlib_Windows_Python3.x
# Ou utiliser :
pip install https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.1-cp312-cp312-win_amd64.whl
```

### Étape 3 : Installer face-recognition
```bash
pip install face-recognition
```

### Étape 4 : Installer EasyOCR (optionnel)
```bash
pip install easyocr
```

---

## ✅ Solution 2 : Augmenter le timeout

```bash
pip install --default-timeout=200 --retries 5 -r requirements-full.txt
```

---

## ✅ Solution 3 : Installer Visual Studio Build Tools

1. **Télécharger Build Tools** : https://visualstudio.microsoft.com/visual-cpp-build-tools/

2. **Installer avec :**
   - ✅ Desktop development with C++
   - ✅ MSVC v143
   - ✅ Windows 10 SDK

3. **Installer CMake** :
   ```bash
   pip install cmake
   ```

4. **Installer dlib** :
   ```bash
   pip install dlib
   pip install face-recognition
   ```

---

## ✅ Solution 4 : Démarrer sans reconnaissance faciale

Pour démarrer rapidement le projet :

1. **Installer les dépendances de base** :
   ```bash
   pip install -r requirements.txt
   ```

2. **L'API fonctionnera** mais sans :
   - ❌ Reconnaissance faciale automatique
   - ❌ Détection OCR des maillots
   - ✅ Upload de photos ✓
   - ✅ CRUD complet ✓
   - ✅ Gestion clubs/joueurs/matches ✓

3. **Ajouter la reconnaissance plus tard** quand dlib est installé

---

## 🔧 Vérifier l'installation

```bash
python -c "import face_recognition; print('Face recognition OK')"
python -c "import easyocr; print('EasyOCR OK')"
```

---

## 📦 Packages par ordre de priorité

### Essentiels (requirements.txt)
```bash
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic cloudinary pillow requests
```

### Optionnels (quand réseau stable)
```bash
pip install opencv-python numpy face-recognition dlib easyocr
```

---

## 🆘 Si rien ne fonctionne

Utilisez **Conda** au lieu de pip :

```bash
conda create -n dfcgalery python=3.10
conda activate dfcgalery
conda install -c conda-forge dlib
pip install -r requirements.txt
```
