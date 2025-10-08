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
# CREDENTIALS API TELEGRAM
# ============================================================================
# IMPORTANT : Vous DEVEZ obtenir vos propres credentials sur https://my.telegram.org
# 1. Allez sur https://my.telegram.org
# 2. Connectez-vous avec votre numéro Telegram
# 3. Créez une nouvelle application
# 4. Copiez api_id et api_hash ici
# ============================================================================

import os

# Charger les credentials depuis le fichier de configuration sécurisé
try:
    import sys
    from pathlib import Path
    # Ajouter le dossier config au path
    config_dir = Path(__file__).parent.parent.parent / "config"
    sys.path.insert(0, str(config_dir))
    from api_credentials import API_ID, API_HASH
    DEFAULT_API_ID = int(API_ID)
    DEFAULT_API_HASH = API_HASH
except ImportError:
    # Fallback si le fichier de config n'existe pas
    DEFAULT_API_ID = 21211112
    DEFAULT_API_HASH = "64342ccdb7588fe8648219265ff5f846"


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
        """Déconnecte le compte (optionnel - pour forcer la déconnexion)"""
        if self.client:
            await self.client.disconnect()
            self.is_connected = False
            self.logger.info(f"Compte déconnecté: {self.account_name}")
    
    def keep_connected(self):
        """Marque le compte comme devant rester connecté"""
        # Ne pas déconnecter automatiquement
        pass
    
    async def send_code_request(self) -> bool:
        """Envoie la demande de code de vérification"""
        try:
            if self.client is None:
                session_file = str(self.session_manager.get_session_file_path(self.session_id))
                self.client = TelegramClient(session_file, self.api_id, self.api_hash)
            
            # S'assurer que le client est connecté
            if not self.client.is_connected():
                await self.client.connect()
            
            # Envoyer la demande de code
            await self.client.send_code_request(self.phone)
            self.logger.info(f"Code de vérification envoyé à {self.phone}")
            return True
        except Exception as e:
            self.logger.error(f"Erreur envoi code: {e}")
            # Essayer de déconnecter et reconnecter
            try:
                if self.client:
                    await self.client.disconnect()
                    await self.client.connect()
                    await self.client.send_code_request(self.phone)
                    return True
            except:
                pass
            return False
    
    async def sign_in(self, code: str, password: str = None) -> Tuple[bool, str]:
        """
        Authentifie le compte avec le code reçu
        Retourne (success, error_message)
        """
        try:
            # S'assurer que le client est connecté
            if not self.client.is_connected():
                await self.client.connect()
            
            await self.client.sign_in(self.phone, code)
            self.is_connected = True
            
            # La session est automatiquement sauvegardée par Telethon
            self.logger.info(f"Authentification réussie: {self.account_name}")
            return True, ""
        except SessionPasswordNeededError:
            # 2FA activé
            if password:
                try:
                    await self.client.sign_in(password=password)
                    self.is_connected = True
                    
                    # La session est automatiquement sauvegardée par Telethon
                    self.logger.info(f"Authentification 2FA réussie: {self.account_name}")
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
        try:
            # S'assurer que le client est connecté
            if not self.client.is_connected():
                await self.client.connect()
            
            dialogs = []
            async for dialog in self.client.iter_dialogs():
                entity = dialog.entity
                
                # Récupérer TOUS les groupes et canaux (même ceux en lecture seule)
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
                0 if x["type"] == "group" else 1,  # Groupes en premier
                -x["participants_count"]  # Plus gros groupes en premier
            ))
            
            return dialogs
        except Exception as e:
            self.logger.error(f"Erreur récupération dialogues: {e}")
            return []
    
    def _can_send_messages(self, entity) -> bool:
        """Vérifie si on peut envoyer des messages dans ce groupe/canal"""
        try:
            if isinstance(entity, Channel):
                # Pour les canaux : être membre (pas forcément admin)
                return not entity.left and not entity.kicked
            elif isinstance(entity, Chat):
                # Pour les groupes : être membre (pas forcément admin)
                return not entity.kicked and not entity.left
            return False
        except Exception:
            # En cas d'erreur, considérer comme utilisable
            return True
    
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
            # S'assurer que chat_id est un int
            if isinstance(chat_id, str):
                chat_id = int(chat_id)
            
            # Vérifier si c'est un envoi immédiat (now) ou programmé
            now = datetime.now()
            time_diff = (schedule_date - now).total_seconds()
            is_immediate = time_diff < 60  # Moins d'1 minute = envoi immédiat
            
            if is_immediate:
                # Envoi immédiat (sans schedule)
                if file_path and Path(file_path).exists():
                    await self.client.send_file(chat_id, file_path, caption=message)
                else:
                    await self.client.send_message(chat_id, message)
            else:
                # Programmation dans Telegram
                if file_path and Path(file_path).exists():
                    await self.client.send_file(chat_id, file_path, caption=message, schedule=schedule_date)
                else:
                    await self.client.send_message(chat_id, message, schedule=schedule_date)
            
            return True, ""
            
        except FloodWaitError as e:
            error_msg = f"🛑 RATE LIMIT : Attendez {e.seconds} secondes ({e.seconds//60} minutes)"
            self.logger.error(error_msg)
            print(f"\n🛑 RATE LIMIT TELEGRAM : {e.seconds}s d'attente requise")
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
    
    async def delete_scheduled_messages(self, chat_id: int, message_ids: list = None) -> Tuple[bool, str]:
        """
        Supprime des messages programmés dans un groupe
        Si message_ids est None, supprime TOUS les messages programmés du groupe
        """
        if not self.is_connected:
            return False, "Compte non connecté"
        
        try:
            # S'assurer que chat_id est un int
            if isinstance(chat_id, str):
                chat_id = int(chat_id)
            
            if message_ids:
                # Supprimer des messages spécifiques
                await self.client.delete_messages(chat_id, message_ids)
                self.logger.info(f"🗑️ {len(message_ids)} message(s) programmé(s) supprimé(s) dans chat {chat_id}")
            else:
                # Récupérer tous les messages programmés et les supprimer
                scheduled_messages = await self.client.get_messages(chat_id, scheduled=True, limit=100)
                if scheduled_messages:
                    msg_ids = [msg.id for msg in scheduled_messages]
                    await self.client.delete_messages(chat_id, msg_ids)
                    self.logger.info(f"🗑️ {len(msg_ids)} message(s) programmé(s) supprimé(s) dans chat {chat_id}")
                else:
                    self.logger.info(f"Aucun message programmé trouvé dans chat {chat_id}")
            
            return True, ""
            
        except Exception as e:
            error_msg = f"Erreur suppression messages programmés: {e}"
            self.logger.error(error_msg)
            return False, error_msg


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
            account.is_connected = True
            self.session_manager.update_session_status(session_id, "active")
        
        return success, error
    
    async def resend_code(self, session_id: str) -> Tuple[bool, str]:
        """
        Renvoie un code de vérification pour un compte non autorisé
        """
        if session_id not in self.accounts:
            return False, "Session introuvable"
        
        account = self.accounts[session_id]
        success = await account.send_code_request()
        
        if success:
            return True, "Code de vérification renvoyé"
        else:
            return False, "Erreur lors de l'envoi du code"
    
    async def load_existing_sessions(self):
        """Charge les sessions existantes"""
        sessions = self.session_manager.list_sessions()
        
        for session_info in sessions:
            try:
                session_id = session_info["session_id"]
                
                # Vérifier si le fichier de session existe
                session_file = self.session_manager.get_session_file_path(session_id)
                if not session_file.exists():
                    self.session_manager.delete_session(session_id)
                    continue
                
                account = TelegramAccount(
                    session_id,
                    session_info["phone"],
                    session_info.get("api_id", DEFAULT_API_ID),
                    session_info.get("api_hash", DEFAULT_API_HASH),
                    session_info.get("account_name")
                )
                
                # Créer le client
                session_file_str = str(session_file)
                account.client = TelegramClient(session_file_str, account.api_id, account.api_hash)
                
                # Tenter de se connecter
                connected = await account.connect()
                if connected:
                    self.accounts[session_id] = account
                else:
                    # Marquer comme non autorisée mais la garder dans les comptes
                    account.is_connected = False
                    self.accounts[session_id] = account
                    self.session_manager.update_session_status(session_id, "unauthorized")
                    
            except Exception as e:
                self.logger.error(f"Erreur chargement session {session_info.get('phone', 'unknown')}: {e}")
    
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
    
    async def _connect_account(self, account):
        """Connecte un compte spécifique"""
        try:
            if account.client:
                await account.client.connect()
                
                if account.client.is_connected():
                    # Tester une opération simple
                    me = await account.client.get_me()
                    if me:
                        account.is_connected = True
                        self.logger.info(f"✅ Connexion maintenue: {account.phone}")
                        return True
                    else:
                        account.is_connected = False
                        self.logger.warning(f"❌ Connexion échouée: {account.phone} (pas d'utilisateur)")
                        return False
                else:
                    account.is_connected = False
                    self.logger.warning(f"❌ Connexion échouée: {account.phone} (client non connecté)")
                    return False
            else:
                account.is_connected = False
                self.logger.warning(f"❌ Pas de client: {account.phone}")
                return False
                
        except Exception as e:
            account.is_connected = False
            self.logger.error(f"❌ Erreur connexion {account.phone}: {e}")
            return False

    async def verify_all_connections(self):
        """Vérifie réellement la connexion de tous les comptes"""
        for account in self.accounts.values():
            await self._connect_account(account)
    
    async def reconnect_account(self, session_id: str) -> Tuple[bool, str]:
        """Reconnecte un compte spécifique sans affecter les autres"""
        if session_id not in self.accounts:
            return False, "Compte introuvable"
        
        account = self.accounts[session_id]
        
        try:
            # Déconnecter d'abord si nécessaire
            if account.client and account.client.is_connected():
                await account.client.disconnect()
            
            # Reconnecter
            success = await self._connect_account(account)
            
            if success:
                return True, f"✅ {account.phone} reconnecté avec succès"
            else:
                return False, f"❌ Échec de la reconnexion pour {account.phone}"
                
        except Exception as e:
            return False, f"❌ Erreur reconnexion {account.phone}: {str(e)}"
    
    async def save_session_after_login(self, session_id: str):
        """Sauvegarde la session après connexion réussie"""
        if session_id in self.accounts:
            account = self.accounts[session_id]
            if account.is_connected:
                # Vérifier que le fichier de session existe
                session_file = self.session_manager.get_session_file_path(session_id)
                if session_file.exists():
                    self.logger.info(f"Session sauvegardée: {account.phone} -> {session_file}")
                    return True
                else:
                    self.logger.error(f"Session non sauvegardée: {account.phone}")
                    return False
        return False
    
    
    def debug_sessions(self):
        """Affiche des informations de debug sur les sessions"""
        self.logger.info("=== DEBUG SESSIONS ===")
        
        # Vérifier le dossier des sessions
        sessions_dir = self.session_manager.sessions_dir
        self.logger.info(f"Dossier sessions: {sessions_dir}")
        self.logger.info(f"Dossier existe: {sessions_dir.exists()}")
        
        if sessions_dir.exists():
            files = list(sessions_dir.glob("*.session"))
            self.logger.info(f"Fichiers .session trouvés: {len(files)}")
            for f in files:
                self.logger.info(f"  - {f.name} ({f.stat().st_size} bytes)")
        
        # Vérifier l'index
        sessions = self.session_manager.list_sessions()
        self.logger.info(f"Sessions dans l'index: {len(sessions)}")
        for session in sessions:
            self.logger.info(f"  - {session['phone']} ({session['session_id']})")
        
        # Vérifier les comptes chargés
        self.logger.info(f"Comptes chargés: {len(self.accounts)}")
        for session_id, account in self.accounts.items():
            self.logger.info(f"  - {account.phone} (connecté: {account.is_connected})")
        
        self.logger.info("=== FIN DEBUG ===")

