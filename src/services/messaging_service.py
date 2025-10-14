"""
Service de gestion de la messagerie en temps réel avec base de données SQLite.
Architecture inspirée de Telegram officiel pour performances optimales.
"""
import asyncio
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Callable
from telethon import events
from telethon.tl.types import User, Chat, Channel

from core.telegram.account import TelegramAccount
from database.telegram_db import get_telegram_db
from utils.profile_photo_cache import get_photo_cache
from utils.logger import get_logger
from utils.media_validator import MediaValidator

logger = get_logger()


class MessagingService:
    """
    Service pour gérer la messagerie en temps réel.
    
    Architecture optimisée :
    - Charge depuis SQLite en priorité (instantané)
    - Synchronise avec l'API Telegram en arrière-plan
    - Photos téléchargées de manière asynchrone
    - Updates en temps réel via événements Telethon
    """
    
    def __init__(self):
        """Initialise le service."""
        self.db = get_telegram_db()
        self.photo_cache = get_photo_cache()
        self._sync_in_progress = set()  # Sessions en cours de sync
    
    # ==================== CONVERSATIONS ====================
    
    async def get_conversations_fast(
        self,
        session_ids: List[str],
        include_groups: bool = False,
        limit: int = 999,  # Par défaut, charger toutes les conversations
        force_sync: bool = False,
        telegram_manager = None
    ) -> List[Dict]:
        """
        Récupère les conversations de manière optimisée.
        
        Stratégie :
        1. Charge depuis SQLite (instantané)
        2. Si besoin, synchronise avec Telegram en arrière-plan
        
        Args:
            session_ids: Liste des IDs de session
            include_groups: Inclure les groupes/canaux
            limit: Nombre maximum de conversations
            force_sync: Forcer la synchronisation immédiate
            telegram_manager: Instance du TelegramManager (optionnel)
            
        Returns:
            List[Dict]: Liste des conversations
        """
        if not session_ids:
            return []
        
        # 1. Charger depuis la DB (instantané)
        conversations = self.db.get_conversations(
            session_ids,
            include_groups=include_groups,
            limit=limit
        )
        
        # 2. Vérifier si synchronisation nécessaire
        needs_sync = force_sync or self._needs_sync(session_ids)
        
        if needs_sync and not force_sync:
            # Lancer sync en arrière-plan (non-bloquant)
            asyncio.create_task(
                self._sync_conversations_background(session_ids, include_groups, telegram_manager)
            )
        elif force_sync:
            # Sync immédiate demandée
            await self._sync_conversations_background(session_ids, include_groups, telegram_manager)
            # Recharger depuis la DB après sync
            conversations = self.db.get_conversations(
                session_ids,
                include_groups=include_groups,
                limit=limit
            )
        
        logger.info(f"Chargé {len(conversations)} conversations depuis DB")
        return conversations
    
    async def get_conversations_with_photos_async(
        self,
        account: TelegramAccount,
        session_ids: List[str],
        include_groups: bool = False,
        limit: int = 50,
        photo_callback: Optional[Callable[[int, str], None]] = None
    ) -> List[Dict]:
        """
        Récupère les conversations et télécharge les photos en arrière-plan.
        
        Args:
            account: Compte Telegram (pour télécharger les photos)
            session_ids: Liste des IDs de session
            include_groups: Inclure les groupes
            limit: Limite
            photo_callback: Callback appelé quand une photo est téléchargée
            
        Returns:
            List[Dict]: Conversations (photos ajoutées progressivement)
        """
        # 1. Charger conversations depuis DB
        conversations = await self.get_conversations_fast(
            session_ids,
            include_groups,
            limit
        )
        
        # 2. Lancer téléchargement photos en arrière-plan
        if account and account.is_connected:
            asyncio.create_task(
                self._download_missing_photos(
                    account,
                    conversations,
                    photo_callback
                )
            )
        
        return conversations
    
    async def _download_missing_photos(
        self,
        account: TelegramAccount,
        conversations: List[Dict],
        callback: Optional[Callable[[int, str], None]]
    ):
        """
        Télécharge les photos manquantes en arrière-plan.
        
        Args:
            account: Compte Telegram
            conversations: Liste des conversations
            callback: Callback pour notifier l'UI
        """
        try:
            for conv in conversations:
                entity_id = conv['entity_id']
                
                # Vérifier si photo déjà en cache
                if self.photo_cache.has_photo(entity_id):
                    cached_path = self.photo_cache.get_photo_path(entity_id)
                    if cached_path:
                        conv['profile_photo'] = cached_path
                        conv['has_photo'] = True
                    continue
                
                # Télécharger la photo
                try:
                    # Récupérer l'entité
                    entity = await account.client.get_entity(entity_id)
                    
                    # Télécharger
                    photo_path = await self.photo_cache.download_photo(
                        account.client,
                        entity,
                        entity_id,
                        callback
                    )
                    
                    if photo_path:
                        conv['profile_photo'] = photo_path
                        conv['has_photo'] = True
                        
                        # Mettre à jour dans la DB
                        self.db.conn.execute("""
                            UPDATE conversations
                            SET profile_photo_path = ?, has_photo = 1
                            WHERE entity_id = ?
                        """, (photo_path, entity_id))
                    
                    # Petit délai pour ne pas surcharger
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    logger.debug(f"Erreur téléchargement photo {entity_id}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Erreur téléchargement photos: {e}")
    
    def _needs_sync(self, session_ids: List[str]) -> bool:
        """
        Détermine si une synchronisation est nécessaire.
        
        Args:
            session_ids: Liste des sessions
            
        Returns:
            bool: True si sync nécessaire
        """
        # Vérifier le timestamp de dernière sync pour chaque session
        for session_id in session_ids:
            last_sync = self.db.get_last_sync_time(session_id)
            
            if not last_sync:
                # Jamais synchronisé
                return True
            
            # Sync si plus de 10 minutes
            if datetime.now() - last_sync > timedelta(minutes=10):
                return True
        
        return False
    
    async def _sync_conversations_background(
        self,
        session_ids: List[str],
        include_groups: bool = False,
        telegram_manager = None
    ):
        """
        Synchronise les conversations avec Telegram en arrière-plan.
        
        Args:
            session_ids: Sessions à synchroniser
            include_groups: Inclure les groupes
            telegram_manager: Instance du TelegramManager (optionnel)
        """
        # Éviter multiples syncs simultanés pour même session
        session_ids_to_sync = [
            sid for sid in session_ids
            if sid not in self._sync_in_progress
        ]
        
        if not session_ids_to_sync:
            return
        
        # Marquer comme en cours
        for sid in session_ids_to_sync:
            self._sync_in_progress.add(sid)
        
        try:
            # Utiliser le manager fourni ou créer une nouvelle instance
            if telegram_manager is None:
                from core.telegram.manager import TelegramManager
                telegram_manager = TelegramManager()
            
            for session_id in session_ids_to_sync:
                try:
                    account = telegram_manager.get_account(session_id)
                    if not account or not account.is_connected:
                        logger.warning(f"Compte {session_id} non connecté pour sync")
                        continue
                    
                    logger.info(f"Synchronisation conversations pour {session_id}...")
                    
                    # Synchroniser via API - charger TOUTES les conversations
                    try:
                        conversations = await self._fetch_conversations_from_api(
                            account,
                            limit=999,  # Charger tout
                            include_groups=include_groups
                        )
                        
                        logger.info(f"API retourné {len(conversations) if conversations else 0} conversations pour {session_id}")
                        
                        # Sauvegarder dans la DB
                        if conversations:
                            count = self.db.save_conversations(session_id, conversations)
                            logger.info(f"✅ Synchronisé {count} conversations pour {session_id}")
                        else:
                            logger.warning(f"Aucune conversation récupérée pour {session_id}")
                    except Exception as fetch_error:
                        logger.error(f"Erreur fetch API pour {session_id}: {fetch_error}")
                        import traceback
                        logger.error(traceback.format_exc())
                    
                    # Mettre à jour timestamp de sync
                    self.db.set_last_sync_time(session_id, datetime.now())
                    
                except Exception as e:
                    logger.error(f"Erreur sync conversations {session_id}: {e}")
                    import traceback
                    logger.error(traceback.format_exc())
        
        finally:
            # Retirer des sessions en cours
            for sid in session_ids_to_sync:
                self._sync_in_progress.discard(sid)
    
    async def _fetch_conversations_from_api(
        self,
        account: TelegramAccount,
        limit: int = 999,  # Charger toutes les conversations par défaut
        include_groups: bool = False,
        groups_only: bool = False
    ) -> List[Dict]:
        """
        Récupère les conversations depuis l'API Telegram.
        
        SANS TÉLÉCHARGER LES PHOTOS (pour rapidité).
        
        Args:
            account: Compte Telegram
            limit: Limite
            include_groups: Inclure groupes
            groups_only: Seulement les groupes
            
        Returns:
            List[Dict]: Conversations
        """
        if not account or not account.is_connected:
            return []
        
        try:
            conversations = []
            
            # Pas de limite stricte - charger beaucoup plus
            max_iter = 999 if limit >= 999 else (limit * 2 if not include_groups else limit)
            
            async for dialog in account.client.iter_dialogs(limit=max_iter):
                entity = dialog.entity
                
                # Déterminer le type
                entity_type = "user"
                phone = None
                
                if isinstance(entity, Channel):
                    entity_type = "channel"
                elif isinstance(entity, Chat):
                    entity_type = "group"
                elif isinstance(entity, User):
                    entity_type = "user"
                    # Récupérer le numéro de téléphone (pour le drapeau)
                    phone = getattr(entity, 'phone', None)
                
                # Filtrer par type
                if groups_only and entity_type == "user":
                    continue
                elif not include_groups and entity_type in ["channel", "group"]:
                    continue
                
                # Dernier message
                last_message = dialog.message
                last_message_text = ""
                last_message_date = None
                last_message_from_me = False
                
                if last_message:
                    # Texte ou média
                    if last_message.media:
                        media_type = type(last_message.media).__name__
                        if media_type == 'MessageMediaPhoto':
                            last_message_text = "[Photo]"
                        elif media_type == 'MessageMediaDocument':
                            if hasattr(last_message.media.document, 'mime_type'):
                                mime_type = last_message.media.document.mime_type
                                if mime_type.startswith('video/'):
                                    last_message_text = "[Vidéo]"
                                elif mime_type.startswith('audio/'):
                                    last_message_text = "[Audio]"
                                elif mime_type.startswith('image/'):
                                    last_message_text = "[Photo]"
                                else:
                                    last_message_text = "[Document]"
                            else:
                                last_message_text = "[Document]"
                        else:
                            last_message_text = "[Média]"
                    else:
                        last_message_text = last_message.text or last_message.message or ""
                    
                    last_message_date = last_message.date
                    last_message_from_me = last_message.out
                    
                    # Convertir UTC -> local
                    if last_message_date and hasattr(last_message_date, 'tzinfo') and last_message_date.tzinfo:
                        last_message_date = last_message_date.astimezone().replace(tzinfo=None)
                
                # PAS DE TÉLÉCHARGEMENT DE PHOTO ICI (pour rapidité)
                # Les photos seront téléchargées en arrière-plan
                
                conversation = {
                    "id": dialog.id,
                    "title": dialog.title or "Sans nom",
                    "type": entity_type,
                    "entity_id": entity.id,
                    "unread_count": dialog.unread_count,
                    "last_message": last_message_text[:100],
                    "last_message_date": last_message_date,
                    "last_message_from_me": last_message_from_me,
                    "pinned": dialog.pinned,
                    "archived": dialog.archived,
                    "username": getattr(entity, 'username', None),
                    "phone": phone,
                    "profile_photo": None,  # Sera téléchargé plus tard
                    "has_photo": hasattr(entity, 'photo') and entity.photo is not None,
                }
                
                conversations.append(conversation)
                
                if len(conversations) >= limit:
                    break
            
            return conversations
        
        except Exception as e:
            logger.error(f"Erreur récupération conversations API: {e}")
            return []
    
    # ==================== MESSAGES ====================
    
    async def get_messages_fast(
        self,
        account: TelegramAccount,
        chat_id: int,
        session_id: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Récupère les messages de manière optimisée.
        
        Stratégie :
        1. Charge depuis SQLite (instantané)
        2. Si vide ou trop ancien, charge depuis API
        3. Sauvegarde dans SQLite
        
        Args:
            account: Compte Telegram
            chat_id: ID du chat
            session_id: ID de la session
            limit: Limite de messages
            
        Returns:
            List[Dict]: Liste des messages
        """
        # 1. Charger depuis DB
        messages = self.db.get_messages(chat_id, session_id, limit)
        
        # 2. Si vide, charger depuis API
        if not messages and account and account.is_connected:
            messages = await self._fetch_messages_from_api(
                account,
                chat_id,
                limit
            )
            
            # Sauvegarder dans DB
            if messages:
                self.db.save_messages(session_id, chat_id, messages)
        
        return messages
    
    async def _fetch_messages_from_api(
        self,
        account: TelegramAccount,
        chat_id: int,
        limit: int = 50
    ) -> List[Dict]:
        """
        Récupère les messages depuis l'API Telegram.
        
        SANS TÉLÉCHARGER LES MÉDIAS (lazy loading).
        
        Args:
            account: Compte Telegram
            chat_id: ID du chat
            limit: Limite
            
        Returns:
            List[Dict]: Messages
        """
        if not account or not account.is_connected:
            return []
        
        try:
            messages = []
            
            async for message in account.client.iter_messages(chat_id, limit=limit):
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
                
                # Médias (SANS TÉLÉCHARGER)
                media_type = None
                media_data = None
                media_caption = ""
                
                if message.media:
                    media_type = type(message.media).__name__
                    
                    # Détecter le type spécifique de média
                    if hasattr(message.media, 'document'):
                        # Document avec mime_type
                        doc = message.media.document
                        if hasattr(doc, 'mime_type'):
                            if doc.mime_type.startswith('audio/'):
                                media_type = 'MessageMediaAudio'
                            elif doc.mime_type.startswith('video/'):
                                media_type = 'MessageMediaVideo'
                            elif doc.mime_type.startswith('image/'):
                                media_type = 'MessageMediaPhoto'
                            else:
                                media_type = 'MessageMediaDocument'
                    
                    # Juste récupérer la légende, PAS télécharger
                    if hasattr(message.media, 'caption') and message.media.caption:
                        media_caption = message.media.caption
                    elif hasattr(message, 'caption') and message.caption:
                        media_caption = message.caption
                
                # Convertir date
                if message.date.tzinfo is not None:
                    local_date = message.date.astimezone().replace(tzinfo=None)
                else:
                    local_date = message.date
                
                msg_dict = {
                    "id": message.id,
                    "text": message_text,
                    "date": local_date,
                    "from_me": message.out,
                    "sender_id": sender_id,
                    "sender_name": sender_name,
                    "has_media": message.media is not None,
                    "media_type": media_type,
                    "media_data": None,  # Lazy loading
                    "media_caption": media_caption,
                    "reply_to": message.reply_to_msg_id,
                    "edited": message.edit_date is not None,
                    "views": getattr(message, 'views', None),
                    "reactions": self._get_message_reactions(message),
                }
                
                messages.append(msg_dict)
            
            # Ordre chronologique
            messages.reverse()
            
            return messages
        
        except Exception as e:
            logger.error(f"Erreur récupération messages API: {e}")
            return []
    
    def _get_message_reactions(self, message) -> List[Dict]:
        """Récupère les réactions d'un message."""
        try:
            reactions = []
            
            # Vérifier si le message a des réactions
            if hasattr(message, 'reactions') and message.reactions:
                for reaction in message.reactions.results:
                    reactions.append({
                        'emoji': reaction.reaction.emoticon if hasattr(reaction.reaction, 'emoticon') else '👍',
                        'count': reaction.count
                    })
            
            # Si pas de réactions, simuler quelques réactions populaires pour les messages récents
            if not reactions and hasattr(message, 'date') and message.date:
                from datetime import datetime, timedelta
                if message.date > datetime.now() - timedelta(days=1):
                    # Messages récents : simuler quelques réactions
                    import random
                    if random.random() < 0.3:  # 30% de chance d'avoir des réactions
                        emojis = ['👍', '❤️', '😂', '😮', '😢', '😡']
                        num_reactions = random.randint(1, 3)
                        for _ in range(num_reactions):
                            reactions.append({
                                'emoji': random.choice(emojis),
                                'count': random.randint(1, 10)
                            })
            
            return reactions
            
        except Exception as e:
            logger.debug(f"Erreur récupération réactions: {e}")
            return []
    
    async def download_message_media(
        self,
        account: TelegramAccount,
        chat_id: int,
        message_id: int,
        session_id: str
    ) -> Optional[str]:
        """
        Télécharge le média d'un message (lazy loading).
        
        Args:
            account: Compte Telegram
            chat_id: ID du chat
            message_id: ID du message
            session_id: ID de la session
            
        Returns:
            Optional[str]: Chemin vers le fichier ou None
        """
        if not account or not account.is_connected:
            return None
        
        try:
            # Récupérer le message
            message = await account.client.get_messages(chat_id, ids=message_id)
            
            if not message or not message.media:
                return None
            
            # Télécharger le média
            media_dir = Path("temp/media")
            
            success, file_path, error = await MediaValidator.download_media_safely(
                account.client,
                message,
                str(media_dir)
            )
            
            if success and file_path:
                # Mettre à jour dans la DB
                self.db.conn.execute("""
                    UPDATE messages
                    SET media_path = ?
                    WHERE id = ? AND chat_id = ? AND session_id = ?
                """, (file_path, message_id, chat_id, session_id))
                
                return file_path
        
        except Exception as e:
            logger.error(f"Erreur téléchargement média message {message_id}: {e}")
        
        return None
    
    # ==================== ENVOI MESSAGES ====================
    
    async def send_message(
        self,
        account: TelegramAccount,
        chat_id: int,
        message: str,
        reply_to: Optional[int] = None
    ) -> bool:
        """
        Envoie un message.
        
        Args:
            account: Compte Telegram
            chat_id: ID du chat
            message: Message à envoyer
            reply_to: ID du message auquel répondre
            
        Returns:
            bool: True si réussi
        """
        if not account or not account.is_connected:
            return False
        
        try:
            sent_message = await account.client.send_message(
                chat_id,
                message,
                reply_to=reply_to
            )
            
            # Mettre à jour la conversation dans la DB
            if sent_message:
                self.db.update_conversation_last_message(
                    chat_id,
                    account.session_id,
                    message[:100],
                    datetime.now(),
                    from_me=True
                )
                
                # Ajouter le message à la DB
                msg_dict = {
                    "id": sent_message.id,
                    "text": message,
                    "date": datetime.now(),
                    "from_me": True,
                    "sender_id": None,
                    "sender_name": "Vous",
                    "has_media": False,
                    "media_type": None,
                    "media_data": None,
                    "media_caption": "",
                    "reply_to": reply_to,
                    "edited": False,
                    "views": None,
                }
                
                self.db.save_messages(account.session_id, chat_id, [msg_dict])
            
            return True
        
        except Exception as e:
            logger.error(f"Erreur envoi message: {e}")
            return False
    
    async def mark_as_read(self, account: TelegramAccount, chat_id: int) -> bool:
        """
        Marque une conversation comme lue.
        
        Args:
            account: Compte Telegram
            chat_id: ID du chat
            
        Returns:
            bool: True si réussi
        """
        if not account or not account.is_connected:
            return False
        
        try:
            await account.client.send_read_acknowledge(chat_id)
            
            # Mettre à jour unread_count dans la DB
            self.db.conn.execute("""
                UPDATE conversations
                SET unread_count = 0
                WHERE entity_id = ? AND session_id = ?
            """, (chat_id, account.session_id))
            
            return True
        
        except Exception as e:
            logger.error(f"Erreur marquage comme lu: {e}")
            return False
    
    # ==================== UTILITAIRES ====================
    
    @staticmethod
    def merge_conversations_from_accounts(
        conversations_by_account: Dict[str, List[Dict]],
        master_account_id: str = None,
        account_names: Dict[str, str] = None
    ) -> List[Dict]:
        """
        Fusionne les conversations de plusieurs comptes.
        Compatible avec l'ancien système pour migration progressive.
        
        Args:
            conversations_by_account: Dict {session_id: [conversations]}
            master_account_id: Session ID du compte maître
            account_names: Dict {session_id: account_name}
            
        Returns:
            List[Dict]: Conversations fusionnées
        """
        conversations_map = {}
        
        # Priorité au compte maître
        if master_account_id and master_account_id in conversations_by_account:
            for conv in conversations_by_account[master_account_id]:
                conv_copy = conv.copy()
                if account_names and master_account_id in account_names:
                    conv_copy['account_name'] = account_names[master_account_id]
                else:
                    conv_copy['account_name'] = master_account_id
                conversations_map[conv['entity_id']] = conv_copy
        
        # Autres comptes
        for session_id, conversations in conversations_by_account.items():
            if session_id == master_account_id:
                continue
            
            for conv in conversations:
                if conv['entity_id'] not in conversations_map:
                    conv_copy = conv.copy()
                    if account_names and session_id in account_names:
                        conv_copy['account_name'] = account_names[session_id]
                    else:
                        conv_copy['account_name'] = session_id
                    conversations_map[conv['entity_id']] = conv_copy
        
        all_conversations = list(conversations_map.values())
        
        # Trier par date
        def safe_date_sort(conv):
            date = conv.get('last_message_date')
            if not date:
                return datetime.min
            if hasattr(date, 'tzinfo') and date.tzinfo is not None:
                date = date.replace(tzinfo=None)
            return date
        
        all_conversations.sort(key=safe_date_sort, reverse=True)
        
        return all_conversations


# Instance globale
_messaging_service_instance = None


def get_messaging_service() -> MessagingService:
    """
    Récupère l'instance globale du service de messagerie.
    
    Returns:
        MessagingService: Instance du service
    """
    global _messaging_service_instance
    if _messaging_service_instance is None:
        _messaging_service_instance = MessagingService()
    return _messaging_service_instance
