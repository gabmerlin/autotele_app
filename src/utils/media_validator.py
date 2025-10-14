"""
Module de validation des uploads de médias pour la sécurité.

Ce module valide les fichiers téléchargés pour prévenir :
- Saturation disque (DoS)
- Upload de fichiers malveillants
- Consommation excessive de bande passante
"""
import os
import asyncio
import shutil
from pathlib import Path
from typing import Optional, Tuple, List
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument

from utils.logger import get_logger
from utils.constants import MAX_FILE_SIZE_BYTES

logger = get_logger()


# Whitelist des types MIME autorisés
ALLOWED_MIME_TYPES = [
    # Images
    'image/jpeg',
    'image/jpg',
    'image/png',
    'image/gif',
    'image/webp',
    'image/bmp',
    
    # Vidéos
    'video/mp4',
    'video/mpeg',
    'video/quicktime',
    'video/x-msvideo',
    'video/webm',
    
    # Documents
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    
    # Audio
    'audio/mpeg',
    'audio/mp3',
    'audio/wav',
    'audio/ogg',
    
    # Archives (avec précaution)
    'application/zip',
    'application/x-rar-compressed',
]

# Extensions de fichiers autorisées (double vérification)
ALLOWED_EXTENSIONS = [
    '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',  # Images
    '.mp4', '.mpeg', '.mov', '.avi', '.webm',  # Vidéos
    '.pdf', '.doc', '.docx',  # Documents
    '.mp3', '.wav', '.ogg',  # Audio
    '.zip', '.rar',  # Archives
]

# Taille maximale par défaut (depuis constants.py)
DEFAULT_MAX_SIZE = MAX_FILE_SIZE_BYTES

# Limite d'espace disque minimum à garder libre (500 MB)
MIN_FREE_SPACE = 500 * 1024 * 1024

# Timeout pour les téléchargements (secondes)
DOWNLOAD_TIMEOUT = 120


