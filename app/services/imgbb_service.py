import httpx
import base64
from fastapi import UploadFile, HTTPException
from app.config.settings import settings
import os

# Limite ImgBB (32 MB)
IMGBB_SIZE_LIMIT = 32 * 1024 * 1024


class ImgBBService:
    def __init__(self):
        """Initialiser le service ImgBB"""
        self.api_key = settings.IMGBB_API_KEY
        self.upload_url = "https://api.imgbb.com/1/upload"
        print(f"[DEBUG] ImgBB Service initialized")
    
    async def upload_image(
        self,
        file: UploadFile,
        folder: str = "dfc_gallery"
    ) -> dict:
        """
        Upload une image sur ImgBB
        
        Args:
            file: Fichier à uploader
            folder: Nom du dossier (utilisé comme préfixe du nom)
            
        Returns:
            dict: Informations sur l'image uploadée (compatible avec l'ancien format)
        """
        try:
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
            
            # ImgBB supporte jusqu'à 32 MB, pas besoin de compression
            if len(contents) > IMGBB_SIZE_LIMIT:
                raise HTTPException(
                    status_code=400,
                    detail=f"Fichier trop volumineux pour ImgBB. Taille maximale: 32 MB"
                )
            
            print(f"[UPLOAD] Uploading {file.filename} ({len(contents) / (1024*1024):.2f} MB) to ImgBB...")
            
            # Encoder en base64
            image_base64 = base64.b64encode(contents).decode('utf-8')
            
            # Préparer les données du formulaire
            form_data = {
                "key": self.api_key,
                "image": image_base64,
                "name": f"{folder}_{os.path.splitext(file.filename)[0]}"
            }
            
            # Envoyer à ImgBB
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(self.upload_url, data=form_data)
            
            if response.status_code != 200:
                error_detail = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                print(f"[ERROR] ImgBB response: {error_detail}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Erreur ImgBB: {error_detail}"
                )
            
            result = response.json()
            
            if not result.get("success"):
                raise HTTPException(
                    status_code=500,
                    detail=f"ImgBB upload failed: {result.get('error', {}).get('message', 'Unknown error')}"
                )
            
            data = result["data"]
            print(f"[UPLOAD] ✅ Success! URL: {data['url']}")
            
            # Retourner un format compatible avec l'ancien service Cloudinary
            return {
                "secure_url": data["url"],
                "url": data["url"],
                "public_id": data["id"],
                "width": data.get("width"),
                "height": data.get("height"),
                "format": data.get("image", {}).get("extension"),
                "bytes": data.get("size"),
                "delete_url": data.get("delete_url"),
                "thumb_url": data.get("thumb", {}).get("url"),
                "medium_url": data.get("medium", {}).get("url") if data.get("medium") else data["url"]
            }
            
        except HTTPException:
            raise
        except Exception as e:
            print(f"[ERROR] Upload exception: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erreur lors de l'upload: {str(e)}"
            )
    
    async def delete_image(self, image_url: str) -> dict:
        """
        Note: ImgBB ne supporte pas la suppression via API avec le free tier.
        Les images expirent automatiquement si configuré, ou restent permanentes.
        
        Args:
            image_url: URL de l'image (non utilisé)
            
        Returns:
            dict: Résultat factice
        """
        print(f"[DELETE] ImgBB free tier ne supporte pas la suppression via API")
        return {"result": "not_supported", "message": "ImgBB free tier does not support deletion via API"}


# Instance globale
imgbb_service = ImgBBService()
