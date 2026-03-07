from PIL import Image
from io import BytesIO
import requests
from typing import Optional, Tuple
from fastapi import HTTPException


class ImageUtils:
    """Utilitaires pour le traitement d'images"""
    
    @staticmethod
    async def resize_image(
        image_url: str,
        max_width: int = 1920,
        max_height: int = 1080,
        quality: int = 85
    ) -> BytesIO:
        """
        Redimensionner une image en conservant le ratio
        
        Args:
            image_url: URL de l'image
            max_width: Largeur maximale
            max_height: Hauteur maximale
            quality: Qualité de compression JPEG (1-100)
            
        Returns:
            BytesIO contenant l'image redimensionnée
        """
        try:
            # Télécharger l'image
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            
            # Conserver le format original si possible
            original_format = image.format or 'JPEG'
            
            # Calculer les nouvelles dimensions
            ratio = min(max_width / image.width, max_height / image.height)
            
            if ratio < 1:
                new_width = int(image.width * ratio)
                new_height = int(image.height * ratio)
                image = image.resize((new_width, new_height), Image.LANCZOS)
            
            # Sauvegarder dans un buffer
            output = BytesIO()
            if original_format in ['JPEG', 'JPG']:
                image.save(output, format='JPEG', quality=quality, optimize=True)
            elif original_format == 'PNG':
                image.save(output, format='PNG', optimize=True)
            else:
                image.save(output, format='JPEG', quality=quality, optimize=True)
            
            output.seek(0)
            return output
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors du redimensionnement: {str(e)}"
            )
    
    @staticmethod
    async def create_thumbnail(
        image_url: str,
        size: Tuple[int, int] = (300, 300),
        quality: int = 75
    ) -> BytesIO:
        """
        Créer une miniature d'une image
        
        Args:
            image_url: URL de l'image
            size: Dimensions de la miniature (width, height)
            quality: Qualité de compression JPEG (1-100)
            
        Returns:
            BytesIO contenant la miniature
        """
        try:
            # Télécharger l'image
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            
            # Convertir en RGB si nécessaire (pour JPEG)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Créer la miniature (crop au centre)
            image.thumbnail(size, Image.LANCZOS)
            
            # Sauvegarder
            output = BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            
            return output
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la création de la miniature: {str(e)}"
            )
    
    @staticmethod
    async def compress_image(
        image_url: str,
        quality: int = 75,
        max_size_mb: Optional[float] = None
    ) -> BytesIO:
        """
        Compresser une image
        
        Args:
            image_url: URL de l'image
            quality: Qualité de compression JPEG (1-100)
            max_size_mb: Taille maximale en MB (optionnel)
            
        Returns:
            BytesIO contenant l'image compressée
        """
        try:
            # Télécharger l'image
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            
            # Convertir en RGB si nécessaire
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # Compression initiale
            output = BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            
            # Si une taille max est spécifiée, réduire progressivement la qualité
            if max_size_mb:
                max_size_bytes = max_size_mb * 1024 * 1024
                current_quality = quality
                
                while output.tell() > max_size_bytes and current_quality > 20:
                    output = BytesIO()
                    current_quality -= 5
                    image.save(output, format='JPEG', quality=current_quality, optimize=True)
            
            output.seek(0)
            return output
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la compression: {str(e)}"
            )
    
    @staticmethod
    def get_image_dimensions(image_url: str) -> Tuple[int, int]:
        """
        Obtenir les dimensions d'une image
        
        Args:
            image_url: URL de l'image
            
        Returns:
            Tuple (width, height)
        """
        try:
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            return image.size
            
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de la lecture des dimensions: {str(e)}"
            )
    
    @staticmethod
    def validate_image(file_content: bytes) -> bool:
        """
        Valider qu'un fichier est bien une image
        
        Args:
            file_content: Contenu du fichier
            
        Returns:
            True si c'est une image valide
        """
        try:
            image = Image.open(BytesIO(file_content))
            image.verify()
            return True
        except:
            return False
