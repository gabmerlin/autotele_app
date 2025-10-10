"""
Gestionnaire de sessions Telegram
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from utils.logger import get_logger
from utils.config import get_config


class SessionManager:
    """Gère les sessions Telegram"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.sessions_dir = Path(self.config.get("paths.sessions_dir"))
        self.sessions_dir.mkdir(exist_ok=True)
        
        # Fichier d'index des sessions
        self.index_file = self.sessions_dir / "sessions_index.json"
        self.sessions_index = self._load_index()
    
    def _load_index(self) -> Dict:
        """Charge l'index des sessions"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Erreur chargement index sessions: {e}")
                return {}
        return {}
    
    def _save_index(self):
        """Sauvegarde l'index des sessions"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.sessions_index, f, indent=2, ensure_ascii=False)
    
    def create_session_entry(self, phone: str, api_id: str, api_hash: str, 
                            account_name: str = None) -> str:
        """
        Crée une entrée de session
        Retourne l'ID de session
        """
        session_id = f"session_{phone.replace('+', '')}"
        
        # Le premier compte ajouté devient automatiquement le compte maître
        is_first_account = len(self.sessions_index) == 0
        
        entry = {
            "session_id": session_id,
            "phone": phone,
            "api_id": api_id,
            "api_hash": api_hash,
            "account_name": account_name or phone,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "status": "active",
            "is_master": is_first_account  # Premier compte = maître
        }
        
        self.sessions_index[session_id] = entry
        self._save_index()
        
        self.logger.info(f"Session créée: {session_id} (Maître: {is_first_account})")
        return session_id
    
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Récupère les informations d'une session"""
        return self.sessions_index.get(session_id)
    
    def list_sessions(self) -> List[Dict]:
        """Liste toutes les sessions"""
        return list(self.sessions_index.values())
    
    def update_last_used(self, session_id: str):
        """Met à jour la date de dernière utilisation"""
        if session_id in self.sessions_index:
            self.sessions_index[session_id]["last_used"] = datetime.now().isoformat()
            self._save_index()
    
    def delete_session(self, session_id: str):
        """Supprime une session"""
        if session_id in self.sessions_index:
            # Supprimer le fichier de session
            session_file = self.sessions_dir / f"{session_id}.session"
            encrypted_file = self.sessions_dir / f"{session_id}.enc"
            
            if session_file.exists():
                session_file.unlink()
            if encrypted_file.exists():
                encrypted_file.unlink()
            
            # Retirer de l'index
            del self.sessions_index[session_id]
            self._save_index()
            
            self.logger.info(f"Session supprimée: {session_id}")
    
    def get_session_file_path(self, session_id: str) -> Path:
        """Retourne le chemin du fichier de session"""
        return self.sessions_dir / f"{session_id}.session"
    
    def update_session_status(self, session_id: str, status: str):
        """Met à jour le statut d'une session"""
        if session_id in self.sessions_index:
            self.sessions_index[session_id]["status"] = status
            self._save_index()
    
    def get_active_sessions(self) -> List[Dict]:
        """Récupère les sessions actives"""
        return [
            session for session in self.sessions_index.values()
            if session.get("status") == "active"
        ]
    
    def update_account_name(self, session_id: str, account_name: str):
        """Met à jour le nom d'un compte"""
        if session_id in self.sessions_index:
            self.sessions_index[session_id]["account_name"] = account_name
            self._save_index()
            self.logger.info(f"Nom du compte mis à jour pour: {session_id}")
    
    def update_account_settings(self, session_id: str, default_message: str = None, 
                               default_schedules: List[str] = None):
        """Met à jour les paramètres prédéfinis d'un compte"""
        if session_id in self.sessions_index:
            if default_message is not None:
                self.sessions_index[session_id]["default_message"] = default_message
            if default_schedules is not None:
                self.sessions_index[session_id]["default_schedules"] = default_schedules
            self._save_index()
            self.logger.info(f"Paramètres mis à jour pour: {session_id}")
    
    def get_account_settings(self, session_id: str) -> Dict:
        """Récupère les paramètres prédéfinis d'un compte"""
        session = self.sessions_index.get(session_id, {})
        return {
            "default_message": session.get("default_message", ""),
            "default_schedules": session.get("default_schedules", []),
            "is_master": session.get("is_master", False)
        }
    
    def get_master_account(self) -> Optional[str]:
        """Retourne le session_id du compte maître"""
        for session_id, session in self.sessions_index.items():
            if session.get("is_master", False):
                return session_id
        return None
    
    def set_master_account(self, session_id: str) -> bool:
        """
        Définit un compte comme compte maître.
        Enlève automatiquement le statut maître des autres comptes (exclusivité).
        
        Args:
            session_id: ID de la session à définir comme maître
            
        Returns:
            bool: True si réussi, False sinon
        """
        if session_id not in self.sessions_index:
            return False
        
        # Retirer le statut maître de tous les comptes
        for sid in self.sessions_index:
            self.sessions_index[sid]["is_master"] = False
        
        # Définir le nouveau compte maître
        self.sessions_index[session_id]["is_master"] = True
        self._save_index()
        
        self.logger.info(f"Compte maître défini: {session_id}")
        return True
    
    def is_master_account(self, session_id: str) -> bool:
        """Vérifie si un compte est le compte maître"""
        session = self.sessions_index.get(session_id, {})
        return session.get("is_master", False)
    
    def can_unset_master(self, session_id: str) -> bool:
        """
        Vérifie si on peut retirer le statut maître d'un compte.
        Impossible si c'est le seul compte.
        
        Returns:
            bool: True si on peut retirer le statut, False sinon
        """
        # Compter le nombre de comptes actifs
        active_sessions = [s for s in self.sessions_index.values() if s.get("status") == "active"]
        return len(active_sessions) > 1

