"""Classe représentant un compte Telegram connecté."""
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from telethon import TelegramClient
from telethon.errors import (
    FloodWaitError,
    PhoneCodeInvalidError,
    SessionPasswordNeededError
)
from telethon.tl.functions.messages import (
    DeleteScheduledMessagesRequest,
    GetScheduledHistoryRequest
)
from telethon.tl.types import Channel, Chat

from core.session_manager import SessionManager
from utils.constants import (
    TELEGRAM_MAX_SCHEDULED_MESSAGES_FETCH,
    TELEGRAM_MIN_DELAY_PER_CHAT
)
from utils.logger import get_logger

logger = get_logger()


class TelegramAccount:
    """Représente un compte Telegram connecté avec ses fonctionnalités."""

    def __init__(
        self,
        session_id: str,
        phone: str,
        api_id: int,
        api_hash: str,
        account_name: Optional[str] = None
    ):
        """
        Initialise un compte Telegram.

        Args:
            session_id: ID unique de la session.
            phone: Numéro de téléphone.
            api_id: ID de l'API Telegram.
            api_hash: Hash de l'API Telegram.
            account_name: Nom du compte (optionnel).
        """
        self.session_id = session_id
        self.phone = phone
        self.api_id = api_id
        self.api_hash = api_hash
        self.account_name = account_name or phone
        self.client: Optional[TelegramClient] = None
        self.is_connected = False
        self.session_manager = SessionManager()
        # Cache des entités pour éviter get_input_entity
        self._entity_cache: Dict[int, any] = {}
    
    async def connect(self, session_file: Optional[str] = None) -> bool:
        """
        Connecte le compte Telegram.

        Args:
            session_file: Chemin du fichier de session (optionnel).

        Returns:
            bool: True si la connexion a réussi.
        """
        try:
            if session_file is None:
                session_file = self.session_manager.get_session_for_client(
                    self.session_id
                )

            self.client = TelegramClient(
                session_file,
                self.api_id,
                self.api_hash
            )
            
            await self.client.connect()

            if not await self.client.is_user_authorized():
                self.is_connected = False
                await self.disconnect()
                return False

            self.is_connected = True
            self.session_manager.update_last_used(self.session_id)
            logger.info(f"Compte {self.account_name} connecté avec succès")
            return True

        except Exception as e:
            logger.error(f"Erreur connexion compte {self.account_name}: {e}")
            await self.disconnect()
            self.is_connected = False
            return False

    async def disconnect(self) -> None:
        """Déconnecte le compte."""
        if self.client:
            try:
                await self.client.disconnect()
                logger.debug(f"Compte {self.account_name} déconnecté")
            except Exception as e:
                logger.warning(f"Erreur lors de la déconnexion de {self.account_name}: {e}")
            finally:
                self.client = None
                self.is_connected = False
    
    async def send_code_request(self) -> bool:
        """
        Envoie la demande de code de vérification.
        
        Returns:
            bool: True si l'envoi a réussi
        """
        try:
            if self.client is None:
                session_file = str(self.session_manager.get_session_file_path(self.session_id))
                self.client = TelegramClient(session_file, self.api_id, self.api_hash)
            
            if not self.client.is_connected():
                await self.client.connect()
            
            await self.client.send_code_request(self.phone)
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi code: {e}")
            # Tentative de reconnexion
            try:
                if self.client:
                    await self.client.disconnect()
                    await self.client.connect()
                    await self.client.send_code_request(self.phone)
                    return True
            except Exception as reconnect_error:
                logger.error(f"Erreur lors de la reconnexion: {reconnect_error}")
            return False
    
    async def sign_in(self, code: str, password: Optional[str] = None) -> Tuple[bool, str]:
        """
        Authentifie le compte avec le code reçu.
        
        Args:
            code: Code de vérification
            password: Mot de passe 2FA (optionnel)
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            if not self.client.is_connected():
                await self.client.connect()
            
            await self.client.sign_in(self.phone, code)
            self.is_connected = True
            return True, ""
            
        except SessionPasswordNeededError:
            # 2FA activé
            if password:
                try:
                    await self.client.sign_in(password=password)
                    self.is_connected = True
                    return True, ""
                except Exception as e:
                    return False, f"Mot de passe 2FA incorrect: {e}"
            return False, "Mot de passe 2FA requis"
            
        except PhoneCodeInvalidError:
            return False, "Code de vérification invalide"
            
        except Exception as e:
            logger.error(f"Erreur authentification: {e}")
            return False, str(e)
    
    async def get_dialogs(self) -> List[Dict]:
        """
        Récupère la liste des dialogues (groupes, canaux, conversations).
        
        Returns:
            List[Dict]: Liste des dialogues
        """
        try:
            if not self.client.is_connected():
                await self.client.connect()
            
            dialogs = []
            
            async for dialog in self.client.iter_dialogs():
                entity = dialog.entity
                
                # Récupérer uniquement les groupes et canaux
                if isinstance(entity, (Channel, Chat)):
                    # CACHER l'entité avec TOUTES les formes d'ID possibles
                    # Les channels/megagroupes ont des IDs avec le préfixe -100
                    entity_id = entity.id
                    self._entity_cache[entity_id] = entity  # ID positif
                    
                    # Pour les channels/megagroupes, cacher aussi avec l'ID négatif
                    if isinstance(entity, Channel) and (entity.megagroup or entity.broadcast):
                        negative_id = -1000000000000 - entity_id  # Format -100XXXXXXXXX
                        self._entity_cache[negative_id] = entity
                    
                    dialog_info = {
                        "id": entity.id,
                        "title": dialog.title,
                        "type": "channel" if isinstance(entity, Channel) else "group",
                        "username": getattr(entity, 'username', None),
                        "can_send": self._can_send_messages(entity),
                        "participants_count": getattr(entity, 'participants_count', 0),
                        "is_broadcast": getattr(entity, 'broadcast', False),
                        "is_megagroup": getattr(entity, 'megagroup', False),
                        "is_member": not getattr(entity, 'left', False) and not getattr(entity, 'kicked', False),
                        "is_admin": getattr(entity, 'admin_rights', None) is not None or getattr(entity, 'creator', False)
                    }
                    dialogs.append(dialog_info)
            
            # Trier par type et taille
            dialogs.sort(key=lambda x: (
                0 if x["type"] == "group" else 1,
                -x["participants_count"]
            ))
            
            return dialogs
            
        except Exception as e:
            logger.error(f"Erreur récupération dialogues: {e}")
            return []
    
    def _can_send_messages(self, entity) -> bool:
        """
        Vérifie si on peut envoyer des messages dans ce groupe/canal.
        
        Args:
            entity: L'entité Telegram (Channel ou Chat)
            
        Returns:
            bool: True si on peut envoyer des messages
        """
        try:
            if isinstance(entity, Channel):
                return not entity.left and not entity.kicked
            elif isinstance(entity, Chat):
                return not entity.kicked and not entity.left
            return False
        except Exception:
            return True
    
    async def schedule_message(
        self,
        chat_id: int,
        message: str,
        schedule_date: datetime,
        file_path: Optional[str] = None,
        uploaded_file = None
    ) -> Tuple[bool, str]:
        """
        Planifie un message dans un groupe/canal.
        
        Args:
            chat_id: ID du chat
            message: Message à envoyer
            schedule_date: Date et heure de planification
            file_path: Chemin du fichier à joindre (optionnel, legacy)
            uploaded_file: Fichier déjà uploadé (optimisé)
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if not self.is_connected:
            return False, "Compte non connecté"
        
        try:
            if isinstance(chat_id, str):
                chat_id = int(chat_id)
            
            # UTILISER l'entité cachée pour éviter get_input_entity
            entity = self._entity_cache.get(chat_id)
            if entity is None:
                # Si pas en cache, résoudre UNE FOIS (coûte 1 API call)
                entity = await self.client.get_input_entity(chat_id)
                self._entity_cache[chat_id] = entity
            
            # Vérifier si c'est un envoi immédiat ou programmé
            now = datetime.now()
            time_diff = (schedule_date - now).total_seconds()
            is_immediate = time_diff < 60
            
            if is_immediate:
                # Envoi immédiat
                if uploaded_file:
                    await self.client.send_message(entity, message, file=uploaded_file)
                elif file_path and Path(file_path).exists():
                    await self.client.send_file(entity, file_path, caption=message)
                else:
                    await self.client.send_message(entity, message)
            else:
                # Envoi programmé
                if uploaded_file:
                    # Utiliser le fichier déjà uploadé (optimisé)
                    await self.client.send_message(
                        entity,
                        message,
                        file=uploaded_file,
                        schedule=schedule_date
                    )
                elif file_path and Path(file_path).exists():
                    # Upload sur place (legacy, moins optimisé)
                    try:
                        import mimetypes
                        from telethon.tl.types import (
                            InputMediaUploadedDocument,
                            DocumentAttributeFilename
                        )
                        
                        file_input = await self.client.upload_file(file_path)
                        mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                        file_name = Path(file_path).name
                        attributes = [DocumentAttributeFilename(file_name=file_name)]
                        
                        media = InputMediaUploadedDocument(
                            file=file_input,
                            mime_type=mime_type,
                            attributes=attributes
                        )
                        await self.client.send_message(
                            entity, 
                            message, 
                            file=media,
                            schedule=schedule_date
                        )
                    except Exception as file_error:
                        # Si l'envoi avec fichier échoue, essayer sans fichier
                        logger.warning(f"Échec envoi fichier programmé, envoi sans fichier: {file_error}")
                        await self.client.send_message(entity, message, schedule=schedule_date)
                else:
                    # Sans fichier
                    await self.client.send_message(entity, message, schedule=schedule_date)
            
            return True, ""
            
        except FloodWaitError as e:
            error_msg = f"Rate limit atteint : attendez {e.seconds} secondes"
            logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Erreur planification message: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    async def get_me(self) -> Optional[Dict]:
        """
        Récupère les informations du compte.
        
        Returns:
            Optional[Dict]: Informations du compte ou None
        """
        if not self.is_connected:
            return None
        
        try:
            me = await self.client.get_me()
            return {
                "id": me.id,
                "first_name": me.first_name,
                "last_name": me.last_name,
                "username": me.username,
                "phone": me.phone,
                "full_name": f"{me.first_name or ''} {me.last_name or ''}".strip() or me.phone
            }
        except Exception as e:
            logger.error(f"Erreur récupération infos compte: {e}")
            return None
    
    async def get_profile_photo_path(self) -> Optional[str]:
        """
        Télécharge et retourne le chemin de la photo de profil.
        
        Returns:
            Optional[str]: Chemin de la photo ou None
        """
        if not self.is_connected:
            return None
        
        try:
            from utils.paths import get_temp_dir
            me = await self.client.get_me()
            
            # Créer le dossier photos s'il n'existe pas
            photos_dir = get_temp_dir() / "photos"
            photos_dir.mkdir(parents=True, exist_ok=True)
            
            # Chemin de la photo
            photo_path = photos_dir / f"profile_{self.session_id}.jpg"
            
            # Télécharger la photo de profil
            if me.photo:
                await self.client.download_profile_photo(me, file=str(photo_path))
                return str(photo_path)
            
            return None
        except Exception as e:
            logger.error(f"Erreur récupération photo profil: {e}")
            return None
    
    async def update_profile_name(self, first_name: str, last_name: str = "") -> Tuple[bool, str]:
        """
        Met à jour le nom du profil Telegram (visible par les autres).
        
        Args:
            first_name: Prénom
            last_name: Nom de famille (optionnel)
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if not self.is_connected:
            return False, "Compte non connecté"
        
        try:
            from telethon.tl.functions.account import UpdateProfileRequest
            
            await self.client(UpdateProfileRequest(
                first_name=first_name,
                last_name=last_name
            ))
            
            return True, ""
        except Exception as e:
            error_msg = f"Erreur mise à jour nom: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    async def update_profile_photo(self, file_path: str) -> Tuple[bool, str]:
        """
        Met à jour la photo de profil Telegram.
        
        Args:
            file_path: Chemin du fichier photo
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if not self.is_connected:
            return False, "Compte non connecté"
        
        try:
            from telethon.tl.functions.photos import UploadProfilePhotoRequest
            
            # Uploader la photo
            uploaded_file = await self.client.upload_file(file_path)
            
            # Définir comme photo de profil
            await self.client(UploadProfilePhotoRequest(
                file=uploaded_file
            ))
            
            return True, ""
        except Exception as e:
            error_msg = f"Erreur mise à jour photo: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    async def get_all_scheduled_messages(self) -> List[Dict]:
        """
        Récupère TOUS les messages programmés du compte.
        
        Returns:
            List[Dict]: Liste des messages programmés
        """
        if not self.is_connected:
            return []
        
        try:
            all_scheduled = []
            dialogs = await self.get_dialogs()
            all_scheduled = []
            
            for i, dialog in enumerate(dialogs):
                chat_id = dialog['id']
                chat_title = dialog['title']
                
                try:
                    # Essayer avec l'API bas niveau
                    try:
                        peer = await self.client.get_input_entity(chat_id)
                        result = await self.client(GetScheduledHistoryRequest(peer=peer, hash=0))
                        
                        if hasattr(result, 'messages') and result.messages:
                            for msg in result.messages:
                                scheduled_info = {
                                    "message_id": msg.id,
                                    "chat_id": chat_id,
                                    "chat_title": chat_title,
                                    "text": getattr(msg, 'message', None) or getattr(msg, 'text', None) or "[Fichier]",
                                    "date": msg.date,
                                    "has_media": hasattr(msg, 'media') and msg.media is not None,
                                    "media_type": type(msg.media).__name__ if hasattr(msg, 'media') and msg.media else None
                                }
                                all_scheduled.append(scheduled_info)
                    except Exception as api_error:
                        # Fallback : iter_messages
                        async for msg in self.client.iter_messages(chat_id, scheduled=True):
                            scheduled_info = {
                                "message_id": msg.id,
                                "chat_id": chat_id,
                                "chat_title": chat_title,
                                "text": msg.text or msg.message or "[Fichier]",
                                "date": msg.date,
                                "has_media": msg.media is not None,
                                "media_type": type(msg.media).__name__ if msg.media else None
                            }
                            all_scheduled.append(scheduled_info)
                    
                    # Petit délai pour éviter les rate limits
                    import asyncio
                    await asyncio.sleep(0.05)
                    
                except Exception as e:
                    continue
            
            all_scheduled.sort(key=lambda x: x['date'])
            return all_scheduled
            
        except Exception as e:
            logger.error(f"Erreur récupération messages programmés: {e}")
            return []
    
    async def delete_scheduled_messages(
        self,
        chat_id: int,
        message_ids: Optional[List[int]] = None
    ) -> Tuple[bool, str]:
        """
        Supprime des messages programmés.
        
        Args:
            chat_id: ID du chat
            message_ids: IDs des messages à supprimer (None = tous)
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if not self.is_connected:
            return False, "Compte non connecté"
        
        try:
            if isinstance(chat_id, str):
                chat_id = int(chat_id)
            
            if message_ids:
                # Supprimer des messages spécifiques
                await self.client(DeleteScheduledMessagesRequest(peer=chat_id, id=message_ids))
            else:
                # Supprimer tous les messages
                scheduled_messages = await self.client.get_messages(chat_id, scheduled=True, limit=TELEGRAM_MAX_SCHEDULED_MESSAGES_FETCH)
                if scheduled_messages:
                    msg_ids = [msg.id for msg in scheduled_messages]
                    await self.client(DeleteScheduledMessagesRequest(peer=chat_id, id=msg_ids))
            
            return True, ""
            
        except Exception as e:
            error_msg = f"Erreur suppression messages: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    async def resolve_username(self, username: str) -> Optional[Dict]:
        """
        Résout un username et retourne les infos de base de l'entité.
        
        Args:
            username: Username à résoudre (avec ou sans @)
            
        Returns:
            Optional[Dict]: Infos de l'entité (id, title, type, username) ou None
        """
        if not self.is_connected:
            return None
        
        try:
            from telethon.tl.types import User
            
            # Nettoyer l'username
            clean_username = username.lstrip('@').strip()
            
            if not clean_username:
                return None
            
            # Résoudre l'entité
            entity = await self.client.get_entity(clean_username)
            
            # Déterminer le type et construire le titre
            if isinstance(entity, User):
                entity_type = "user"
                first_name = getattr(entity, 'first_name', '') or ''
                last_name = getattr(entity, 'last_name', '') or ''
                title = f"{first_name} {last_name}".strip() or clean_username
            elif isinstance(entity, Channel):
                entity_type = "channel"
                title = getattr(entity, 'title', clean_username)
            elif isinstance(entity, Chat):
                entity_type = "group"
                title = getattr(entity, 'title', clean_username)
            else:
                return None
            
            return {
                "id": entity.id,
                "title": title,
                "type": entity_type,
                "username": getattr(entity, 'username', None) or clean_username,
            }
            
        except Exception as e:
            logger.error(f"Erreur résolution username {username}: {e}")
            return None

