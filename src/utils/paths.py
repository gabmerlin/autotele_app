"""
Gestion centralisée des chemins de l'application.
"""
from pathlib import Path
from typing import Final

# Racine du projet
PROJECT_ROOT: Final[Path] = Path(__file__).parent.parent.parent

# Répertoires principaux
TEMP_DIR: Final[Path] = PROJECT_ROOT / 'temp'
SESSIONS_DIR: Final[Path] = PROJECT_ROOT / 'sessions'
LOGS_DIR: Final[Path] = PROJECT_ROOT / 'logs'
CONFIG_DIR: Final[Path] = PROJECT_ROOT / 'config'
BACKUP_DIR: Final[Path] = PROJECT_ROOT / 'backup'


def get_temp_dir() -> Path:
    """
    Retourne le répertoire temporaire et le crée si nécessaire.
    
    Returns:
        Path: Chemin du répertoire temporaire
    """
    TEMP_DIR.mkdir(exist_ok=True)
    return TEMP_DIR


def get_sessions_dir() -> Path:
    """
    Retourne le répertoire des sessions et le crée si nécessaire.
    
    Returns:
        Path: Chemin du répertoire des sessions
    """
    SESSIONS_DIR.mkdir(exist_ok=True)
    return SESSIONS_DIR


def get_logs_dir() -> Path:
    """
    Retourne le répertoire des logs et le crée si nécessaire.
    
    Returns:
        Path: Chemin du répertoire des logs
    """
    LOGS_DIR.mkdir(exist_ok=True)
    return LOGS_DIR


def get_config_dir() -> Path:
    """
    Retourne le répertoire de configuration.
    
    Returns:
        Path: Chemin du répertoire de configuration
    """
    return CONFIG_DIR


def ensure_all_directories() -> None:
    """Crée tous les répertoires nécessaires à l'application."""
    TEMP_DIR.mkdir(exist_ok=True)
    SESSIONS_DIR.mkdir(exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    CONFIG_DIR.mkdir(exist_ok=True)
    BACKUP_DIR.mkdir(exist_ok=True)

