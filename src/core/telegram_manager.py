"""
Gestionnaire de connexions Telegram multi-comptes
"""
import asyncio
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from telethon import TelegramClient
from telethon.tl.types import Channel, Chat, User
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, FloodWaitError

from core.session_manager import SessionManager
from utils.logger import get_logger
from utils.config import get_config


# ============================================================================
# CREDENTIALS API TELEGRAM PAR DÉFAUT
# ============================================================================
# Ces credentials sont utilisés pour tous les utilisateurs de l'application.
# Obtenez vos propres credentials sur https://my.telegram.org
# 
# IMPORTANT : Gardez ces valeurs PRIVÉES et ne les commitez pas dans Git !
# En production, utilisez des variables d'environnement ou un fichier de config sécurisé.
# ============================================================================

DEFAULT_API_ID = "YOUR_API_ID_HERE"  # Remplacez par votre api_id
DEFAULT_API_HASH = "YOUR_API_HASH_HERE"  # Remplacez par votre api_hash

# Alternative : Charger depuis variable d'environnement
import os
if os.getenv("AUTOTELE_API_ID"):
    DEFAULT_API_ID = os.getenv("AUTOTELE_API_ID")
if os.getenv("AUTOTELE_API_HASH"):
    DEFAULT_API_HASH = os.getenv("AUTOTELE_API_HASH")


