"""Gestion centralisée des chemins de l'application."""
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