class MediaValidator:
    """Validateur de médias pour les téléchargements sécurisés."""
    
    @staticmethod
    def get_real_mime_type(file_path: str) -> str:
        """
        Détecte le VRAI type MIME d'un fichier via les magic bytes.
        
        SÉCURITÉ: Vérifie le contenu réel du fichier, pas juste l'extension.
        Cela évite les fichiers malveillants déguisés (ex: .exe renommé en .jpg)
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            str: Type MIME détecté ou 'application/octet-stream'
        """
        try:
            with open(file_path, 'rb') as f:
                header = f.read(32)  # Lire les 32 premiers bytes
            
            if len(header) < 4:
                return 'application/octet-stream'
            
            # Images
            if header.startswith(b'\xff\xd8\xff'):
                return 'image/jpeg'
            elif header.startswith(b'\x89PNG\r\n\x1a\n'):
                return 'image/png'
            elif header.startswith(b'GIF89a') or header.startswith(b'GIF87a'):
                return 'image/gif'
            elif header.startswith(b'RIFF') and header[8:12] == b'WEBP':
                return 'image/webp'
            elif header.startswith(b'BM'):
                return 'image/bmp'
            
            # Documents
            elif header.startswith(b'%PDF'):
                return 'application/pdf'
            elif header.startswith(b'PK\x03\x04'):
                # ZIP ou documents Office (docx, xlsx)
                if b'word/' in header or b'xl/' in header:
                    return 'application/vnd.openxmlformats-officedocument'
                return 'application/zip'
            elif header.startswith(b'\xd0\xcf\x11\xe0'):
                # Format Microsoft Office ancien (doc, xls)
                return 'application/msword'
            
            # Audio
            elif header.startswith(b'ID3') or header.startswith(b'\xff\xfb'):
                return 'audio/mpeg'
            elif header.startswith(b'RIFF') and header[8:12] == b'WAVE':
                return 'audio/wav'
            elif header.startswith(b'OggS'):
                return 'audio/ogg'
            
            # Vidéo
            elif header[4:8] == b'ftyp':
                # MP4, MOV, M4V
                return 'video/mp4'
            elif header.startswith(b'RIFF') and header[8:12] == b'AVI ':
                return 'video/x-msvideo'
            elif header.startswith(b'\x1a\x45\xdf\xa3'):
                return 'video/webm'
            
            # Archives
            elif header.startswith(b'Rar!\x1a\x07'):
                return 'application/x-rar-compressed'
            elif header.startswith(b'\x1f\x8b'):
                return 'application/gzip'
            
            # ⚠️ FICHIERS DANGEREUX À BLOQUER
            elif header.startswith(b'MZ'):
                # Exécutable Windows (.exe, .dll, .sys)
                return 'application/x-msdownload'
            elif header.startswith(b'\x7fELF'):
                # Exécutable Linux/Unix
                return 'application/x-executable'
            elif header.startswith(b'#!'):
                # Script shell
                return 'application/x-sh'
            
        except Exception as e:
            logger.debug(f"Erreur lecture magic bytes: {e}")
        
        return 'application/octet-stream'
    
    @staticmethod
    def is_mime_type_compatible(real_mime: str, expected_mime: str) -> bool:
        """
        Vérifie si deux types MIME sont compatibles.
        
        Args:
            real_mime: Type MIME réel (détecté via magic bytes)
            expected_mime: Type MIME attendu (déclaré)
            
        Returns:
            bool: True si compatibles
        """
        if not real_mime or not expected_mime:
            return True  # Si on ne peut pas vérifier, on accepte
        
        # Normaliser
        real_mime = real_mime.lower().strip()
        expected_mime = expected_mime.lower().strip()
        
        # Correspondance exacte
        if real_mime == expected_mime:
            return True
        
        # Catégories compatibles (même préfixe)
        real_category = real_mime.split('/')[0]
        expected_category = expected_mime.split('/')[0]
        
        if real_category == expected_category:
            return True  # image/jpeg vs image/jpg OK
        
        # Cas spéciaux
        compatible_pairs = [
            ('image/jpg', 'image/jpeg'),
            ('image/jpeg', 'image/jpg'),
            ('application/zip', 'application/vnd.openxmlformats-officedocument'),
        ]
        
        return (real_mime, expected_mime) in compatible_pairs or \
               (expected_mime, real_mime) in compatible_pairs
    
    @staticmethod
    def validate_file_size(size: int, max_size: int = DEFAULT_MAX_SIZE) -> Tuple[bool, str]:
        """
        Valide la taille d'un fichier.
        
        Args:
            size: Taille du fichier en bytes
            max_size: Taille maximale autorisée en bytes
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if size <= 0:
            return False, "Taille de fichier invalide"
        
        if size > max_size:
            size_mb = size / (1024 * 1024)
            max_mb = max_size / (1024 * 1024)
            return False, f"Fichier trop volumineux: {size_mb:.1f} MB (max: {max_mb:.1f} MB)"
        
        return True, ""
    
    @staticmethod
    def validate_mime_type(mime_type: str) -> Tuple[bool, str]:
        """
        Valide le type MIME d'un fichier.
        
        Args:
            mime_type: Type MIME du fichier
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not mime_type:
            return False, "Type MIME inconnu"
        
        # Normaliser le type MIME
        mime_lower = mime_type.lower().strip()
        
        if mime_lower in ALLOWED_MIME_TYPES:
            return True, ""
        
        return False, f"Type MIME non autorisé: {mime_type}"
    
    @staticmethod
    def validate_extension(filename: str) -> Tuple[bool, str]:
        """
        Valide l'extension d'un fichier.
        
        Args:
            filename: Nom du fichier
            
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not filename:
            return False, "Nom de fichier vide"
        
        # Récupérer l'extension
        ext = Path(filename).suffix.lower()
        
        if not ext:
            return False, "Fichier sans extension"
        
        if ext in ALLOWED_EXTENSIONS:
            return True, ""
        
        return False, f"Extension non autorisée: {ext}"
    
    @staticmethod
    def check_disk_space(directory: str) -> Tuple[bool, str]:
        """
        Vérifie qu'il y a suffisamment d'espace disque disponible.
        
        Args:
            directory: Répertoire de destination
            
        Returns:
            Tuple[bool, str]: (has_space, error_message)
        """
        try:
            usage = shutil.disk_usage(directory)
            free_space = usage.free
            
            if free_space < MIN_FREE_SPACE:
                free_mb = free_space / (1024 * 1024)
                min_mb = MIN_FREE_SPACE / (1024 * 1024)
                return False, f"Espace disque insuffisant: {free_mb:.0f} MB libre (min: {min_mb:.0f} MB)"
            
            return True, ""
        except Exception as e:
            return False, f"Erreur vérification espace disque: {e}"
    
    @staticmethod
    def validate_telegram_media(media) -> Tuple[bool, str, dict]:
        """
        Valide un média Telegram avant téléchargement.
        
        Args:
            media: Objet média Telegram
            
        Returns:
            Tuple[bool, str, dict]: (is_valid, error_message, info)
        """
        if not media:
            return False, "Aucun média fourni", {}
        
        info = {
            'type': type(media).__name__,
            'size': 0,
            'mime_type': None,
            'filename': None
        }
        
        # Validation pour les photos
        if isinstance(media, MessageMediaPhoto):
            # Les photos Telegram sont généralement sûres et de taille raisonnable
            info['mime_type'] = 'image/jpeg'  # Par défaut pour les photos
            return True, "", info
        
        # Validation pour les documents
        if isinstance(media, MessageMediaDocument):
            if not hasattr(media, 'document') or not media.document:
                return False, "Document invalide", info
            
            doc = media.document
            
            # Récupérer les informations
            size = getattr(doc, 'size', 0)
            mime_type = getattr(doc, 'mime_type', None)
            
            info['size'] = size
            info['mime_type'] = mime_type
            
            # Récupérer le nom du fichier si disponible
            if hasattr(doc, 'attributes'):
                for attr in doc.attributes:
                    if hasattr(attr, 'file_name'):
                        info['filename'] = attr.file_name
                        break
            
            # Valider la taille
            is_valid, error = MediaValidator.validate_file_size(size)
            if not is_valid:
                return False, error, info
            
            # Valider le type MIME
            if mime_type:
                is_valid, error = MediaValidator.validate_mime_type(mime_type)
                if not is_valid:
                    return False, error, info
            
            # Valider l'extension si filename disponible
            if info['filename']:
                is_valid, error = MediaValidator.validate_extension(info['filename'])
                if not is_valid:
                    return False, error, info
            
            return True, "", info
        
        # Type de média non supporté
        return False, f"Type de média non supporté: {type(media).__name__}", info
    
    @staticmethod
    async def download_media_safely(
        client,
        message,
        destination_dir: str,
        timeout: int = DOWNLOAD_TIMEOUT
    ) -> Tuple[bool, Optional[str], str]:
        """
        Télécharge un média avec toutes les validations de sécurité.
        
        Args:
            client: Client Telegram
            message: Message contenant le média
            destination_dir: Répertoire de destination
            timeout: Timeout en secondes
            
        Returns:
            Tuple[bool, Optional[str], str]: (success, file_path, error_message)
        """
        try:
            # Vérifier qu'il y a un média
            if not message.media:
                return False, None, "Aucun média dans le message"
            
            # Valider le média
            is_valid, error, info = MediaValidator.validate_telegram_media(message.media)
            if not is_valid:
                logger.warning(f"Média rejeté: {error}")
                return False, None, error
            
            # Vérifier l'espace disque
            has_space, error = MediaValidator.check_disk_space(destination_dir)
            if not has_space:
                logger.error(f"{error}")
                return False, None, error
            
            # Créer le répertoire si nécessaire
            os.makedirs(destination_dir, exist_ok=True)
            
            # Télécharger avec timeout
            logger.debug(
                f"📥 Téléchargement média: {info['type']} "
                f"({info['size'] / 1024:.1f} KB, {info['mime_type']})"
            )
            
            try:
                file_path = await asyncio.wait_for(
                    client.download_media(message, destination_dir),
                    timeout=timeout
                )
                
                if file_path:
                    # Vérifications post-téléchargement
                    downloaded_size = os.path.getsize(file_path)
                    
                    # 1. Vérifier la taille correspond
                    expected_size = info.get('size', 0)
                    if expected_size > 0:
                        # Tolérance de 1KB pour les variations
                        if abs(downloaded_size - expected_size) > 1024:
                            os.remove(file_path)
                            return False, None, "Taille du fichier incorrecte (possible corruption)"
                    
                    # 2. Vérifier le VRAI type MIME (magic bytes)
                    real_mime = MediaValidator.get_real_mime_type(file_path)
                    expected_mime = info.get('mime_type')
                    
                    # Bloquer les exécutables et scripts
                    dangerous_types = [
                        'application/x-msdownload',  # .exe Windows
                        'application/x-executable',   # Binaires Linux
                        'application/x-sh',           # Scripts shell
                    ]
                    
                    if real_mime in dangerous_types:
                        os.remove(file_path)
                        logger.warning(f"🚫 Fichier exécutable bloqué: {real_mime}")
                        return False, None, "Type de fichier interdit (exécutable ou script)"
                    
                    # 3. Vérifier cohérence MIME déclaré vs réel
                    if expected_mime and not MediaValidator.is_mime_type_compatible(real_mime, expected_mime):
                        os.remove(file_path)
                        logger.warning(f"🚫 MIME incohérent: attendu {expected_mime}, obtenu {real_mime}")
                        return False, None, f"Type MIME incohérent (possible fichier déguisé)"
                    
                    logger.debug(f"✅ Fichier vérifié: {real_mime} ({downloaded_size} bytes)")
                    return True, file_path, ""
                else:
                    return False, None, "Échec du téléchargement"
                
            except asyncio.TimeoutError:
                error_msg = f"Timeout après {timeout}s"
                logger.warning(f"{error_msg}")
                return False, None, error_msg
        
        except Exception as e:
            error_msg = f"Erreur téléchargement: {e}"
            logger.error(f"{error_msg}")
            return False, None, error_msg
    
    @staticmethod
    def get_safe_filename(original_filename: str) -> str:
        """
        Nettoie un nom de fichier pour éviter les injections de chemin.
        
        Args:
            original_filename: Nom de fichier original
            
        Returns:
            str: Nom de fichier sécurisé
        """
        if not original_filename:
            return "unnamed_file"
        
        # Retirer les chemins relatifs et absolus
        filename = Path(original_filename).name
        
        # Retirer les caractères dangereux
        dangerous_chars = ['..', '/', '\\', '\x00', '|', ':', '*', '?', '"', '<', '>']
        safe_name = filename
        
        for char in dangerous_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Limiter la longueur
        if len(safe_name) > 200:
            ext = Path(safe_name).suffix
            safe_name = safe_name[:200-len(ext)] + ext
        
        return safe_name


# Instance globale
_validator = MediaValidator()


def get_media_validator() -> MediaValidator:
    """
    Récupère l'instance globale du validateur de médias.
    
    Returns:
        MediaValidator: Instance du validateur
    """
    return _validator

