import cloudinary
import cloudinary.uploader
from fastapi import UploadFile, HTTPException
from app.config.settings import settings
import os
from PIL import Image
import io

# Limite Cloudinary Free tier (10 MB)
CLOUDINARY_FREE_LIMIT = 10 * 1024 * 1024


class CloudinaryService:
    def __init__(self):
        """Initialiser la configuration Cloudinary"""
        print(f"[DEBUG] Cloudinary Config - cloud_name: {settings.CLOUDINARY_CLOUD_NAME}")
        print(f"[DEBUG] Cloudinary Config - api_key: {settings.CLOUDINARY_API_KEY}")
        
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET
        )
    
    def _compress_image(self, contents: bytes, target_size: int = CLOUDINARY_FREE_LIMIT) -> bytes:
        """
        Compresse une image pour qu'elle soit en dessous de la taille cible.
        
        Args:
            contents: Contenu binaire de l'image
            target_size: Taille cible en bytes (défaut: 10 MB)
            
        Returns:
            bytes: Image compressée
        """
        # Ouvrir l'image
        img = Image.open(io.BytesIO(contents))
        
        # Convertir en RGB si nécessaire (pour les PNG avec transparence)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        
        original_size = len(contents)
        print(f"[COMPRESS] Taille originale: {original_size / (1024*1024):.2f} MB")
        
        # Essayer différentes qualités en descendant
        for quality in [85, 75, 65, 55, 45, 35]:
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            compressed = output.getvalue()
            
            print(f"[COMPRESS] Qualité {quality}: {len(compressed) / (1024*1024):.2f} MB")
            
            if len(compressed) < target_size:
                print(f"[COMPRESS] ✅ Compression réussie à qualité {quality}")
                return compressed
        
        # Si toujours trop gros, réduire la résolution
        print("[COMPRESS] Réduction de la résolution nécessaire...")
        
        for scale in [0.75, 0.5, 0.35, 0.25]:
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            resized.save(output, format='JPEG', quality=75, optimize=True)
            compressed = output.getvalue()
            
            print(f"[COMPRESS] Résolution {new_width}x{new_height}: {len(compressed) / (1024*1024):.2f} MB")
            
            if len(compressed) < target_size:
                print(f"[COMPRESS] ✅ Compression réussie à {int(scale*100)}% de la taille originale")
                return compressed
        
        # Dernier recours: très basse qualité et résolution
        output = io.BytesIO()
        resized = img.resize((int(img.width * 0.2), int(img.height * 0.2)), Image.Resampling.LANCZOS)
        resized.save(output, format='JPEG', quality=50, optimize=True)
        return output.getvalue()
    
    async def upload_image(
        self,
        file: UploadFile,
        folder: str = "dfc_gallery"
    ) -> dict:
        """
        Upload une image sur Cloudinary
        
        Args:
            file: Fichier à uploader
            folder: Dossier de destination sur Cloudinary
            
        Returns:
            dict: Informations sur l'image uploadée
        """
        try:
            # Forcer la reconfiguration avant chaque upload
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET
            )
            
            # Vérifier la configuration active
            current_config = cloudinary.config()
            print(f"[DEBUG UPLOAD] Config active - cloud_name: {current_config.cloud_name}")
            
            # Valider l'extension
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in settings.ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Extension de fichier non autorisée. Extensions acceptées: {settings.ALLOWED_EXTENSIONS}"
                )
            
            # Lire le contenu du fichier
            contents = await file.read()
            
            # Valider la taille (vs limite backend)
            if len(contents) > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"Fichier trop volumineux. Taille maximale: {settings.MAX_FILE_SIZE / (1024*1024)} MB"
                )
            
            # Compresser automatiquement si > 10 MB (limite Cloudinary Free)
            if len(contents) > CLOUDINARY_FREE_LIMIT:
                print(f"[UPLOAD] Fichier {file.filename} > 10 MB, compression automatique...")
                contents = self._compress_image(contents)
                print(f"[UPLOAD] Taille après compression: {len(contents) / (1024*1024):.2f} MB")
            
            # Upload sur Cloudinary
            upload_result = cloudinary.uploader.upload(
                contents,
                folder=folder,
                resource_type="image",
                format="jpg",
                quality="auto:good",
                fetch_format="auto"
            )
            
            return upload_result
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'upload: {str(e)}"
            )
    
    async def delete_image(self, image_url: str) -> dict:
        """
        Supprimer une image de Cloudinary
        
        Args:
            image_url: URL de l'image à supprimer
            
        Returns:
            dict: Résultat de la suppression
        """
        try:
            # Extraire le public_id de l'URL
            public_id = self._extract_public_id(image_url)
            
            # Supprimer de Cloudinary
            result = cloudinary.uploader.destroy(public_id)
            
            return result
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la suppression: {str(e)}"
            )
    
    def _extract_public_id(self, url: str) -> str:
        """
        Extraire le public_id d'une URL Cloudinary
        
        Args:
            url: URL complète de l'image
            
        Returns:
            str: Public ID de l'image
        """
        # Format typique: https://res.cloudinary.com/cloud_name/image/upload/v1234567890/folder/image.jpg
        parts = url.split('/')
        # Trouver l'index après "upload"
        try:
            upload_idx = parts.index('upload')
            # Le public_id commence après version (v1234567890)
            public_id_parts = parts[upload_idx + 2:]  # Sauter "upload" et version
            public_id = '/'.join(public_id_parts)
            # Retirer l'extension
            public_id = os.path.splitext(public_id)[0]
            return public_id
        except (ValueError, IndexError):
            raise HTTPException(
                status_code=400,
                detail="URL Cloudinary invalide"
            )
    
    async def get_optimized_url(
        self,
        public_id: str,
        width: int = None,
        height: int = None,
        quality: str = "auto"
    ) -> str:
        """
        Obtenir une URL optimisée pour une image
        
        Args:
            public_id: ID public de l'image
            width: Largeur souhaitée
            height: Hauteur souhaitée
            quality: Qualité (auto, low, good, best)
            
        Returns:
            str: URL optimisée
        """
        transformation = {
            'quality': quality,
            'fetch_format': 'auto'
        }
        
        if width:
            transformation['width'] = width
        if height:
            transformation['height'] = height
        
        url = cloudinary.CloudinaryImage(public_id).build_url(**transformation)
        return url
