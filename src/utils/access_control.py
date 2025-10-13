"""
Système de contrôle d'accès strict pour AutoTele
"""
from typing import Callable, Any
from functools import wraps
from nicegui import ui

from services.subscription_service import get_subscription_service
from services.auth_service import get_auth_service
from utils.logger import get_logger

logger = get_logger()


def require_subscription(func: Callable) -> Callable:
    """
    Décorateur qui vérifie l'abonnement avant d'exécuter une fonction.
    
    Si l'utilisateur n'a pas d'abonnement actif, affiche l'écran de souscription.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        auth_service = get_auth_service()
        subscription_service = get_subscription_service()
        
        # Vérifier l'authentification
        if not auth_service.is_authenticated():
            logger.warning("Tentative d'accès sans authentification")
            return
        
        # Récupérer l'ID utilisateur
        user_id = auth_service.get_user_id()
        if not user_id:
            logger.error("Impossible de récupérer l'ID utilisateur")
            return
        
        # Vérifier l'abonnement dans Supabase
        subscription = await subscription_service._load_subscription_from_supabase(user_id)
        
        if not subscription:
            logger.warning(f"Utilisateur {user_id} tente d'accéder sans abonnement actif")
            # Afficher l'écran de souscription
            await _show_subscription_required()
            return
        
        # Abonnement valide, exécuter la fonction
        return await func(*args, **kwargs)
    
    return wrapper


def require_auth_and_subscription(func: Callable) -> Callable:
    """
    Décorateur qui vérifie l'authentification ET l'abonnement.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        auth_service = get_auth_service()
        
        # Vérifier l'authentification
        if not auth_service.is_authenticated():
            logger.warning("Tentative d'accès sans authentification")
            # Rediriger vers la connexion
            return
        
        # Vérifier l'abonnement
        subscription_service = get_subscription_service()
        user_id = auth_service.get_user_id()
        
        if user_id:
            subscription = await subscription_service._load_subscription_from_supabase(user_id)
            if not subscription:
                await _show_subscription_required()
                return
        
        return await func(*args, **kwargs)
    
    return wrapper


async def _show_subscription_required():
    """Affiche l'écran de souscription requis - délègue à app.py"""
    # Ne pas afficher de popup ici, laisser app.py gérer l'affichage
    # Cette fonction est appelée par le décorateur mais on délègue à app.py
    pass


class AccessController:
    """Contrôleur d'accès centralisé"""
    
    def __init__(self):
        self.auth_service = get_auth_service()
        self.subscription_service = get_subscription_service()
    
    async def check_access(self) -> bool:
        """
        Vérifie si l'utilisateur a accès à l'application.
        
        Returns:
            True si l'utilisateur est authentifié et a un abonnement actif
        """
        # Vérifier l'authentification
        if not self.auth_service.is_authenticated():
            return False
        
        # Vérifier l'abonnement
        user_id = self.auth_service.get_user_id()
        if not user_id:
            return False
        
        subscription = await self.subscription_service._load_subscription_from_supabase(user_id)
        return subscription is not None
    
    async def get_user_subscription_info(self) -> dict:
        """
        Récupère les informations d'abonnement de l'utilisateur connecté.
        
        Returns:
            Dict avec les infos d'abonnement ou None si pas d'abonnement
        """
        if not self.auth_service.is_authenticated():
            return None
        
        user_id = self.auth_service.get_user_id()
        if not user_id:
            return None
        
        return await self.subscription_service._load_subscription_from_supabase(user_id)


# Instance globale du contrôleur d'accès
_access_controller = None

def get_access_controller() -> AccessController:
    """Retourne l'instance globale du contrôleur d'accès"""
    global _access_controller
    if _access_controller is None:
        _access_controller = AccessController()
    return _access_controller
