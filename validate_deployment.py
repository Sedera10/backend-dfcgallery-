#!/usr/bin/env python3
"""
Script de validation pour l'hébergement DFC Gallery
Vérifie que tous les fichiers et configurations nécessaires sont présents
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """Vérifie qu'un fichier existe"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} - MANQUANT")
        return False

def check_requirements():
    """Vérifie que requirements.txt contient les dépendances essentielles"""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt manquant")
        return False
    
    content = req_file.read_text()
    essential_deps = [
        "fastapi", "uvicorn", "sqlalchemy", "psycopg2-binary", 
        "pydantic", "gunicorn", "requests", "httpx"
    ]
    
    missing = [dep for dep in essential_deps if dep not in content.lower()]
    
    if missing:
        print(f"❌ Dépendances manquantes dans requirements.txt: {', '.join(missing)}")
        return False
    else:
        print("✅ requirements.txt contient les dépendances essentielles")
        return True

def check_env_example():
    """Vérifie .env.example"""
    env_file = Path(".env.example")
    if not env_file.exists():
        print("❌ .env.example manquant")
        return False
    
    content = env_file.read_text()
    required_vars = [
        "DATABASE_URL", "SECRET_KEY", "CLOUDINARY_CLOUD_NAME", 
        "CLOUDINARY_API_KEY", "CLOUDINARY_API_SECRET"
    ]
    
    missing = [var for var in required_vars if var not in content]
    
    if missing:
        print(f"❌ Variables manquantes dans .env.example: {', '.join(missing)}")
        return False
    else:
        print("✅ .env.example contient les variables essentielles")
        return True

def main():
    print("🔍 Validation de la configuration d'hébergement DFC Gallery")
    print("=" * 60)
    
    all_good = True
    
    # Fichiers essentiels pour l'hébergement
    files_to_check = [
        ("requirements.txt", "Dépendances Python"),
        ("Procfile", "Configuration Heroku/Railway"),
        ("runtime.txt", "Version Python"),
        ("gunicorn.conf.py", "Configuration serveur production"),
        ("Dockerfile", "Image Docker"),
        (".dockerignore", "Exclusions Docker"),
        ("docker-compose.yml", "Orchestration Docker"),
        (".env.example", "Template variables d'environnement"),
        ("DEPLOYMENT.md", "Guide d'hébergement"),
        ("app/main.py", "Application principale")
    ]
    
    print("\n📁 Vérification des fichiers:")
    for filepath, description in files_to_check:
        if not check_file_exists(filepath, description):
            all_good = False
    
    print("\n📦 Vérification des dépendances:")
    if not check_requirements():
        all_good = False
    
    print("\n🔧 Vérification de la configuration:")
    if not check_env_example():
        all_good = False
    
    # Vérifications additionnelles
    print("\n🏥 Endpoint de health check:")
    main_py = Path("app/main.py")
    if main_py.exists():
        content = main_py.read_text()
        if "/health" in content:
            print("✅ Endpoint /health présent")
        else:
            print("❌ Endpoint /health manquant - ajoutez pour le monitoring")
            all_good = False
    
    print("\n" + "=" * 60)
    if all_good:
        print("🎉 SUCCÈS: Votre application est prête pour l'hébergement!")
        print("📖 Consultez DEPLOYMENT.md pour les instructions détaillées")
        sys.exit(0)
    else:
        print("⚠️  ATTENTION: Des éléments sont manquants pour l'hébergement")
        print("🔧 Corrigez les problèmes ci-dessus avant de déployer")
        sys.exit(1)

if __name__ == "__main__":
    main()