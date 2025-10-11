"""
Service de gestion de la messagerie en temps réel.
"""
import asyncio
import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
from telethon import events
from telethon.tl.types import User, Chat, Channel

from core.telegram.account import TelegramAccount
from utils.logger import get_logger

logger = get_logger()


class MessagingService:
    """Service pour gérer la messagerie en temps réel."""
    
    # Cache des conversations
    _conversations_cache_file = "conversations_cache.json"
    
    @classmethod
    def get_cache_file_path(cls) -> Path:
        """Retourne le chemin du fichier de cache."""
        return Path("temp") / cls._conversations_cache_file
    
    @classmethod
    def load_conversations_cache(cls) -> dict:
        """Charge le cache des conversations depuis le fichier."""
        cache_file = cls.get_cache_file_path()
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erreur lecture cache conversations: {e}")
        return {}
    
    @classmethod
    def save_conversations_cache(cls, conversations_by_account: dict) -> None:
        """Sauvegarde le cache des conversations."""
        try:
            cache_file = cls.get_cache_file_path()
            cache_file.parent.mkdir(exist_ok=True)
            
            # Convertir les datetime en strings pour JSON
            cache_data = {}
            for session_id, conversations in conversations_by_account.items():
                cache_data[session_id] = []
                for conv in conversations:
                    conv_copy = conv.copy()
                    if conv_copy.get('last_message_date') and hasattr(conv_copy['last_message_date'], 'isoformat'):
                        conv_copy['last_message_date'] = conv_copy['last_message_date'].isoformat()
                    cache_data[session_id].append(conv_copy)
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Erreur sauvegarde cache conversations: {e}")
    
    @classmethod
    def is_cache_valid(cls, max_age_minutes: int = 30) -> bool:
        """Vérifie si le cache est valide (pas trop ancien)."""
        cache_file = cls.get_cache_file_path()
        if not cache_file.exists():
            return False
        
        import time
        age_minutes = (time.time() - cache_file.stat().st_mtime) / 60
        return age_minutes < max_age_minutes
    
    @staticmethod
    async def get_conversations(account: TelegramAccount, limit: int = 30, include_groups: bool = False) -> List[Dict]:
        """
        Récupère les conversations récentes d'un compte.
        
        Args:
            account: Compte Telegram
            limit: Nombre maximum de conversations
            include_groups: Si True, inclut les groupes et canaux. Si False, uniquement les users.
            
        Returns:
            List[Dict]: Liste des conversations avec dernier message
        """
        if not account or not account.is_connected:
            logger.warning("Tentative de récupération de conversations avec compte non connecté")
            return []
        
        try:
            conversations = []
            
            # Limite raisonnable pour éviter la surcharge
            max_iter = limit * 3 if not include_groups else limit
            dialog_count = 0
            async for dialog in account.client.iter_dialogs(limit=max_iter):
                dialog_count += 1
                entity = dialog.entity
                
                # Déterminer le type d'entité
                entity_type = "user"
                if isinstance(entity, Channel):
                    entity_type = "channel"
                elif isinstance(entity, Chat):
                    entity_type = "group"
                
                # 🔒 Filtrer par type si nécessaire
                if not include_groups and entity_type in ["channel", "group"]:
                    continue
                
                # Récupérer le dernier message
                last_message = dialog.message
                last_message_text = ""
                last_message_date = None
                last_message_from_me = False
                
                if last_message:
                    # Gestion du texte du dernier message
                    if last_message.media:
                        # Déterminer le type de média
                        media_type = type(last_message.media).__name__
                        if media_type == 'MessageMediaPhoto':
                            last_message_text = "📷 Photo"
                        elif media_type == 'MessageMediaDocument':
                            # Vérifier si c'est une vidéo, audio, etc.
                            if hasattr(last_message.media.document, 'mime_type'):
                                mime_type = last_message.media.document.mime_type
                                if mime_type.startswith('video/'):
                                    last_message_text = "🎥 Vidéo"
                                elif mime_type.startswith('audio/'):
                                    last_message_text = "🎵 Audio"
                                elif mime_type.startswith('image/'):
                                    last_message_text = "🖼️ Image"
                                else:
                                    last_message_text = "📎 Document"
                            else:
                                last_message_text = "📎 Document"
                        elif media_type == 'MessageMediaVideo':
                            last_message_text = "🎥 Vidéo"
                        elif media_type == 'MessageMediaAudio':
                            last_message_text = "🎵 Audio"
                        else:
                            last_message_text = "[Média]"
                        
                        # Ajouter la légende si elle existe
                        if hasattr(last_message.media, 'caption') and last_message.media.caption:
                            last_message_text += f": {last_message.media.caption}"
                        elif hasattr(last_message, 'caption') and last_message.caption:
                            last_message_text += f": {last_message.caption}"
                    else:
                        last_message_text = last_message.text or last_message.message or ""
                    
                    last_message_date = last_message.date
                    last_message_from_me = last_message.out
                    
                    # 🕐 Convertir l'heure UTC en heure locale
                    if last_message_date:
                        if hasattr(last_message_date, 'tzinfo') and last_message_date.tzinfo is not None:
                            last_message_date = last_message_date.astimezone().replace(tzinfo=None)
                        # Sinon, on garde la date telle quelle
                
                # Télécharger la photo de profil si elle existe
                profile_photo_path = None
                try:
                    if hasattr(entity, 'photo') and entity.photo:
                        # Créer le dossier pour les photos de profil
                        photos_dir = os.path.join(os.getcwd(), 'temp', 'photos')
                        os.makedirs(photos_dir, exist_ok=True)
                        
                        # Télécharger la photo de profil
                        profile_photo_path = await account.client.download_profile_photo(entity, photos_dir)
                except Exception as e:
                    pass
                
                conversation = {
                    "id": dialog.id,
                    "title": dialog.title or "Sans nom",
                    "type": entity_type,
                    "entity_id": entity.id,
                    "unread_count": dialog.unread_count,
                    "last_message": last_message_text[:100],  # Limiter à 100 caractères
                    "last_message_date": last_message_date,
                    "last_message_from_me": last_message_from_me,
                    "pinned": dialog.pinned,
                    "archived": dialog.archived,
                    "username": getattr(entity, 'username', None),
                    "profile_photo": profile_photo_path,
                    "has_photo": profile_photo_path is not None,
                }
                
                conversations.append(conversation)
                
                # Arrêter si on a assez de conversations
                if len(conversations) >= limit:
                    break
            
            return conversations
            
        except Exception as e:
            logger.error(f"Erreur récupération conversations: {e}")
            return []
    
    @staticmethod
    async def get_messages(
        account: TelegramAccount,
        chat_id: int,
        limit: int = 30,
        offset_id: int = 0
    ) -> List[Dict]:
        """
        Récupère les messages d'une conversation.
        
        Args:
            account: Compte Telegram
            chat_id: ID du chat
            limit: Nombre maximum de messages
            offset_id: ID du message de départ (pour pagination)
            
        Returns:
            List[Dict]: Liste des messages
        """
        if not account or not account.is_connected:
            return []
        
        try:
            messages = []
            
            async for message in account.client.iter_messages(
                chat_id,
                limit=limit,
                offset_id=offset_id
            ):
                # Informations sur l'expéditeur
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
                
                # Texte du message
                message_text = message.text or message.message or ""
                
                # Gestion des médias
                media_type = None
                media_data = None
                media_caption = ""
                
                if message.media:
                    media_type = type(message.media).__name__
                    
                    # Pour les photos et documents
                    if media_type in ['MessageMediaPhoto', 'MessageMediaDocument']:
                        try:
                            # Créer le dossier de médias s'il n'existe pas
                            media_dir = os.path.join(os.getcwd(), 'temp', 'media')
                            os.makedirs(media_dir, exist_ok=True)
                            
                            # Télécharger le média dans le dossier temp/media
                            media_data = await account.client.download_media(message, media_dir)
                            
                            # Récupérer la légende si elle existe
                            if hasattr(message.media, 'caption') and message.media.caption:
                                media_caption = message.media.caption
                            elif hasattr(message, 'caption') and message.caption:
                                media_caption = message.caption
                                
                        except Exception as e:
                            logger.warning(f"Erreur téléchargement média: {e}")
                            media_data = None
                
                # 🕐 Convertir l'heure UTC en heure locale
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
                    "media_data": media_data,  # Chemin vers le fichier téléchargé
                    "media_caption": media_caption,
                    "reply_to": message.reply_to_msg_id,
                    "edited": message.edit_date is not None,
                    "views": getattr(message, 'views', None),
                }
                
                messages.append(msg_dict)
            
            # Les messages sont retournés du plus récent au plus ancien
            # On les inverse pour avoir l'ordre chronologique
            messages.reverse()
            
            return messages
            
        except Exception as e:
            logger.error(f"Erreur récupération messages: {e}")
            return []
    
    @staticmethod
    async def send_message(
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
            reply_to: ID du message auquel répondre (optionnel)
            
        Returns:
            bool: True si l'envoi a réussi
        """
        if not account or not account.is_connected:
            return False
        
        try:
            await account.client.send_message(
                chat_id,
                message,
                reply_to=reply_to
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi message: {e}")
            return False
    
    @staticmethod
    async def mark_as_read(account: TelegramAccount, chat_id: int) -> bool:
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
            return True
            
        except Exception as e:
            logger.error(f"Erreur marquage comme lu: {e}")
            return False
    
    @staticmethod
    def setup_new_message_handler(
        account: TelegramAccount,
        callback: Callable[[Dict], None]
    ) -> None:
        """
        Configure un gestionnaire pour les nouveaux messages.
        
        Args:
            account: Compte Telegram
            callback: Fonction à appeler pour chaque nouveau message
        """
        if not account or not account.is_connected or not account.client:
            return
        
        @account.client.on(events.NewMessage(incoming=True))
        async def new_message_handler(event):
            try:
                message = event.message
                chat = await event.get_chat()
                sender = await event.get_sender()
                
                # Nom de l'expéditeur
                sender_name = "Inconnu"
                if sender:
                    if hasattr(sender, 'first_name'):
                        sender_name = sender.first_name or ""
                        if hasattr(sender, 'last_name') and sender.last_name:
                            sender_name += f" {sender.last_name}"
                    elif hasattr(sender, 'title'):
                        sender_name = sender.title
                
                # Créer le dictionnaire du message
                msg_dict = {
                    "id": message.id,
                    "chat_id": event.chat_id,
                    "chat_title": getattr(chat, 'title', None) or sender_name,
                    "text": message.text or message.message or "[Média]",
                    "date": message.date,
                    "sender_id": sender.id if sender else None,
                    "sender_name": sender_name,
                    "has_media": message.media is not None,
                    "media_type": type(message.media).__name__ if message.media else None,
                }
                
                # Appeler le callback
                callback(msg_dict)
                
            except Exception as e:
                logger.error(f"Erreur dans le gestionnaire de nouveaux messages: {e}")
    
    @staticmethod
    async def search_conversations(
        conversations: List[Dict],
        search_text: str
    ) -> List[Dict]:
        """
        Filtre les conversations par texte de recherche.
        
        Args:
            conversations: Liste des conversations
            search_text: Texte à rechercher
            
        Returns:
            List[Dict]: Liste filtrée des conversations
        """
        if not search_text:
            return conversations
        
        search_lower = search_text.lower().strip()
        return [
            conv for conv in conversations
            if search_lower in conv['title'].lower()
        ]
    
    @staticmethod
    def merge_conversations_from_accounts(
        conversations_by_account: Dict[str, List[Dict]],
        master_account_id: str = None,
        account_names: Dict[str, str] = None
    ) -> List[Dict]:
        """
        Fusionne les conversations de plusieurs comptes en filtrant les doublons.
        Si un groupe existe sur plusieurs comptes, ne garde que celui du compte maître.
        
        Args:
            conversations_by_account: Dict {session_id: [conversations]}
            master_account_id: Session ID du compte maître (optionnel)
            account_names: Dict {session_id: account_name} pour les vrais noms
            
        Returns:
            List[Dict]: Liste fusionnée et triée par date
        """
        # Dictionnaire pour détecter les doublons (par entity_id)
        conversations_map = {}
        
        # Priorité au compte maître si défini
        if master_account_id and master_account_id in conversations_by_account:
            # D'abord ajouter toutes les conversations du compte maître
            for conv in conversations_by_account[master_account_id]:
                conv_copy = conv.copy()
                # Utiliser le vrai nom du compte si disponible
                conv_copy['account_name'] = account_names.get(master_account_id, master_account_id) if account_names else master_account_id
                conversations_map[conv['entity_id']] = conv_copy
        
        # Ajouter les conversations des autres comptes (uniquement si pas déjà présentes)
        for session_id, conversations in conversations_by_account.items():
            if session_id == master_account_id:
                continue  # Déjà traité
            
            for conv in conversations:
                # Si ce groupe n'existe pas déjà (pas de doublon), l'ajouter
                if conv['entity_id'] not in conversations_map:
                    conv_copy = conv.copy()
                    # Utiliser le vrai nom du compte si disponible
                    conv_copy['account_name'] = account_names.get(session_id, session_id) if account_names else session_id
                    conversations_map[conv['entity_id']] = conv_copy
        
        # Convertir en liste
        all_conversations = list(conversations_map.values())
        
        # Trier par date du dernier message (plus récent en premier)
        # Gérer les dates avec timezone
        def safe_date_sort(conv):
            date = conv.get('last_message_date')
            if not date:
                return datetime.min
            
            # Normaliser la date pour éviter les problèmes de timezone
            if hasattr(date, 'tzinfo') and date.tzinfo is not None:
                date = date.replace(tzinfo=None)
            
            return date
        
        all_conversations.sort(key=safe_date_sort, reverse=True)
        
        return all_conversations