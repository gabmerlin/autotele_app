"""
Classe représentant un compte Telegram connecté.
"""
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat
from telethon.tl.functions.messages import GetScheduledHistoryRequest, DeleteScheduledMessagesRequest
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError

from core.session_manager import SessionManager
from utils.logger import get_logger
from utils.constants import TELEGRAM_MIN_DELAY_PER_CHAT, TELEGRAM_MAX_SCHEDULED_MESSAGES_FETCH

logger = get_logger()


class TelegramAccount:
    """Représente un compte Telegram connecté."""
    
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
            session_id: ID unique de la session
            phone: Numéro de téléphone
            api_id: ID de l'API Telegram
            api_hash: Hash de l'API Telegram
            account_name: Nom du compte (optionnel)
        """
        self.session_id = session_id
        self.phone = phone
        self.api_id = api_id
        self.api_hash = api_hash
        self.account_name = account_name or phone
        self.client: Optional[TelegramClient] = None
        self.is_connected = False
        self.session_manager = SessionManager()
    
    async def connect(self, session_file: Optional[str] = None) -> bool:
        """
        Connecte le compte Telegram.
        
        Args:
            session_file: Chemin du fichier de session (optionnel)
            
        Returns:
            bool: True si la connexion a réussi
        """
        try:
            if session_file is None:
                session_file = str(self.session_manager.get_session_file_path(self.session_id))
            
            self.client = TelegramClient(session_file, self.api_id, self.api_hash)
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                self.is_connected = False
                return False
            
            self.is_connected = True
            self.session_manager.update_last_used(self.session_id)
            logger.info(f"Compte connecté: {self.account_name}")
            return True
            
        except Exception as e:
            logger.error(f"Erreur connexion compte {self.account_name}: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self) -> None:
        """Déconnecte le compte."""
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
            logger.info(f"Compte déconnecté: {self.account_name}")
    
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
            logger.info(f"Code de vérification envoyé à {self.phone}")
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
            logger.info(f"Authentification réussie: {self.account_name}")
            return True, ""
            
        except SessionPasswordNeededError:
            # 2FA activé
            if password:
                try:
                    await self.client.sign_in(password=password)
                    self.is_connected = True
                    logger.info(f"Authentification 2FA réussie: {self.account_name}")
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
        file_path: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Planifie un message dans un groupe/canal.
        
        Args:
            chat_id: ID du chat
            message: Message à envoyer
            schedule_date: Date et heure de planification
            file_path: Chemin du fichier à joindre (optionnel)
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if not self.is_connected:
            return False, "Compte non connecté"
        
        try:
            if isinstance(chat_id, str):
                chat_id = int(chat_id)
            
            # Vérifier si c'est un envoi immédiat ou programmé
            now = datetime.now()
            time_diff = (schedule_date - now).total_seconds()
            is_immediate = time_diff < 60
            
            if is_immediate:
                # Envoi immédiat
                if file_path and Path(file_path).exists():
                    await self.client.send_file(chat_id, file_path, caption=message)
                else:
                    await self.client.send_message(chat_id, message)
            else:
                # Envoi programmé
                if file_path and Path(file_path).exists():
                    try:
                        # Pour les messages programmés avec fichiers, utiliser send_message avec document
                        from telethon.tl.types import InputMediaDocument
                        file_input = await self.client.upload_file(file_path)
                        media = InputMediaDocument(file_input)
                        await self.client.send_message(
                            chat_id, 
                            message, 
                            file=media,
                            schedule=schedule_date
                        )
                    except Exception as file_error:
                        # Si l'envoi avec fichier échoue, essayer sans fichier
                        logger.warning(f"Échec envoi fichier programmé, envoi sans fichier: {file_error}")
                        await self.client.send_message(chat_id, message, schedule=schedule_date)
                else:
                    await self.client.send_message(chat_id, message, schedule=schedule_date)
            
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
                "phone": me.phone
            }
        except Exception as e:
            logger.error(f"Erreur récupération infos compte: {e}")
            return None
    
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
            
            logger.info(f"Scan complet de {len(dialogs)} groupe(s)...")
            
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
                        logger.debug(f"API bas niveau échouée pour {chat_title}, utilisation de iter_messages: {api_error}")
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
                    logger.debug(f"Erreur {chat_title}: {str(e)[:80]}")
                    continue
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Progression: {i + 1}/{len(dialogs)} groupes - {len(all_scheduled)} messages")
            
            all_scheduled.sort(key=lambda x: x['date'])
            logger.info(f"Scan terminé: {len(all_scheduled)} message(s) trouvé(s)")
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
                logger.info(f"🗑️ {len(message_ids)} message(s) supprimé(s)")
            else:
                # Supprimer tous les messages
                scheduled_messages = await self.client.get_messages(chat_id, scheduled=True, limit=TELEGRAM_MAX_SCHEDULED_MESSAGES_FETCH)
                if scheduled_messages:
                    msg_ids = [msg.id for msg in scheduled_messages]
                    await self.client(DeleteScheduledMessagesRequest(peer=chat_id, id=msg_ids))
                    logger.info(f"🗑️ {len(msg_ids)} message(s) supprimé(s)")
            
            return True, ""
            
        except Exception as e:
            error_msg = f"Erreur suppression messages: {e}"
            logger.error(error_msg)
            return False, error_msg

