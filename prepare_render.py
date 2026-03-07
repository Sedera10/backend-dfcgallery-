#!/usr/bin/env python3
"""
Script de préparation pour le déploiement Render
Vérifie la configuration et génère le résumé des étapes
"""

import os
import sys
from pathlib import Path

def check_render_readiness():
    """Vérifie que l'app est prête pour Render"""
    print("🔍 Vérification configuration Render")
    print("=" * 50)
    
    errors = []
    warnings = []
    
    # Fichiers essentiels Render
    required_files = {
        "requirements.txt": "Dépendances Python",
        "gunicorn.conf.py": "Configuration serveur",
        "app/main.py": "Application FastAPI",
        "render.yaml": "Configuration Render (optionnel)",
        "RENDER_DEPLOYMENT.md": "Guide déploiement",
        ".env.render": "Variables d'environnement pour Render"
    }
    
    for file, desc in required_files.items():
        if Path(file).exists():
            print(f"✅ {desc}: {file}")
        else:
            print(f"❌ {desc}: {file}")
            errors.append(file)
    
    # Vérifier que les clés ne sont pas dans .env.example
    env_example = Path(".env.example") 
    if env_example.exists():
        content = env_example.read_text()
        if "dpyiqh6ll" in content or "dfcgalerykey" in content:
            warnings.append("🔒 Clés API réelles détectées dans .env.example")
        else:
            print("✅ .env.example sécurisé")
    
    # Vérifier gitignore
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env.render" in content:
            print("✅ .env.render dans .gitignore")
        else:
            warnings.append("⚠️ Ajoutez .env.render au .gitignore")
    
    return errors, warnings

def display_render_steps():
    """Affiche les étapes de déploiement Render"""
    print("\n🚀 Étapes de déploiement Render:")
    print("=" * 50)
    
    steps = [
        "1. Commitez votre code: git add . && git commit && git push",
        "2. Créez un service PostgreSQL sur render.com",
        "3. Créez un Web Service Python sur render.com", 
        "4. Configurez Build Command: pip install -r requirements.txt",
        "5. Configurez Start Command: gunicorn -c gunicorn.conf.py app.main:app",
        "6. Copiez les variables d'environnement depuis .env.render",
        "7. Récupérez DATABASE_URL de votre PostgreSQL",
        "8. Déployez et testez /health"
    ]
    
    for step in steps:
        print(f"  {step}")
    
    print(f"\n📖 Guide détaillé: RENDER_DEPLOYMENT.md")
    print(f"🔑 Vos variables d'env: .env.render")

def main():
    print("🎯 Préparation déploiement Render - DFC Gallery")
    
    errors, warnings = check_render_readiness()
    
    # Affichage des warnings
    if warnings:
        print(f"\n⚠️  Avertissements ({len(warnings)}):")
        for warning in warnings:
            print(f"  {warning}")
    
    # Résultat final
    if errors:
        print(f"\n❌ Erreurs bloquantes ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
        print("\n🔧 Corrigez ces problèmes avant de déployer")
        return False
    else:
        print("\n✅ Configuration Render OK!")
        display_render_steps()
        
        print("\n💡 URLs finales:")
        print("  - API: https://dfc-galery-api.onrender.com")
        print("  - Health: https://dfc-galery-api.onrender.com/health") 
        print("  - Docs: https://dfc-galery-api.onrender.com/docs")
        
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)