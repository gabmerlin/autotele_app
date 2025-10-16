"""
Service de recherche d'utilisateurs Telegram par username.
"""
from typing import Dict, Optional
from telethon.tl.types import User, Chat, Channel

from core.telegram.account import TelegramAccount
from utils.logger import get_logger

logger = get_logger()


class UserSearchService:
    """Service pour rechercher des utilisateurs/canaux par username."""
    
    @staticmethod
    async def search_by_username(
        account: TelegramAccount,
        username: str
    ) -> Optional[Dict]:
        """
        Recherche un utilisateur/canal par username.
        
        Args:
            account: Compte Telegram à utiliser pour la recherche
            username: Username à rechercher (avec ou sans @)
            
        Returns:
            Dict avec les infos formatées comme une conversation, ou None si introuvable
        """
        if not account or not account.is_connected:
            logger.warning("Tentative de recherche avec compte non connecté")
            return None
        
        try:
            # Nettoyer l'username (enlever @ et espaces)
            clean_username = username.lstrip('@').strip()
            
            if not clean_username:
                logger.warning("Username vide après nettoyage")
                return None
            
            # Rechercher l'entité via Telegram
            entity = await account.client.get_entity(clean_username)
            
            # Déterminer le type d'entité
            entity_type = "user"
            title = clean_username
            
            if isinstance(entity, User):
                entity_type = "user"
                # Construire le nom complet
                first_name = getattr(entity, 'first_name', '') or ''
                last_name = getattr(entity, 'last_name', '') or ''
                title = f"{first_name} {last_name}".strip()
                if not title:
                    title = clean_username
                    
            elif isinstance(entity, Channel):
                entity_type = "channel"
                title = getattr(entity, 'title', clean_username)
                
            elif isinstance(entity, Chat):
                entity_type = "group"
                title = getattr(entity, 'title', clean_username)
            
            # Formater comme une conversation standard
            conversation = {
                "id": entity.id,
                "title": title,
                "type": entity_type,
                "entity_id": entity.id,
                "unread_count": 0,
                "last_message": "",
                "last_message_date": None,
                "last_message_from_me": False,
                "pinned": False,
                "archived": False,
                "username": getattr(entity, 'username', None) or clean_username,
                "profile_photo": None,
                "has_photo": False,
            }
            
            logger.info(f"Utilisateur trouvé: {title} (@{clean_username})")
            return conversation
            
        except ValueError as e:
            # Username invalide ou introuvable
            logger.warning(f"Username {username} introuvable: {e}")
            return None
            
        except Exception as e:
            logger.error(f"Erreur recherche username {username}: {e}")
            return None


