"""
Système d'updates en temps réel pour la messagerie.
Utilise les événements Telethon pour mettre à jour la DB automatiquement.
"""
import asyncio
from datetime import datetime
from typing import Dict, Optional, Callable, Set
from telethon import events
from telethon.tl.types import User, Chat, Channel

from core.telegram.account import TelegramAccount
from database.telegram_db import get_telegram_db
from utils.logger import get_logger

logger = get_logger()


class RealtimeUpdates:
    """
    Gestionnaire d'updates en temps réel.
    
    Écoute les événements Telethon et met à jour la base de données
    automatiquement pour garder les conversations à jour sans rechargement.
    """
    
    def __init__(self):
        """Initialise le gestionnaire d'updates."""
        self.db = get_telegram_db()
        self._active_handlers: Dict[str, Set] = {}  # {session_id: {handlers}}
        self._ui_callbacks: Dict[str, Callable] = {}  # {event_type: callback}
    
    def setup_handlers(self, account: TelegramAccount):
        """
        Configure les gestionnaires d'événements pour un compte.
        
        Args:
            account: Compte Telegram
        """
        if not account or not account.is_connected or not account.client:
            return
        
        session_id = account.session_id
        
        # Éviter de recréer les handlers si déjà configurés
        if session_id in self._active_handlers:
            logger.debug(f"Handlers déjà configurés pour {session_id}")
            return
        
        self._active_handlers[session_id] = set()
        
        # Handler 1: Nouveaux messages
        @account.client.on(events.NewMessage(incoming=True))
        async def on_new_message(event):
            await self._handle_new_message(account, event)
        
        # Handler 2: Messages édités
        @account.client.on(events.MessageEdited())
        async def on_message_edited(event):
            await self._handle_message_edited(account, event)
        
        # Handler 3: Messages lus
        @account.client.on(events.MessageRead())
        async def on_message_read(event):
            await self._handle_message_read(account, event)
        
        # Handler 4: Changements de chat (titre, photo, etc.)
        @account.client.on(events.ChatAction())
        async def on_chat_action(event):
            await self._handle_chat_action(account, event)
        
        # Stocker les références aux handlers
        self._active_handlers[session_id].add(on_new_message)
        self._active_handlers[session_id].add(on_message_edited)
        self._active_handlers[session_id].add(on_message_read)
        self._active_handlers[session_id].add(on_chat_action)
        
        logger.info(f"Handlers temps réel configurés pour {account.account_name}")
    
    def remove_handlers(self, account: TelegramAccount):
        """
        Supprime les gestionnaires d'événements d'un compte.
        
        Args:
            account: Compte Telegram
        """
        session_id = account.session_id
        
        if session_id in self._active_handlers:
            # Telethon supprime automatiquement les handlers quand on les perd
            del self._active_handlers[session_id]
            logger.info(f"Handlers supprimés pour {account.account_name}")
    
    def register_ui_callback(self, event_type: str, callback: Callable):
        """
        Enregistre un callback pour notifier l'UI des updates.
        
        Args:
            event_type: Type d'événement ('new_message', 'message_edited', etc.)
            callback: Fonction à appeler
        """
        self._ui_callbacks[event_type] = callback
    
    async def _handle_new_message(self, account: TelegramAccount, event):
        """
        Gère l'arrivée d'un nouveau message.
        
        Args:
            account: Compte Telegram
            event: Événement Telethon
        """
        try:
            message = event.message
            chat_id = event.chat_id
            
            # Infos expéditeur
            sender_name = "Inconnu"
            sender_id = None
            
            if message.sender:
                sender_id = message.sender.id
                if hasattr(message.sender, 'first_name'):
                    sender_name = message.sender.first_name or ""
                    if hasattr(message.sender, 'last_name') and message.sender.last_name:
                        sender_name += f" {message.sender.last_name}"
                elif hasattr(message.sender, 'title'):
                    sender_name = message.sender.title
            
            # Texte
            message_text = message.text or message.message or ""
            if message.media:
                media_type = type(message.media).__name__
                if media_type == 'MessageMediaPhoto':
                    message_text = "[Photo]"
                elif 'Document' in media_type:
                    message_text = "[Document]"
                else:
                    message_text = "[Média]"
            
            # Média
            media_type = None
            media_caption = ""
            
            if message.media:
                media_type = type(message.media).__name__
                if hasattr(message.media, 'caption') and message.media.caption:
                    media_caption = message.media.caption
                elif hasattr(message, 'caption') and message.caption:
                    media_caption = message.caption
            
            # Date
            if message.date.tzinfo is not None:
                local_date = message.date.astimezone().replace(tzinfo=None)
            else:
                local_date = message.date
            
            # Créer le dictionnaire du message
            msg_dict = {
                "id": message.id,
                "text": message_text,
                "date": local_date,
                "from_me": message.out,
                "sender_id": sender_id,
                "sender_name": sender_name,
                "has_media": message.media is not None,
                "media_type": media_type,
                "media_data": None,
                "media_caption": media_caption,
                "reply_to": message.reply_to_msg_id,
                "edited": False,
                "views": getattr(message, 'views', None),
            }
            
            # Sauvegarder dans la DB
            self.db.save_messages(account.session_id, chat_id, [msg_dict])
            
            # Mettre à jour la conversation
            self.db.update_conversation_last_message(
                chat_id,
                account.session_id,
                message_text[:100],
                local_date,
                from_me=False
            )
            
            # Incrémenter unread_count
            self.db.conn.execute("""
                UPDATE conversations
                SET unread_count = unread_count + 1
                WHERE entity_id = ? AND session_id = ?
            """, (chat_id, account.session_id))
            
            # Notifier l'UI
            if 'new_message' in self._ui_callbacks:
                try:
                    self._ui_callbacks['new_message'](msg_dict, chat_id)
                except Exception as e:
                    logger.error(f"Erreur callback UI new_message: {e}")
            
            logger.debug(f"Nouveau message reçu et sauvegardé : chat {chat_id}")
        
        except Exception as e:
            logger.error(f"Erreur traitement nouveau message: {e}")
    
    async def _handle_message_edited(self, account: TelegramAccount, event):
        """
        Gère l'édition d'un message.
        
        Args:
            account: Compte Telegram
            event: Événement Telethon
        """
        try:
            message = event.message
            chat_id = event.chat_id
            
            # Texte modifié
            message_text = message.text or message.message or ""
            
            # Mettre à jour dans la DB
            self.db.conn.execute("""
                UPDATE messages
                SET text = ?, edited = 1
                WHERE id = ? AND chat_id = ? AND session_id = ?
            """, (message_text, message.id, chat_id, account.session_id))
            
            # Notifier l'UI
            if 'message_edited' in self._ui_callbacks:
                try:
                    self._ui_callbacks['message_edited'](message.id, chat_id, message_text)
                except Exception as e:
                    logger.error(f"Erreur callback UI message_edited: {e}")
            
            logger.debug(f"Message édité : {message.id} dans chat {chat_id}")
        
        except Exception as e:
            logger.error(f"Erreur traitement message édité: {e}")
    
    async def _handle_message_read(self, account: TelegramAccount, event):
        """
        Gère la lecture de messages.
        
        Args:
            account: Compte Telegram
            event: Événement Telethon
        """
        try:
            chat_id = event.chat_id
            
            # Réinitialiser unread_count
            self.db.conn.execute("""
                UPDATE conversations
                SET unread_count = 0
                WHERE entity_id = ? AND session_id = ?
            """, (chat_id, account.session_id))
            
            # Notifier l'UI
            if 'messages_read' in self._ui_callbacks:
                try:
                    self._ui_callbacks['messages_read'](chat_id)
                except Exception as e:
                    logger.error(f"Erreur callback UI messages_read: {e}")
            
            logger.debug(f"Messages lus : chat {chat_id}")
        
        except Exception as e:
            logger.error(f"Erreur traitement messages lus: {e}")
    
    async def _handle_chat_action(self, account: TelegramAccount, event):
        """
        Gère les actions dans un chat (changement titre, photo, etc.).
        
        Args:
            account: Compte Telegram
            event: Événement Telethon
        """
        try:
            chat_id = event.chat_id
            
            # Récupérer les infos à jour du chat
            chat = await event.get_chat()
            
            if not chat:
                return
            
            # Mise à jour du titre
            if hasattr(event, 'new_title') and event.new_title:
                self.db.conn.execute("""
                    UPDATE conversations
                    SET title = ?
                    WHERE entity_id = ? AND session_id = ?
                """, (event.new_title, chat_id, account.session_id))
                
                logger.debug(f"Titre de chat mis à jour : {event.new_title}")
            
            # Mise à jour de la photo
            if hasattr(event, 'new_photo') and event.new_photo:
                # Invalider le cache de photo
                # La nouvelle photo sera téléchargée lors du prochain affichage
                self.db.conn.execute("""
                    UPDATE conversations
                    SET profile_photo_path = NULL, has_photo = 1
                    WHERE entity_id = ? AND session_id = ?
                """, (chat_id, account.session_id))
                
                logger.debug(f"Photo de chat modifiée : chat {chat_id}")
            
            # Notifier l'UI
            if 'chat_action' in self._ui_callbacks:
                try:
                    self._ui_callbacks['chat_action'](chat_id, event)
                except Exception as e:
                    logger.error(f"Erreur callback UI chat_action: {e}")
        
        except Exception as e:
            logger.error(f"Erreur traitement action chat: {e}")
    
    def get_stats(self) -> Dict:
        """
        Récupère les statistiques des handlers actifs.
        
        Returns:
            Dict: Statistiques
        """
        return {
            'active_sessions': len(self._active_handlers),
            'total_handlers': sum(len(handlers) for handlers in self._active_handlers.values()),
            'ui_callbacks': len(self._ui_callbacks)
        }


# Instance globale
_realtime_updates_instance = None


def get_realtime_updates() -> RealtimeUpdates:
    """
    Récupère l'instance globale du gestionnaire d'updates.
    
    Returns:
        RealtimeUpdates: Instance du gestionnaire
    """
    global _realtime_updates_instance
    if _realtime_updates_instance is None:
        _realtime_updates_instance = RealtimeUpdates()
    return _realtime_updates_instance

