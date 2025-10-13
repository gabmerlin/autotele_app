"""Gestionnaire de sessions Telegram avec chiffrement automatique."""
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from utils.config import get_config
from utils.logger import get_logger


class SessionManager:
    """Gère les sessions Telegram avec un système de chiffrement optionnel."""

    def __init__(self):
        """Initialise le gestionnaire de sessions."""
        self.config = get_config()
        self.logger = get_logger()
        self.sessions_dir = Path(self.config.get("paths.sessions_dir"))
        self.sessions_dir.mkdir(exist_ok=True)

        self.index_file = self.sessions_dir / "sessions_index.json"
        self.sessions_index = self._load_index()

        # Système de chiffrement - Désactivé pour stabilité
        # Le module est disponible dans src/utils/encryption.py
        # Pour activer : décommenter le code ci-dessous
        self.encryption = None

        # Pour réactiver le chiffrement AES-256:
        # try:
        #     from utils.encryption import get_encryption
        #     self.encryption = get_encryption()
        #     self.logger.info("Chiffrement des sessions activé (AES-256)")
        # except ValueError as e:
        #     self.logger.warning(f"Chiffrement désactivé: {e}")
        #     self.encryption = None
    
    def _load_index(self) -> Dict:
        """Charge l'index des sessions depuis le fichier JSON."""
        if not self.index_file.exists():
            return {}

        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Erreur chargement index sessions: {e}")
            return {}

    def _save_index(self) -> None:
        """Sauvegarde l'index des sessions dans le fichier JSON."""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.sessions_index,
                    f,
                    indent=2,
                    ensure_ascii=False
                )
        except Exception as e:
            self.logger.error(f"Erreur sauvegarde index sessions: {e}")
    
    def create_session_entry(
        self,
        phone: str,
        api_id: str,
        api_hash: str,
        account_name: Optional[str] = None
    ) -> str:
        """
        Crée une entrée de session.

        SÉCURITÉ : Les api_id et api_hash ne sont PAS stockés dans l'index.
        Ils sont chargés depuis le fichier .env à chaque utilisation.

        Args:
            phone: Numéro de téléphone.
            api_id: API ID (non stocké, paramètre legacy).
            api_hash: API Hash (non stocké, paramètre legacy).
            account_name: Nom du compte (optionnel).

        Returns:
            str: ID de la session créée.
        """
        session_id = f"session_{phone.replace('+', '')}"

        # Le premier compte ajouté devient automatiquement le compte maître
        is_first_account = len(self.sessions_index) == 0

        entry = {
            "session_id": session_id,
            "phone": phone,
            "account_name": account_name or phone,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "status": "active",
            "is_master": is_first_account
        }

        self.sessions_index[session_id] = entry
        self._save_index()

        return session_id
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Récupère les informations d'une session."""
        return self.sessions_index.get(session_id)

    def list_sessions(self) -> List[Dict]:
        """Liste toutes les sessions disponibles."""
        return list(self.sessions_index.values())

    def update_last_used(self, session_id: str) -> None:
        """Met à jour la date de dernière utilisation d'une session."""
        if session_id in self.sessions_index:
            self.sessions_index[session_id]["last_used"] = (
                datetime.now().isoformat()
            )
            self._save_index()

    def delete_session(self, session_id: str) -> None:
        """Supprime une session et ses fichiers associés."""
        if session_id not in self.sessions_index:
            return

        # Supprimer les fichiers de session
        session_file = self.sessions_dir / f"{session_id}.session"
        encrypted_file = self.sessions_dir / f"{session_id}.enc"

        for file in [session_file, encrypted_file]:
            if file.exists():
                file.unlink()

        # Retirer de l'index
        del self.sessions_index[session_id]
        self._save_index()
    
    def get_session_file_path(
        self,
        session_id: str,
        encrypted: bool = True
    ) -> Path:
        """
        Retourne le chemin du fichier de session.

        Args:
            session_id: ID de la session.
            encrypted: Si True, retourne le chemin du fichier chiffré,
                      sinon le chemin du fichier non chiffré.

        Returns:
            Path: Chemin du fichier de session.

        Note:
            TelegramClient ajoute automatiquement .session à la fin du nom.
            Donc si on passe "session_xxx.enc", il crée
            "session_xxx.enc.session".
        """
        if encrypted and self.encryption:
            return self.sessions_dir / f"{session_id}.enc"
        return self.sessions_dir / f"{session_id}.session"
    
    def get_session_for_client(self, session_id: str) -> str:
        """
        Retourne le chemin de la session pour TelegramClient.

        Déchiffre automatiquement la session si le chiffrement est activé.

        Args:
            session_id: ID de la session.

        Returns:
            str: Chemin du fichier de session (déchiffré si nécessaire).
        """
        if not self.encryption:
            return str(self.get_session_file_path(session_id,
                                                   encrypted=False))

        encrypted_path = self.get_session_file_path(session_id,
                                                     encrypted=True)
        decrypted_path = self.get_session_file_path(session_id,
                                                     encrypted=False)

        # Si le fichier chiffré existe, le déchiffrer temporairement
        if encrypted_path.exists():
            success, msg, path = self.encryption.decrypt_session_file(
                encrypted_path,
                decrypted_path
            )
            if success and path:
                # Retourner sans .session (Telethon l'ajoute automatiquement)
                return str(path.with_suffix(''))

            self.logger.error(
                f"Erreur déchiffrement session {session_id}: {msg}"
            )
            # Fallback sur fichier non chiffré si existe
            if decrypted_path.exists():
                return str(decrypted_path.with_suffix(''))

        # Si aucun fichier n'existe, retourner le chemin attendu
        return str(decrypted_path.with_suffix(''))
    
    def update_session_status(self, session_id: str, status: str) -> None:
        """Met à jour le statut d'une session."""
        if session_id in self.sessions_index:
            self.sessions_index[session_id]["status"] = status
            self._save_index()

    def get_active_sessions(self) -> List[Dict]:
        """Récupère uniquement les sessions actives."""
        return [
            session for session in self.sessions_index.values()
            if session.get("status") == "active"
        ]

    def update_account_name(self, session_id: str,
                           account_name: str) -> None:
        """Met à jour le nom d'un compte."""
        if session_id in self.sessions_index:
            self.sessions_index[session_id]["account_name"] = account_name
            self._save_index()

    def update_account_settings(
        self,
        session_id: str,
        default_message: Optional[str] = None,
        default_schedules: Optional[List[str]] = None
    ) -> None:
        """Met à jour les paramètres prédéfinis d'un compte."""
        if session_id not in self.sessions_index:
            return

        if default_message is not None:
            self.sessions_index[session_id]["default_message"] = (
                default_message
            )
        if default_schedules is not None:
            self.sessions_index[session_id]["default_schedules"] = (
                default_schedules
            )
        self._save_index()
    
    def get_account_settings(self, session_id: str) -> Dict:
        """Récupère les paramètres prédéfinis d'un compte."""
        session = self.sessions_index.get(session_id, {})
        return {
            "default_message": session.get("default_message", ""),
            "default_schedules": session.get("default_schedules", []),
            "is_master": session.get("is_master", False)
        }

    def get_master_account(self) -> Optional[str]:
        """Retourne le session_id du compte maître."""
        for session_id, session in self.sessions_index.items():
            if session.get("is_master", False):
                return session_id
        return None

    def set_master_account(self, session_id: str) -> bool:
        """
        Définit un compte comme compte maître.

        Enlève automatiquement le statut maître des autres comptes
        (exclusivité).

        Args:
            session_id: ID de la session à définir comme maître.

        Returns:
            bool: True si réussi, False sinon.
        """
        if session_id not in self.sessions_index:
            return False

        # Retirer le statut maître de tous les comptes
        for sid in self.sessions_index:
            self.sessions_index[sid]["is_master"] = False

        # Définir le nouveau compte maître
        self.sessions_index[session_id]["is_master"] = True
        self._save_index()

        return True

    def is_master_account(self, session_id: str) -> bool:
        """Vérifie si un compte est le compte maître."""
        session = self.sessions_index.get(session_id, {})
        return session.get("is_master", False)

    def can_unset_master(self, session_id: str) -> bool:
        """
        Vérifie si on peut retirer le statut maître d'un compte.

        Impossible si c'est le seul compte actif.

        Args:
            session_id: ID de la session (non utilisé mais gardé
                       pour compatibilité).

        Returns:
            bool: True si on peut retirer le statut, False sinon.
        """
        active_sessions = [
            s for s in self.sessions_index.values()
            if s.get("status") == "active"
        ]
        return len(active_sessions) > 1

