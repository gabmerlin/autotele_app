"""Gestion centralisée des chemins de l'application."""
import sys
from pathlib import Path
from typing import Final


def get_application_path() -> Path:
    """
    Retourne le chemin racine de l'application.
    
    Compatible avec PyInstaller (exécutable compilé) et mode développement.
    
    Returns:
        Path: Chemin racine de l'application
    """
    if getattr(sys, 'frozen', False):
        # Application compilée avec PyInstaller
        # sys.executable pointe vers AutoTele.exe
        # On retourne le répertoire parent (où se trouve l'exe)
        return Path(sys.executable).parent
    else:
        # Mode développement (script Python)
        return Path(__file__).parent.parent.parent


# Racine du projet (compatible PyInstaller)
PROJECT_ROOT: Final[Path] = get_application_path()

# Répertoires principaux (créés dynamiquement à côté de l'exe)
TEMP_DIR: Final[Path] = PROJECT_ROOT / 'temp'
SESSIONS_DIR: Final[Path] = PROJECT_ROOT / 'sessions'
LOGS_DIR: Final[Path] = PROJECT_ROOT / 'logs'
CONFIG_DIR: Final[Path] = PROJECT_ROOT / 'config'
BACKUP_DIR: Final[Path] = PROJECT_ROOT / 'backup'


def _ensure_dir_exists(directory: Path) -> Path:
    """
    Crée un répertoire s'il n'existe pas et le retourne.

    Args:
        directory: Chemin du répertoire à créer.

    Returns:
        Path: Chemin du répertoire créé.
    """
    directory.mkdir(exist_ok=True)
    return directory


def get_temp_dir() -> Path:
    """Retourne le répertoire temporaire et le crée si nécessaire."""
    return _ensure_dir_exists(TEMP_DIR)


def get_sessions_dir() -> Path:
    """Retourne le répertoire des sessions et le crée si nécessaire."""
    return _ensure_dir_exists(SESSIONS_DIR)


def get_logs_dir() -> Path:
    """Retourne le répertoire des logs et le crée si nécessaire."""
    return _ensure_dir_exists(LOGS_DIR)


def get_config_dir() -> Path:
    """Retourne le répertoire de configuration."""
    return CONFIG_DIR


def ensure_all_directories() -> None:
    """Crée tous les répertoires nécessaires à l'application."""
    for directory in [TEMP_DIR, SESSIONS_DIR, LOGS_DIR, CONFIG_DIR,
                      BACKUP_DIR]:
        _ensure_dir_exists(directory)


def get_image_url_path(image_path: str) -> str:
    """
    Convertit un chemin d'image en URL relative pour NiceGUI.
    
    Cette fonction est utilisée pour afficher les images dans l'interface
    web quand l'application est compilée avec PyInstaller.
    
    Args:
        image_path: Chemin absolu vers l'image
        
    Returns:
        str: URL relative pour NiceGUI (ex: "temp/photos/image.jpg")
    """
    if not image_path:
        return ""
    
    try:
        from pathlib import Path
        from utils.logger import get_logger
        
        logger = get_logger()
        path_obj = Path(image_path)
        temp_dir = get_temp_dir()
        
        # Vérifier si le fichier existe
        if not path_obj.exists():
            logger.warning(f"Image introuvable: {image_path}")
            return ""
        
        # Convertir en chemin relatif depuis temp_dir
        try:
            if path_obj.is_relative_to(temp_dir):
                relative_path = path_obj.relative_to(temp_dir)
                url_path = f"temp/{relative_path.as_posix()}"
                logger.debug(f"URL image générée: {url_path}")
                return url_path
        except (ValueError, TypeError):
            # Fallback pour les versions Python < 3.9
            pass
        
        # Comparaison manuelle des chemins
        path_str = str(path_obj)
        temp_str = str(temp_dir)
        
        if path_str.startswith(temp_str):
            # Extraire le chemin relatif
            relative_part = path_str[len(temp_str):]
            relative_part = relative_part.replace('\\', '/').lstrip('/')
            url_path = f"temp/{relative_part}"
            logger.debug(f"URL image générée (manuel): {url_path}")
            return url_path
        
        # Si l'image n'est pas dans temp, retourner le chemin tel quel
        logger.warning(f"Image hors dossier temp: {image_path}")
        return image_path
        
    except Exception as e:
        logger.error(f"Erreur conversion chemin image: {e}")
        return image_path


def get_image_base64_data(image_path: str, max_size_kb: int = 50) -> str:
    """
    Convertit une image en base64 pour l'affichage direct dans l'interface.
    
    Cette fonction est une solution de contournement pour PyInstaller
    quand NiceGUI ne peut pas servir les fichiers statiques.
    
    Args:
        image_path: Chemin vers l'image
        max_size_kb: Taille maximale en KB (par défaut 50KB)
        
    Returns:
        str: Data URL base64 (ex: "data:image/jpeg;base64,/9j/4AAQ...")
    """
    if not image_path:
        return ""
    
    try:
        from pathlib import Path
        import base64
        from PIL import Image
        import io
        from utils.logger import get_logger
        
        logger = get_logger()
        path_obj = Path(image_path)
        
        # Vérifier si le fichier existe
        if not path_obj.exists():
            logger.warning(f"Image introuvable pour base64: {image_path}")
            return ""
        
        # Charger l'image avec PIL
        with Image.open(path_obj) as img:
            # Convertir en RGB si nécessaire
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
                # Redimensionner si l'image est trop grande
                max_dimension = 200  # Maximum 200x200 pixels
                if img.width > max_dimension or img.height > max_dimension:
                    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
                    # CORRECTION : Retirer log debug (performance)
            
            # Optimiser la qualité pour réduire la taille
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=85, optimize=True)
            image_data = output.getvalue()
            
            # Vérifier la taille
            size_kb = len(image_data) / 1024
            if size_kb > max_size_kb:
                # Réduire encore plus la qualité
                output = io.BytesIO()
                img.save(output, format='JPEG', quality=70, optimize=True)
                image_data = output.getvalue()
                size_kb = len(image_data) / 1024
                logger.debug(f"Qualité réduite, nouvelle taille: {size_kb:.1f} KB")
            
            # Convertir en base64
            base64_data = base64.b64encode(image_data).decode('utf-8')
            
            data_url = f"data:image/jpeg;base64,{base64_data}"
            # CORRECTION : Retirer log debug (performance) - génère des milliers de logs
            return data_url
            
    except Exception as e:
        logger.error(f"Erreur conversion image en base64: {e}")
        return ""