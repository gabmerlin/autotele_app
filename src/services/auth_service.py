"""
Service d'authentification avec Supabase
"""
import asyncio
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import json
from pathlib import Path

try:
    from supabase import create_client, Client
except ImportError:
    create_client = None
    Client = None

from utils.logger import get_logger
from utils.config import Config

logger = get_logger()


class AuthService:
    """Gère l'authentification et les sessions utilisateur via Supabase"""
    
    def __init__(self):
        self.config = Config()
        self.supabase: Optional[Client] = None
        self.current_user: Optional[Dict[str, Any]] = None
        self._session_file = Path("config/.user_session")
        self._initialize_supabase()
    
    def _initialize_supabase(self):
        """Initialise le client Supabase"""
        try:
            # SÉCURITÉ : Charger la config depuis .env (pas depuis app_config.json)
            supabase_config = self.config.get_supabase_config()
            url = supabase_config.get('url', '')
            anon_key = supabase_config.get('anon_key', '')
            
            if not url or not anon_key:
                logger.warning("Configuration Supabase manquante")
                return
            
            if create_client is None:
                logger.error("Module supabase non disponible. Installez-le avec: pip install supabase")
                return
            
            # Créer le client Supabase
            self.supabase = create_client(
                supabase_url=url,
                supabase_key=anon_key
            )
            
        except ValueError as e:
            # Erreur de configuration (secrets manquants dans .env)
            logger.error(f"❌ Configuration Supabase invalide: {e}")
            self.supabase = None
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de Supabase: {e}")
    
    async def sign_up(self, email: str, password: str, metadata: Optional[Dict] = None) -> tuple[bool, str]:
        """
        Crée un nouveau compte utilisateur
        
        Args:
            email: Email de l'utilisateur
            password: Mot de passe
            metadata: Métadonnées supplémentaires (nom, etc.)
        
        Returns:
            (succès, message)
        """
        try:
            if not self.supabase:
                return False, "Service d'authentification non disponible"
            
            # Créer le compte
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": metadata or {}
                }
            })
            
            if response.user:
                return True, "Compte créé avec succès. Vérifiez votre email pour confirmer."
            else:
                return False, "Erreur lors de la création du compte"
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erreur lors de l'inscription: {error_msg}")
            
            if "already registered" in error_msg.lower():
                return False, "Cet email est déjà utilisé"
            elif "password" in error_msg.lower():
                return False, "Le mot de passe doit contenir au moins 6 caractères"
            else:
                return False, f"Erreur: {error_msg}"
    
    async def sign_in(self, email: str, password: str) -> tuple[bool, str]:
        """
        Connecte un utilisateur existant
        
        Args:
            email: Email de l'utilisateur
            password: Mot de passe
        
        Returns:
            (succès, message)
        """
        try:
            if not self.supabase:
                return False, "Service d'authentification non disponible"
            
            # Connexion
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                self.current_user = {
                    "id": response.user.id,
                    "email": response.user.email,
                    "metadata": response.user.user_metadata,
                    "session": {
                        "access_token": response.session.access_token,
                        "refresh_token": response.session.refresh_token,
                        "expires_at": response.session.expires_at
                    }
                }
                
                # Sauvegarder la session localement
                await self._save_session()
                
                return True, "Connexion réussie"
            else:
                return False, "Email ou mot de passe incorrect"
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Erreur lors de la connexion: {error_msg}")
            
            if "invalid" in error_msg.lower() or "credentials" in error_msg.lower():
                return False, "Email ou mot de passe incorrect"
            else:
                return False, f"Erreur: {error_msg}"
    
    async def sign_out(self) -> tuple[bool, str]:
        """Déconnecte l'utilisateur actuel"""
        try:
            if self.supabase and self.current_user:
                self.supabase.auth.sign_out()
            
            self.current_user = None
            
            # Supprimer la session locale
            if self._session_file.exists():
                self._session_file.unlink()
            
            return True, "Déconnexion réussie"
            
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {e}")
            return False, f"Erreur: {str(e)}"
    
    async def restore_session(self) -> bool:
        """Restaure une session sauvegardée si elle est valide"""
        try:
            if not self._session_file.exists():
                return False
            
            # Lire la session sauvegardée
            with open(self._session_file, 'r') as f:
                session_data = json.load(f)
            
            # Vérifier l'expiration
            expires_at = session_data.get('session', {}).get('expires_at', 0)
            if datetime.now().timestamp() >= expires_at:
                self._session_file.unlink()
                return False
            
            # Restaurer la session dans Supabase
            if self.supabase:
                access_token = session_data.get('session', {}).get('access_token')
                refresh_token = session_data.get('session', {}).get('refresh_token')
                
                if access_token and refresh_token:
                    self.supabase.auth.set_session(access_token, refresh_token)
                    self.current_user = session_data
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Erreur lors de la restauration de session: {e}")
            if self._session_file.exists():
                self._session_file.unlink()
            return False
    
    async def _save_session(self):
        """Sauvegarde la session actuelle localement"""
        try:
            if self.current_user:
                self._session_file.parent.mkdir(exist_ok=True)
                with open(self._session_file, 'w') as f:
                    json.dump(self.current_user, f)
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de session: {e}")
    
    def is_authenticated(self) -> bool:
        """Vérifie si un utilisateur est connecté"""
        return self.current_user is not None
    
    def get_user_id(self) -> Optional[str]:
        """Retourne l'ID de l'utilisateur connecté"""
        return self.current_user.get('id') if self.current_user else None
    
    def get_user_email(self) -> Optional[str]:
        """Retourne l'email de l'utilisateur connecté"""
        return self.current_user.get('email') if self.current_user else None
    
    async def reset_password(self, email: str) -> tuple[bool, str]:
        """Envoie un email de réinitialisation de mot de passe"""
        try:
            if not self.supabase:
                return False, "Service d'authentification non disponible"
            
            self.supabase.auth.reset_password_for_email(email)
            return True, "Email de réinitialisation envoyé"
            
        except Exception as e:
            logger.error(f"Erreur lors de la réinitialisation: {e}")
            return False, f"Erreur: {str(e)}"
    
    async def update_user_metadata(self, metadata: Dict[str, Any]) -> tuple[bool, str]:
        """Met à jour les métadonnées de l'utilisateur"""
        try:
            if not self.supabase or not self.current_user:
                return False, "Utilisateur non connecté"
            
            response = self.supabase.auth.update_user({
                "data": metadata
            })
            
            if response.user:
                self.current_user['metadata'].update(metadata)
                await self._save_session()
                return True, "Profil mis à jour"
            else:
                return False, "Erreur lors de la mise à jour"
                
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour: {e}")
            return False, f"Erreur: {str(e)}"


# Instance singleton
_auth_service = None

def get_auth_service() -> AuthService:
    """Retourne l'instance singleton du service d'authentification"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service

