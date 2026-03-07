#!/usr/bin/env python3
"""
Script pour basculer entre les versions de requirements.txt
Usage:
  python deploy-mode.py production  # Version Render (sans ML)
  python deploy-mode.py full       # Version complète (avec ML)
"""

import sys
import shutil
from pathlib import Path

def switch_requirements(mode):
    """Bascule entre les versions de requirements"""
    base_path = Path(__file__).parent
    
    if mode == "production":
        # Version simplifiée pour Render
        src = base_path / "requirements-render.txt"
        if src.exists():
            shutil.copy(src, base_path / "requirements.txt")
            print("✅ Mode PRODUCTION activé (sans Face Recognition/OCR)")
            print("📦 Dépendances: FastAPI, DB, Cloudinary seulement")
        else:
            print("❌ Fichier requirements-render.txt manquant")
            return False
            
    elif mode == "full":
        # Version complète avec ML
        src = base_path / "requirements-full-backup.txt"
        if src.exists():
            shutil.copy(src, base_path / "requirements.txt")
            print("✅ Mode COMPLET activé (avec Face Recognition/OCR)")
            print("📦 Dépendances: Toutes les features activées")
        else:
            print("❌ Fichier requirements-full-backup.txt manquant")
            return False
    else:
        print("❌ Mode invalide. Utilisez: 'production' ou 'full'")
        return False
        
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python deploy-mode.py [production|full]")
        sys.exit(1)
        
    mode = sys.argv[1]
    if switch_requirements(mode):
        print(f"\n🚀 Prêt pour: {mode}")
        if mode == "production":
            print("💡 Push sur GitHub pour déclencher le redéploiement Render")
        else:
            print("💡 Testez en local avec: pip install -r requirements.txt")
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()