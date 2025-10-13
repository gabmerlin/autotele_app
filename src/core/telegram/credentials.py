"""Gestion des credentials API Telegram."""
import os
import sys
from pathlib import Path
from typing import Tuple

from dotenv import load_dotenv

from utils.logger import get_logger

logger = get_logger()

# Charger le fichier .env dès l'import de ce module
ENV_PATH = Path(__file__).parent.parent.parent.parent / '.env'
load_dotenv(dotenv_path=ENV_PATH)


def get_api_credentials() -> Tuple[int, str]:
    """
    Récupère les credentials API Telegram.

    Cherche dans cet ordre:
    1. Variables d'environnement (RECOMMANDÉ)
    2. Fichier config/api_credentials.py

    IMPORTANT : Ne fournit AUCUNE valeur par défaut pour des raisons
    de sécurité. Les credentials doivent être explicitement définis.

    Returns:
        Tuple[int, str]: (api_id, api_hash)

    Raises:
        ValueError: Si les credentials ne sont pas configurés.
    """
    # 1. Essayer les variables d'environnement
    env_id = os.getenv("AUTOTELE_API_ID")
    env_hash = os.getenv("AUTOTELE_API_HASH")

    if env_id and env_hash:
        try:
            return int(env_id), env_hash
        except ValueError:
            logger.error(
                "API_ID d'environnement invalide (doit être un nombre)"
            )
            raise ValueError("API_ID doit être un nombre valide")

    # 2. Essayer le fichier de config
    try:
        config_dir = (
            Path(__file__).parent.parent.parent.parent / "config"
        )
        sys.path.insert(0, str(config_dir))

        from api_credentials import API_HASH, API_ID

        if API_ID and API_HASH:
            return int(API_ID), API_HASH
    except ImportError:
        logger.warning("Fichier api_credentials.py introuvable")
    except ValueError as e:
        logger.error(f"Erreur validation credentials: {e}")
        raise
    except Exception as e:
        logger.error(f"Erreur chargement credentials: {e}")

    # 3. AUCUNE valeur par défaut - ÉCHEC SÉCURISÉ
    error_msg = (
        "ERREUR : Credentials API Telegram non configurés.\n\n"
        "Configuration requise :\n"
        "1. Créez un fichier .env à la racine du projet\n"
        "2. Ajoutez vos credentials (https://my.telegram.org) :\n"
        "   AUTOTELE_API_ID=votre_api_id\n"
        "   AUTOTELE_API_HASH=votre_api_hash\n\n"
        "Voir .env.example pour un modèle"
    )
    logger.error(error_msg)
    raise ValueError(error_msg)

