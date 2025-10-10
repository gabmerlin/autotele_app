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
                
                # Vérifier si le fichier de session existe
                session_file = self.session_manager.get_session_file_path(session_id)
                if not session_file.exists():
                    self.session_manager.delete_session(session_id)
                    continue
                
                # Utiliser les credentials du fichier ou les credentials par défaut
                _api_id = int(session_info.get("api_id", api_id))
                _api_hash = session_info.get("api_hash", api_hash)
                
                account = TelegramAccount(
                    session_id,
                    session_info["phone"],
                    _api_id,
                    _api_hash,
                    session_info.get("account_name")
                )
                
                # Créer le client
                session_file_str = str(session_file)
                account.client = TelegramClient(session_file_str, account.api_id, account.api_hash)
                
                # Tenter de se connecter
                connected = await account.connect()
                if connected:
                    self.accounts[session_id] = account
                    if progress_callback:
                        progress_callback(progress, f"✓ {account_name} connecté")
                else:
                    # Garder dans les comptes mais marquer comme non autorisé
                    account.is_connected = False
                    self.accounts[session_id] = account
                    self.session_manager.update_session_status(session_id, "unauthorized")
                    if progress_callback:
                        progress_callback(progress, f"⚠ {account_name} non autorisé")
                    
            except Exception as e:
                logger.error(f"Erreur chargement session {session_info.get('phone', 'unknown')}: {e}")
                if progress_callback:
                    progress_callback(progress, f"✗ Erreur: {session_info.get('account_name', 'Compte')}")
        
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
        logger.info(f"Nom du compte mis à jour: {session_id} -> {account_name}")
    
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
        logger.info(f"Compte supprimé: {session_id}")
    
    async def disconnect_all(self) -> None:
        """Déconnecte tous les comptes."""
        for account in self.accounts.values():
            await account.disconnect()
        
        logger.info("Tous les comptes déconnectés")
    
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
                return True, f"✅ {account.phone} reconnecté avec succès"
            else:
                return False, f"❌ Échec de la reconnexion pour {account.phone}"
                
        except Exception as e:
            return False, f"❌ Erreur reconnexion {account.phone}: {str(e)}"

