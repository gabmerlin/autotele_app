"""
Gestionnaire central des comptes Telegram.
"""
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from telethon import TelegramClient

from core.session_manager import SessionManager
from .account import TelegramAccount
from .credentials import get_api_credentials
from utils.logger import get_logger

logger = get_logger()


class TelegramManager:
    """Gestionnaire central pour gérer plusieurs comptes Telegram."""
    
    def __init__(self):
        """Initialise le gestionnaire de comptes Telegram."""
        self.accounts: Dict[str, TelegramAccount] = {}
        self.session_manager = SessionManager()
    
    async def add_account(
        self,
        phone: str,
        account_name: Optional[str] = None,
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Ajoute un nouveau compte Telegram.
        
        Args:
            phone: Numéro de téléphone
            account_name: Nom du compte (optionnel)
            api_id: ID de l'API Telegram (optionnel)
            api_hash: Hash de l'API Telegram (optionnel)
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, session_id)
        """
        try:
            # Utiliser les credentials par défaut si non fournis
            if not api_id or not api_hash:
                api_id, api_hash = get_api_credentials()
            
            # Créer une entrée de session
            session_id = self.session_manager.create_session_entry(
                phone, str(api_id), api_hash, account_name
            )
            
            # Créer l'objet compte
            account = TelegramAccount(session_id, phone, api_id, api_hash, account_name)
            
            # Envoyer le code de vérification
            success = await account.send_code_request()
            if not success:
                return False, "Erreur lors de l'envoi du code de vérification", None
            
            self.accounts[session_id] = account
            return True, "Code de vérification envoyé", session_id
            
        except Exception as e:
            error_msg = f"Erreur ajout compte: {e}"
            logger.error(error_msg)
            return False, error_msg, None
    
    async def verify_account(
        self,
        session_id: str,
        code: str,
        password: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Vérifie le code et complète l'authentification.
        
        Args:
            session_id: ID de la session
            code: Code de vérification
            password: Mot de passe 2FA (optionnel)
            
        Returns:
            Tuple[bool, str]: (success, error_message)
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
        Renvoie un code de vérification.
        
        Args:
            session_id: ID de la session
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if session_id not in self.accounts:
            return False, "Session introuvable"
        
        account = self.accounts[session_id]
        success = await account.send_code_request()
        
        if success:
            return True, "Code de vérification renvoyé"
        else:
            return False, "Erreur lors de l'envoi du code"
    
    async def load_existing_sessions(self) -> None:
        """Charge les sessions existantes depuis le disque."""
        await self.load_existing_sessions_with_progress(None)
    
    async def load_existing_sessions_with_progress(self, progress_callback=None) -> None:
        """
        Charge les sessions existantes depuis le disque avec callback de progression.
        
        Args:
            progress_callback: Fonction callback(progress: int, message: str)
        """
        sessions = self.session_manager.list_sessions()
        
        if not sessions:
            if progress_callback:
                progress_callback(100, "Aucun compte à charger")
            return
        
        api_id, api_hash = get_api_credentials()
        total = len(sessions)
        
        for idx, session_info in enumerate(sessions):
            try:
                session_id = session_info["session_id"]
                account_name = session_info.get("account_name", session_info.get("phone", "Compte"))
                
                # Calculer la progression (10% à 90%, le 100% sera fait après)
                progress = 10 + int((idx / total) * 80)
                if progress_callback:
                    progress_callback(progress, f"Connexion à {account_name}...")
                
                # Vérifier si le fichier de session existe (chiffré ou non)
                # Note: TelegramClient ajoute .session, donc on cherche plusieurs variantes
                session_base = self.session_manager.sessions_dir / session_id
                possible_files = [
                    session_base.with_suffix('.enc.session'),  # Chiffré par Telethon
                    session_base.with_suffix('.enc'),           # Chiffré pur
                    session_base.with_suffix('.session'),       # Non chiffré
                ]
                
                # Vérifier si au moins un fichier existe
                session_exists = any(f.exists() for f in possible_files)
                
                if not session_exists:
                    self.session_manager.delete_session(session_id)
                    continue
                
                # SÉCURITÉ : Toujours utiliser les credentials depuis .env
                # Ne JAMAIS lire depuis session_info (legacy)
                _api_id = api_id
                _api_hash = api_hash
                
                account = TelegramAccount(
                    session_id,
                    session_info["phone"],
                    _api_id,
                    _api_hash,
                    session_info.get("account_name")
                )
                
                # Créer le client avec le chemin de session (déchiffré automatiquement si nécessaire)
                session_file_str = self.session_manager.get_session_for_client(session_id)
                account.client = TelegramClient(session_file_str, account.api_id, account.api_hash)
                
                # Tenter de se connecter
                connected = await account.connect()
                if connected:
                    self.accounts[session_id] = account
                    
                    # Récupérer et mettre à jour le nom Telegram + photo de profil
                    try:
                        me = await account.get_me()
                        if me:
                            telegram_name = me.get("full_name", account_name)
                            if telegram_name != account_name:
                                account.account_name = telegram_name
                                self.session_manager.update_account_name(session_id, telegram_name)
                        
                        # Télécharger la photo de profil en arrière-plan
                        try:
                            await account.get_profile_photo_path()
                        except Exception as photo_error:
                            # Ne pas bloquer le chargement si la photo échoue
                            logger.warning(f"Impossible de télécharger la photo de profil pour {account.account_name}: {photo_error}")
                    except Exception as e:
                        logger.error(f"Erreur récupération infos Telegram: {e}")
                    
                    if progress_callback:
                        progress_callback(progress, f"{account.account_name} connecté")
                else:
                    # Garder dans les comptes mais marquer comme non autorisé
                    account.is_connected = False
                    self.accounts[session_id] = account
                    self.session_manager.update_session_status(session_id, "unauthorized")
                    if progress_callback:
                        progress_callback(progress, f"{account_name} non autorisé")
                    
            except Exception as e:
                logger.error(f"Erreur chargement session {session_info.get('phone', 'unknown')}: {e}")
                if progress_callback:
                    progress_callback(progress, f"Erreur: {session_info.get('account_name', 'Compte')}")
        
        # Progression finale
        if progress_callback:
            progress_callback(90, "Finalisation...")
    
    def get_account(self, session_id: str) -> Optional[TelegramAccount]:
        """
        Récupère un compte par son ID.
        
        Args:
            session_id: ID de la session
            
        Returns:
            Optional[TelegramAccount]: Le compte ou None
        """
        return self.accounts.get(session_id)
    
    def list_accounts(self, reload_settings: bool = True) -> List[Dict]:
        """
        Liste tous les comptes.
        
        Args:
            reload_settings: Si True, recharge les settings depuis le fichier
        
        Returns:
            List[Dict]: Liste des comptes avec leurs informations
        """
        # Recharger l'index si demandé pour avoir les settings à jour
        if reload_settings:
            self.session_manager.sessions_index = self.session_manager._load_index()
        
        return [
            {
                "session_id": acc.session_id,
                "account_name": acc.account_name,
                "phone": acc.phone,
                "is_connected": acc.is_connected,
                "settings": self.session_manager.get_account_settings(acc.session_id)
            }
            for acc in self.accounts.values()
        ]
    
    def update_account_name(self, session_id: str, account_name: str) -> None:
        """
        Met à jour le nom d'un compte.
        
        Args:
            session_id: ID de la session
            account_name: Nouveau nom du compte
        """
        if session_id in self.accounts:
            self.accounts[session_id].account_name = account_name
        self.session_manager.update_account_name(session_id, account_name)
    
    async def remove_account(self, session_id: str) -> None:
        """
        Supprime un compte.
        
        Args:
            session_id: ID de la session
        """
        if session_id in self.accounts:
            await self.accounts[session_id].disconnect()
            del self.accounts[session_id]
        
        self.session_manager.delete_session(session_id)
    
    async def disconnect_all(self) -> None:
        """Déconnecte tous les comptes."""
        for account in self.accounts.values():
            await account.disconnect()
    
    async def reconnect_account(self, session_id: str) -> Tuple[bool, str]:
        """
        Reconnecte un compte spécifique.
        
        Args:
            session_id: ID de la session
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if session_id not in self.accounts:
            return False, "Compte introuvable"
        
        account = self.accounts[session_id]
        
        try:
            # Déconnecter d'abord
            if account.client and account.client.is_connected():
                await account.client.disconnect()
            
            # Reconnecter
            success = await account.connect()
            
            if success:
                # Mettre à jour les infos depuis Telegram
                try:
                    await self.update_account_name_from_telegram(session_id)
                except Exception as e:
                    logger.warning(f"Impossible de mettre à jour les infos après reconnexion: {e}")
                
                return True, f"{account.phone} reconnecté avec succès"
            else:
                return False, f"Échec de la reconnexion pour {account.phone}"
                
        except Exception as e:
            return False, f"Erreur reconnexion {account.phone}: {str(e)}"
    
    async def update_account_name_from_telegram(self, session_id: str) -> bool:
        """
        Récupère et met à jour le nom du compte depuis Telegram, et télécharge la photo de profil.
        
        Args:
            session_id: ID de la session
            
        Returns:
            bool: True si réussi
        """
        if session_id not in self.accounts:
            return False
        
        account = self.accounts[session_id]
        
        try:
            # Récupérer les infos du compte
            me = await account.get_me()
            if me:
                full_name = me.get("full_name", account.phone)
                # Mettre à jour le nom dans l'objet compte
                account.account_name = full_name
                # Mettre à jour dans le session manager
                self.session_manager.update_account_name(session_id, full_name)
            
            # Télécharger la photo de profil
            try:
                await account.get_profile_photo_path()
            except Exception as photo_error:
                logger.warning(f"Impossible de télécharger la photo de profil: {photo_error}")
            
            return True
        except Exception as e:
            logger.error(f"Erreur mise à jour infos depuis Telegram: {e}")
        
        return False
    
    async def get_account_profile_photo(self, session_id: str) -> Optional[str]:
        """
        Récupère le chemin de la photo de profil d'un compte.
        
        Args:
            session_id: ID de la session
            
        Returns:
            Optional[str]: Chemin de la photo ou None
        """
        if session_id not in self.accounts:
            return None
        
        account = self.accounts[session_id]
        
        try:
            return await account.get_profile_photo_path()
        except Exception as e:
            logger.error(f"Erreur récupération photo profil: {e}")
            return None
    
    async def update_account_profile_name(self, session_id: str, full_name: str) -> Tuple[bool, str]:
        """
        Met à jour le nom du profil Telegram (visible par les autres).
        
        Args:
            session_id: ID de la session
            full_name: Nom complet (peut contenir prénom et nom)
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if session_id not in self.accounts:
            return False, "Compte introuvable"
        
        account = self.accounts[session_id]
        
        try:
            # Séparer le nom complet en prénom et nom
            parts = full_name.strip().split(maxsplit=1)
            first_name = parts[0] if parts else full_name
            last_name = parts[1] if len(parts) > 1 else ""
            
            # Mettre à jour sur Telegram
            success, error = await account.update_profile_name(first_name, last_name)
            
            if success:
                # Mettre à jour localement
                account.account_name = full_name
                self.session_manager.update_account_name(session_id, full_name)
            
            return success, error
        except Exception as e:
            error_msg = f"Erreur mise à jour nom profil: {e}"
            logger.error(error_msg)
            return False, error_msg
    
    async def update_account_profile_photo(self, session_id: str, file_path: str) -> Tuple[bool, str]:
        """
        Met à jour la photo de profil Telegram.
        
        Args:
            session_id: ID de la session
            file_path: Chemin du fichier photo
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        if session_id not in self.accounts:
            return False, "Compte introuvable"
        
        account = self.accounts[session_id]
        
        try:
            success, error = await account.update_profile_photo(file_path)
            
            if success:
                # Télécharger la nouvelle photo dans le cache
                try:
                    import asyncio
                    await asyncio.sleep(1)  # Attendre un peu que Telegram traite la photo
                    await account.get_profile_photo_path()
                except Exception as cache_error:
                    logger.warning(f"Impossible de mettre à jour le cache de la photo: {cache_error}")
            
            return success, error
        except Exception as e:
            error_msg = f"Erreur mise à jour photo profil: {e}"
            logger.error(error_msg)
            return False, error_msg

