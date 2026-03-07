#!/usr/bin/env python3
"""
Script pour basculer entre les versions de requirements.txt
Usage:
  python deploy-mode.py minimal     # Version Render ultra-basic (API seulement)
  python deploy-mode.py production  # Version avec images (nécessite plan payant)
  python deploy-mode.py full        # Version complète avec ML
"""

import sys
import shutil
from pathlib import Path

def switch_requirements(mode):
    """Bascule entre les versions de requirements"""
    base_path = Path(__file__).parent
    
    if mode == "minimal":
        # Version ultra-basique pour Render (gratuit)
        src = base_path / "requirements-minimal.txt"
        if src.exists():
            shutil.copy(src, base_path / "requirements.txt")
            print("✅ Mode MINIMAL activé (API seulement)")
            print("📦 Dépendances: FastAPI, DB, Auth seulement")
            print("⚠️  Images désactivées temporairement")
        else:
            print("❌ Fichier requirements-minimal.txt manquant")
            return False
            
    elif mode == "production":
        # Version avec traitement d'images
        src = base_path / "requirements-with-images-backup.txt"
        if src.exists():
            shutil.copy(src, base_path / "requirements.txt")
            print("✅ Mode PRODUCTION activé (avec traitement d'images)")
            print("📦 Dépendances: FastAPI, DB, Cloudinary, Pillow")
            print("💰 Nécessite plan payant Render")
        else:
            print("❌ Fichier requirements-with-images-backup.txt manquant")
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
        print("❌ Mode invalide. Utilisez: 'minimal', 'production' ou 'full'")
        return False
        
    return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python deploy-mode.py [minimal|production|full]")
        print()
        print("Modes disponibles:")
        print("  minimal    - API basique (gratuit Render)")
        print("  production - Avec images (plan payant)")  
        print("  full       - Toutes features ML (développement)")
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