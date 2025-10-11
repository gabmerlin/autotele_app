"""
Gestion des credentials API Telegram.
"""
import os
import sys
from pathlib import Path
from typing import Tuple

from utils.logger import get_logger

logger = get_logger()


def get_api_credentials() -> Tuple[int, str]:
    """
    Récupère les credentials API Telegram.
    
    Cherche dans cet ordre:
    1. Variables d'environnement
    2. Fichier config/api_credentials.py
    3. Valeurs par défaut
    
    Returns:
        Tuple[int, str]: (api_id, api_hash)
    """
    # 1. Essayer les variables d'environnement
    env_id = os.getenv("AUTOTELE_API_ID")
    env_hash = os.getenv("AUTOTELE_API_HASH")
    
    if env_id and env_hash:
        try:
            return int(env_id), env_hash
        except ValueError:
            logger.warning("API_ID d'environnement invalide")
    
    # 2. Essayer le fichier de config
    try:
        config_dir = Path(__file__).parent.parent.parent.parent / "config"
        sys.path.insert(0, str(config_dir))
        
        from api_credentials import API_ID, API_HASH
        
        return int(API_ID), API_HASH
    except ImportError:
        logger.warning("Fichier api_credentials.py introuvable, utilisation des valeurs par défaut")
    except Exception as e:
        logger.error(f"Erreur chargement credentials: {e}")
    
    # 3. Valeurs par défaut
    return 21211112, "64342ccdb7588fe8648219265ff5f846"

