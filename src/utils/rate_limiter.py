"""
Module de rate limiting côté client pour éviter les FloodWait.

SÉCURITÉ: Limite le nombre de requêtes API pour éviter les bans temporaires
de Telegram (FloodWaitError).

Limites Telegram officielles :
- 20 messages par seconde dans un même chat
- Pas plus de 30 messages par seconde au total
- Limite augmentée pour les bots/comptes vérifiés
"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple, Optional
import asyncio

from utils.logger import get_logger

logger = get_logger()


class RateLimiter:
    """
    Rate limiter côté client pour les requêtes Telegram.
    
    Implémente l'algorithme du token bucket pour un contrôle précis
    du débit de requêtes.
    """
    
    # Limites par défaut (conservatrices pour éviter les bans)
    DEFAULT_LIMITS = {
        'send_message': (20, 60),      # 20 messages par minute
        'send_file': (10, 60),          # 10 fichiers par minute
        'get_dialogs': (5, 60),         # 5 requêtes par minute
        'get_messages': (30, 60),       # 30 requêtes par minute
        'download_media': (15, 60),     # 15 téléchargements par minute
        'schedule_message': (20, 60),   # 20 messages programmés par minute
    }
    
    def __init__(self, custom_limits: Optional[Dict[str, Tuple[int, int]]] = None):
        """
        Initialise le rate limiter.
        
        Args:
            custom_limits: Limites personnalisées {action: (max_requests, period_seconds)}
        """
        self.limits = {**self.DEFAULT_LIMITS}
        if custom_limits:
            self.limits.update(custom_limits)
        
        # Historique des requêtes par action et identifiant
        # Format: {action:identifier: [timestamp1, timestamp2, ...]}
        self.requests: Dict[str, list] = defaultdict(list)
        
        # Verrouillage pour thread-safety
        self._locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        
        logger.debug("Rate limiter initialisé avec limites conservatrices")
    
    async def check_rate_limit(
        self,
        action: str,
        identifier: str = "global"
    ) -> Tuple[bool, int]:
        """
        Vérifie si une action est autorisée selon les limites de débit.
        
        Args:
            action: Type d'action (ex: 'send_message', 'get_dialogs')
            identifier: Identifiant unique (ex: chat_id, session_id)
        
        Returns:
            Tuple[bool, int]: (is_allowed, wait_seconds)
                - is_allowed: True si l'action est autorisée
                - wait_seconds: Temps d'attente en secondes si refusé
        """
        # Si l'action n'a pas de limite définie, autoriser
        if action not in self.limits:
            return True, 0
        
        max_requests, period_seconds = self.limits[action]
        key = f"{action}:{identifier}"
        
        # Utiliser un lock pour éviter les race conditions
        async with self._locks[key]:
            now = datetime.now()
            cutoff = now - timedelta(seconds=period_seconds)
            
            # Nettoyer les requêtes trop anciennes
            self.requests[key] = [
                ts for ts in self.requests[key]
                if ts > cutoff
            ]
            
            # Vérifier si la limite est atteinte
            if len(self.requests[key]) >= max_requests:
                # Calculer le temps d'attente
                oldest_request = min(self.requests[key])
                wait_until = oldest_request + timedelta(seconds=period_seconds)
                wait_seconds = int((wait_until - now).total_seconds())
                
                logger.warning(
                    f"Rate limit atteint pour {action} ({identifier}): "
                    f"{len(self.requests[key])}/{max_requests} en {period_seconds}s. "
                    f"Attendre {wait_seconds}s"
                )
                
                return False, max(0, wait_seconds)
            
            # Enregistrer la requête
            self.requests[key].append(now)
            
            logger.debug(
                f"Rate limit OK pour {action} ({identifier}): "
                f"{len(self.requests[key])}/{max_requests}"
            )
            
            return True, 0
    
    async def wait_if_needed(
        self,
        action: str,
        identifier: str = "global"
    ) -> bool:
        """
        Attend automatiquement si la limite de débit est atteinte.
        
        ATTENTION: Cette méthode peut bloquer pendant plusieurs secondes.
        
        Args:
            action: Type d'action
            identifier: Identifiant unique
        
        Returns:
            bool: True si l'action peut maintenant être effectuée
        """
        is_allowed, wait_seconds = await self.check_rate_limit(action, identifier)
        
        if not is_allowed and wait_seconds > 0:
            logger.info(
                f"⏳ Attente de {wait_seconds}s pour respecter le rate limit "
                f"({action})"
            )
            await asyncio.sleep(wait_seconds)
            
            # Réessayer après l'attente
            is_allowed, _ = await self.check_rate_limit(action, identifier)
        
        return is_allowed
    
    def get_remaining_requests(
        self,
        action: str,
        identifier: str = "global"
    ) -> int:
        """
        Retourne le nombre de requêtes restantes pour une action.
        
        Args:
            action: Type d'action
            identifier: Identifiant unique
        
        Returns:
            int: Nombre de requêtes restantes (ou -1 si pas de limite)
        """
        if action not in self.limits:
            return -1
        
        max_requests, period_seconds = self.limits[action]
        key = f"{action}:{identifier}"
        
        now = datetime.now()
        cutoff = now - timedelta(seconds=period_seconds)
        
        # Nettoyer les requêtes anciennes
        self.requests[key] = [
            ts for ts in self.requests[key]
            if ts > cutoff
        ]
        
        current_count = len(self.requests[key])
        remaining = max(0, max_requests - current_count)
        
        return remaining
    
    def reset_limit(self, action: str, identifier: str = "global"):
        """
        Réinitialise le compteur pour une action spécifique.
        
        ATTENTION: Utiliser avec précaution. Peut causer des FloodWait.
        
        Args:
            action: Type d'action
            identifier: Identifiant unique
        """
        key = f"{action}:{identifier}"
        self.requests[key] = []
        logger.warning(f"Rate limit réinitialisé pour {action} ({identifier})")
    
    def get_stats(self) -> Dict[str, Dict]:
        """
        Retourne les statistiques du rate limiter.
        
        Returns:
            Dict: Statistiques par action
        """
        stats = {}
        
        for action, (max_req, period) in self.limits.items():
            stats[action] = {
                'limit': max_req,
                'period_seconds': period,
                'active_identifiers': 0,
                'total_requests_tracked': 0
            }
        
        now = datetime.now()
        
        for key, timestamps in self.requests.items():
            if ':' not in key:
                continue
            
            action, _ = key.split(':', 1)
            
            if action in stats:
                # Compter seulement les requêtes récentes
                if action in self.limits:
                    _, period = self.limits[action]
                    cutoff = now - timedelta(seconds=period)
                    recent_requests = [ts for ts in timestamps if ts > cutoff]
                    
                    if recent_requests:
                        stats[action]['active_identifiers'] += 1
                        stats[action]['total_requests_tracked'] += len(recent_requests)
        
        return stats


# Instance globale (singleton)
_rate_limiter_instance: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """
    Récupère l'instance globale du rate limiter.
    
    Returns:
        RateLimiter: Instance du rate limiter
    """
    global _rate_limiter_instance
    
    if _rate_limiter_instance is None:
        _rate_limiter_instance = RateLimiter()
    
    return _rate_limiter_instance


def reset_rate_limiter():
    """Réinitialise l'instance globale (utile pour les tests)."""
    global _rate_limiter_instance
    _rate_limiter_instance = None

