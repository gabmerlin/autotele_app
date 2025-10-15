"""
Système de cache persistent pour les photos de profil.
Utilise la base de données SQLite pour stocker les chemins des photos.
"""
import os
import asyncio
from pathlib import Path
from typing import Optional, Callable
from telethon import TelegramClient

from database.telegram_db import get_telegram_db
from utils.logger import get_logger
from utils.media_validator import MediaValidator

logger = get_logger()


class ProfilePhotoCache:
    """
    Gestionnaire de cache pour les photos de profil.
    
    Fonctionnalités :
    - Vérifie si une photo existe déjà en cache
    - Télécharge les photos manquantes en arrière-plan
    - Stocke les chemins dans la base de données SQLite
    """
    
    def __init__(self):
        """Initialise le cache des photos."""
        self.db = get_telegram_db()
        
        # CORRECTION : Utiliser get_temp_dir() pour la cohérence
        from utils.paths import get_temp_dir
        self.photos_dir = get_temp_dir() / "photos"
        self.photos_dir.mkdir(parents=True, exist_ok=True)
        
        # Queue pour téléchargements en arrière-plan
        self._download_queue: asyncio.Queue = asyncio.Queue()
        self._is_processing = False
    
    def get_photo_path(self, entity_id: int) -> Optional[str]:
        """
        Récupère le chemin d'une photo depuis le cache.
        
        Args:
            entity_id: ID de l'entité
            
        Returns:
            Optional[str]: Chemin de la photo ou None si pas en cache
        """
        photo_path = self.db.get_profile_photo(entity_id)
        
        # Vérifier que le fichier existe toujours
        if photo_path and os.path.exists(photo_path):
            return photo_path
        
        # Si le fichier n'existe plus, supprimer de la DB
        if photo_path:
            logger.warning(f"Photo en cache mais fichier manquant: {photo_path}")
            # Note: on pourrait supprimer l'entrée de la DB ici
        
        return None
    
    def has_photo(self, entity_id: int) -> bool:
        """
        Vérifie si une photo existe en cache.
        
        Args:
            entity_id: ID de l'entité
            
        Returns:
            bool: True si la photo existe
        """
        photo_path = self.get_photo_path(entity_id)
        return photo_path is not None
    
    async def download_photo(
        self,
        client: TelegramClient,
        entity: any,
        entity_id: int,
        callback: Optional[Callable[[int, str], None]] = None
    ) -> Optional[str]:
        """
        Télécharge une photo de profil et la met en cache.
        
        ÉVITE LES DOUBLONS : Utilise entity_id comme nom de fichier.
        
        Args:
            client: Client Telegram
            entity: Entité Telegram
            entity_id: ID de l'entité
            callback: Fonction appelée après téléchargement (entity_id, photo_path)
            
        Returns:
            Optional[str]: Chemin de la photo ou None
        """
        # Vérifier si déjà en cache
        cached_path = self.get_photo_path(entity_id)
        if cached_path:
            logger.debug(f"Photo déjà en cache pour entity {entity_id}")
            return cached_path
        
        try:
            # Vérifier l'espace disque avant téléchargement
            has_space, space_error = MediaValidator.check_disk_space(str(self.photos_dir))
            if not has_space:
                logger.warning(f"Espace disque insuffisant : {space_error}")
                return None
            
            # Vérifier si l'entité a une photo
            if not hasattr(entity, 'photo') or not entity.photo:
                logger.debug(f"Entity {entity_id} n'a pas de photo")
                return None
            
            # Nom de fichier basé sur entity_id (ÉVITE LES DOUBLONS)
            target_file = self.photos_dir / f"{entity_id}.jpg"
            
            # Si le fichier existe déjà sur disque (mais pas en DB)
            if target_file.exists():
                logger.debug(f"Photo trouvée sur disque pour entity {entity_id}")
                self.db.save_profile_photo(entity_id, str(target_file))
                return str(target_file)
            
            # Télécharger avec timeout et nom de fichier unique
            photo_path = await asyncio.wait_for(
                client.download_profile_photo(entity, str(target_file)),
                timeout=15  # 15 secondes max
            )
            
            if photo_path:
                # Sauvegarder dans la DB
                self.db.save_profile_photo(entity_id, photo_path)
                logger.debug(f"Photo téléchargée et mise en cache : {photo_path}")
                
                # Appeler le callback si fourni
                if callback:
                    try:
                        callback(entity_id, photo_path)
                    except Exception as e:
                        logger.error(f"Erreur callback photo: {e}")
                
                return photo_path
            
        except asyncio.TimeoutError:
            logger.debug(f"Timeout téléchargement photo entity {entity_id}")
        except Exception as e:
            logger.debug(f"Erreur téléchargement photo entity {entity_id}: {e}")
        
        return None
    
    async def download_photo_async(
        self,
        client: TelegramClient,
        entity: any,
        entity_id: int,
        callback: Optional[Callable[[int, str], None]] = None
    ):
        """
        Télécharge une photo en arrière-plan (non-bloquant).
        
        Args:
            client: Client Telegram
            entity: Entité Telegram
            entity_id: ID de l'entité
            callback: Fonction appelée après téléchargement
        """
        # Créer une tâche asynchrone
        asyncio.create_task(
            self._download_photo_task(client, entity, entity_id, callback)
        )
    
    async def _download_photo_task(
        self,
        client: TelegramClient,
        entity: any,
        entity_id: int,
        callback: Optional[Callable[[int, str], None]]
    ):
        """Tâche de téléchargement de photo (privée)."""
        try:
            await self.download_photo(client, entity, entity_id, callback)
        except Exception as e:
            logger.error(f"Erreur tâche téléchargement photo {entity_id}: {e}")
    
    def save_photo_path(self, entity_id: int, photo_path: str):
        """
        Sauvegarde un chemin de photo dans le cache.
        
        Utile quand la photo est déjà téléchargée par un autre moyen.
        
        Args:
            entity_id: ID de l'entité
            photo_path: Chemin de la photo
        """
        if os.path.exists(photo_path):
            self.db.save_profile_photo(entity_id, photo_path)
            logger.debug(f"Chemin photo sauvegardé dans cache : {entity_id}")
        else:
            logger.warning(f"Tentative de sauvegarder chemin inexistant : {photo_path}")
    
    def get_cache_stats(self) -> dict:
        """
        Récupère les statistiques du cache.
        
        Returns:
            dict: Statistiques
        """
        stats = self.db.get_stats()
        
        # Taille totale des photos
        total_size = 0
        photo_count = 0
        
        if self.photos_dir.exists():
            for photo_file in self.photos_dir.iterdir():
                if photo_file.is_file():
                    total_size += photo_file.stat().st_size
                    photo_count += 1
        
        return {
            'photos_in_db': stats.get('photos_count', 0),
            'photos_on_disk': photo_count,
            'total_size_mb': total_size / (1024 * 1024),
            'photos_dir': str(self.photos_dir)
        }
    
    def cleanup_orphaned_photos(self):
        """
        Nettoie les photos orphelines (fichiers sans entrée dans la DB).
        """
        if not self.photos_dir.exists():
            return
        
        cleaned = 0
        for photo_file in self.photos_dir.iterdir():
            if photo_file.is_file():
                # Vérifier si ce fichier est référencé dans la DB
                photo_path = str(photo_file)
                # Requête pour vérifier si le chemin existe
                cursor = self.db.conn.execute(
                    "SELECT 1 FROM profile_photos WHERE photo_path = ?",
                    (photo_path,)
                )
                
                if not cursor.fetchone():
                    # Fichier orphelin, le supprimer
                    try:
                        photo_file.unlink()
                        cleaned += 1
                        logger.debug(f"Photo orpheline supprimée : {photo_path}")
                    except Exception as e:
                        logger.error(f"Erreur suppression photo orpheline : {e}")
        
        if cleaned > 0:
            logger.info(f"Nettoyage : {cleaned} photo(s) orpheline(s) supprimée(s)")
        
        return cleaned


# Instance globale (singleton)
_photo_cache_instance = None


def get_photo_cache() -> ProfilePhotoCache:
    """
    Récupère l'instance globale du cache photos.
    
    Returns:
        ProfilePhotoCache: Instance du cache
    """
    global _photo_cache_instance
    if _photo_cache_instance is None:
        _photo_cache_instance = ProfilePhotoCache()
    return _photo_cache_instance

