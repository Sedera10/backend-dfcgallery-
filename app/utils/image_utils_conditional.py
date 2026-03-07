"""
Version conditionnelle des utilitaires image
Fonctionne avec ou sans Pillow installé
"""

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

def resize_image(image_data, max_size=(800, 600)):
    """Redimensionner une image (si Pillow disponible)"""
    if not PILLOW_AVAILABLE:
        # Retourner les données originales si Pillow n'est pas disponible
        return image_data
    
    try:
        # Code original avec Pillow
        img = Image.open(image_data)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        return img
    except Exception as e:
        print(f"Erreur redimensionnement image: {e}")
        return image_data

def validate_image_format(image_data):
    """Valider le format d'image (si Pillow disponible)"""
    if not PILLOW_AVAILABLE:
        # Validation basique sans Pillow
        return True
    
    try:
        img = Image.open(image_data)
        return img.format.lower() in ['jpeg', 'jpg', 'png', 'webp']
    except Exception:
        return False

def get_image_info(image_data):
    """Obtenir les infos d'image (si Pillow disponible)"""
    if not PILLOW_AVAILABLE:
        return {"width": 0, "height": 0, "format": "unknown"}
    
    try:
        img = Image.open(image_data)
        return {
            "width": img.width,
            "height": img.height, 
            "format": img.format
        }
    except Exception:
        return {"width": 0, "height": 0, "format": "unknown"}