class TelegramAccount:
    """Représente un compte Telegram connecté"""
    
    def __init__(self, session_id: str, phone: str, 
                 api_id: str = None, api_hash: str = None,
                 account_name: str = None):
        self.session_id = session_id
        self.phone = phone
        # Utiliser les credentials par défaut si non fournis
        self.api_id = int(api_id) if api_id else int(DEFAULT_API_ID)
        self.api_hash = api_hash if api_hash else DEFAULT_API_HASH
        self.account_name = account_name or phone
        self.client: Optional[TelegramClient] = None
        self.is_connected = False
        self.logger = get_logger()
        self.session_manager = SessionManager()
    
    async def connect(self, session_file: str = None) -> bool:
        """
        Connecte le compte Telegram
        """
        try:
            if session_file is None:
                session_file = str(self.session_manager.get_session_file_path(self.session_id))
            
            self.client = TelegramClient(
                session_file,
                self.api_id,
                self.api_hash
            )
            
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                self.is_connected = False
                return False
            
            self.is_connected = True
            self.session_manager.update_last_used(self.session_id)
            self.logger.info(f"Compte connecté: {self.account_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erreur connexion compte {self.account_name}: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Déconnecte le compte"""
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
            self.logger.info(f"Compte déconnecté: {self.account_name}")
    
    async def send_code_request(self) -> bool:
        """Envoie la demande de code de vérification"""
        try:
            if self.client is None:
                session_file = str(self.session_manager.get_session_file_path(self.session_id))
                self.client = TelegramClient(session_file, self.api_id, self.api_hash)
                await self.client.connect()
            
            await self.client.send_code_request(self.phone)
            return True
        except Exception as e:
            self.logger.error(f"Erreur envoi code: {e}")
            return False
    
    async def sign_in(self, code: str, password: str = None) -> Tuple[bool, str]:
        """
        Authentifie le compte avec le code reçu
        Retourne (success, error_message)
        """
        try:
            await self.client.sign_in(self.phone, code)
            self.is_connected = True
            self.logger.info(f"Authentification réussie: {self.account_name}")
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
            self.logger.error(f"Erreur authentification: {e}")
            return False, str(e)
    
    async def get_dialogs(self) -> List[Dict]:
        """
        Récupère la liste des dialogues (groupes, canaux, conversations)
        """
        if not self.is_connected:
            return []
        
        try:
            dialogs = []
            async for dialog in self.client.iter_dialogs():
                entity = dialog.entity
                
                # Filtrer uniquement les groupes et canaux où on peut écrire
                if isinstance(entity, (Channel, Chat)):
                    dialog_info = {
                        "id": entity.id,
                        "title": dialog.title,
                        "type": "channel" if isinstance(entity, Channel) else "group",
                        "username": getattr(entity, 'username', None),
                        "can_send": self._can_send_messages(entity)
                    }
                    dialogs.append(dialog_info)
            
            return dialogs
        except Exception as e:
            self.logger.error(f"Erreur récupération dialogues: {e}")
            return []
    
    def _can_send_messages(self, entity) -> bool:
        """Vérifie si on peut envoyer des messages dans ce groupe/canal"""
        try:
            if isinstance(entity, Channel):
                return entity.creator or (entity.admin_rights and entity.admin_rights.post_messages)
            elif isinstance(entity, Chat):
                return not entity.kicked and not entity.left
            return False
        except Exception:
            return False
    
    async def schedule_message(self, chat_id: int, message: str, 
                              schedule_date: datetime,
                              file_path: str = None) -> Tuple[bool, str]:
        """
        Planifie un message dans un groupe/canal
        Utilise la fonctionnalité native de Telegram
        """
        if not self.is_connected:
            return False, "Compte non connecté"
        
        try:
            # Vérifier rate limit
            config = get_config()
            delay = config.get("telegram.rate_limit_delay", 3)
            await asyncio.sleep(delay)
            
            # Envoyer le message planifié
            if file_path and Path(file_path).exists():
                await self.client.send_file(
                    chat_id,
                    file_path,
                    caption=message,
                    schedule=schedule_date
                )
            else:
                await self.client.send_message(
                    chat_id,
                    message,
                    schedule=schedule_date
                )
            
            self.logger.info(f"Message planifié pour {schedule_date} dans chat {chat_id}")
            return True, ""
            
        except FloodWaitError as e:
            error_msg = f"Rate limit atteint. Attendez {e.seconds} secondes."
            self.logger.warning(error_msg)
            return False, error_msg
        except Exception as e:
            error_msg = f"Erreur planification message: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    async def get_me(self) -> Optional[Dict]:
        """Récupère les informations du compte"""
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
            self.logger.error(f"Erreur récupération infos compte: {e}")
            return None


class TelegramManager:
    """Gestionnaire central des comptes Telegram"""
    
    def __init__(self):
        self.accounts: Dict[str, TelegramAccount] = {}
        self.session_manager = SessionManager()
        self.logger = get_logger()
        self.config = get_config()
    
    async def add_account(self, phone: str, account_name: str = None,
                         api_id: str = None, api_hash: str = None) -> Tuple[bool, str, Optional[str]]:
        """
        Ajoute un nouveau compte
        Si api_id et api_hash ne sont pas fournis, utilise les credentials par défaut
        Retourne (success, message, session_id)
        """
        try:
            # Utiliser les credentials par défaut si non fournis
            _api_id = api_id if api_id else DEFAULT_API_ID
            _api_hash = api_hash if api_hash else DEFAULT_API_HASH
            
            # Créer une entrée de session
            session_id = self.session_manager.create_session_entry(
                phone, _api_id, _api_hash, account_name
            )
            
            # Créer l'objet compte
            account = TelegramAccount(session_id, phone, _api_id, _api_hash, account_name)
            
            # Envoyer le code de vérification
            success = await account.send_code_request()
            if not success:
                return False, "Erreur lors de l'envoi du code de vérification", None
            
            self.accounts[session_id] = account
            return True, "Code de vérification envoyé", session_id
            
        except Exception as e:
            error_msg = f"Erreur ajout compte: {e}"
            self.logger.error(error_msg)
            return False, error_msg, None
    
    async def verify_account(self, session_id: str, code: str, 
                            password: str = None) -> Tuple[bool, str]:
        """
        Vérifie le code et complète l'authentification
        """
        if session_id not in self.accounts:
            return False, "Session introuvable"
        
        account = self.accounts[session_id]
        success, error = await account.sign_in(code, password)
        
        if success:
            self.session_manager.update_session_status(session_id, "active")
        
        return success, error
    
    async def load_existing_sessions(self):
        """Charge les sessions existantes"""
        sessions = self.session_manager.get_active_sessions()
        
        for session_info in sessions:
            try:
                session_id = session_info["session_id"]
                account = TelegramAccount(
                    session_id,
                    session_info["phone"],
                    session_info["api_id"],
                    session_info["api_hash"],
                    session_info.get("account_name")
                )
                
                # Tenter de se connecter
                connected = await account.connect()
                if connected:
                    self.accounts[session_id] = account
                    self.logger.info(f"Session chargée: {session_id}")
                else:
                    self.logger.warning(f"Session non autorisée: {session_id}")
                    self.session_manager.update_session_status(session_id, "unauthorized")
                    
            except Exception as e:
                self.logger.error(f"Erreur chargement session {session_id}: {e}")
    
    def get_account(self, session_id: str) -> Optional[TelegramAccount]:
        """Récupère un compte par son ID"""
        return self.accounts.get(session_id)
    
    def list_accounts(self) -> List[Dict]:
        """Liste tous les comptes"""
        return [
            {
                "session_id": acc.session_id,
                "account_name": acc.account_name,
                "phone": acc.phone,
                "is_connected": acc.is_connected
            }
            for acc in self.accounts.values()
        ]
    
    async def remove_account(self, session_id: str):
        """Supprime un compte"""
        if session_id in self.accounts:
            await self.accounts[session_id].disconnect()
            del self.accounts[session_id]
        
        self.session_manager.delete_session(session_id)
        self.logger.info(f"Compte supprimé: {session_id}")
    
    async def disconnect_all(self):
        """Déconnecte tous les comptes"""
        for account in self.accounts.values():
            await account.disconnect()
        
        self.logger.info("Tous les comptes déconnectés")

