"""
Gestionnaire global de notifications pour l'application AutoTele.
Limite le nombre de notifications affichées simultanément à 3 maximum.
"""
from typing import Optional, List, Dict
import time
from nicegui import ui

from utils.logger import get_logger

logger = get_logger()


class NotificationManager:
    """Gestionnaire global des notifications avec limitation."""
    
    _instance: Optional['NotificationManager'] = None
    _active_notifications: List[Dict] = []  # Liste des notifications actives
    _max_notifications: int = 3
    _notification_duration: int = 5  # Durée d'affichage en secondes
    
    def __new__(cls) -> 'NotificationManager':
        """Implémentation du pattern Singleton."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def notify(self, message: str, type: str = 'info') -> None:
        """
        Affiche une notification avec limitation globale.
        
        Args:
            message: Message à afficher
            type: Type de notification ('info', 'positive', 'negative', 'warning')
        """
        # Nettoyer les notifications expirées
        self._cleanup_expired_notifications()
        
        # Vérifier si on peut afficher la notification
        if len(self._active_notifications) >= self._max_notifications:
            return  # Ignorer complètement la notification
        
        try:
            # Afficher la notification
            ui.notify(message, type=type)
            
            # Ajouter à la liste des notifications actives
            notification_info = {
                'message': message,
                'type': type,
                'timestamp': time.time(),
                'id': id(message)  # Utiliser l'id du message comme identifiant unique
            }
            self._active_notifications.append(notification_info)
            
        except Exception as e:
            logger.error(f"Erreur affichage notification: {e}")
    
    def _cleanup_expired_notifications(self) -> None:
        """Supprime les notifications expirées de la liste."""
        current_time = time.time()
        self._active_notifications = [
            notif for notif in self._active_notifications
            if current_time - notif['timestamp'] < self._notification_duration
        ]
    
    def reset_count(self) -> None:
        """Réinitialise le compteur de notifications."""
        self._active_notifications.clear()
    
    def get_count(self) -> int:
        """Retourne le nombre actuel de notifications affichées."""
        self._cleanup_expired_notifications()
        return len(self._active_notifications)
    
    def get_max_notifications(self) -> int:
        """Retourne le nombre maximum de notifications autorisées."""
        return self._max_notifications
    
    def set_max_notifications(self, max_count: int) -> None:
        """
        Définit le nombre maximum de notifications autorisées.
        
        Args:
            max_count: Nombre maximum de notifications (minimum 1)
        """
        if max_count < 1:
            max_count = 1
        self._max_notifications = max_count


# Instance globale
notification_manager = NotificationManager()


def notify(message: str, type: str = 'info') -> None:
    """
    Fonction globale pour afficher des notifications.
    
    Args:
        message: Message à afficher
        type: Type de notification ('info', 'positive', 'negative', 'warning')
    """
    notification_manager.notify(message, type)


def reset_notifications() -> None:
    """Réinitialise le compteur de notifications global."""
    notification_manager.reset_count()


def get_notification_count() -> int:
    """Retourne le nombre actuel de notifications affichées."""
    return notification_manager.get_count()
