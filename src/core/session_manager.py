"""
Gestionnaire de sessions Telegram chiffrées
"""
import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from utils.crypto import SessionEncryptor
from utils.logger import get_logger
from utils.config import get_config


class SessionManager:
    """Gère les sessions Telegram chiffrées"""
    
    def __init__(self):
        self.config = get_config()
        self.logger = get_logger()
        self.encryptor = SessionEncryptor()
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
        
        entry = {
            "session_id": session_id,
            "phone": phone,
            "api_id": api_id,
            "api_hash": api_hash,
            "account_name": account_name or phone,
            "created_at": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "status": "active"
        }
        
        self.sessions_index[session_id] = entry
        self._save_index()
        
        self.logger.info(f"Session créée: {session_id}")
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
    
    def encrypt_session_file(self, session_id: str):
        """Chiffre un fichier de session"""
        session_file = self.get_session_file_path(session_id)
        encrypted_file = self.sessions_dir / f"{session_id}.enc"
        
        if session_file.exists():
            self.encryptor.encrypt_file(str(session_file), str(encrypted_file))
            # Optionnel : supprimer le fichier non chiffré
            # session_file.unlink()
            self.logger.info(f"Session chiffrée: {session_id}")
    
    def decrypt_session_file(self, session_id: str):
        """Déchiffre un fichier de session"""
        encrypted_file = self.sessions_dir / f"{session_id}.enc"
        session_file = self.get_session_file_path(session_id)
        
        if encrypted_file.exists():
            self.encryptor.decrypt_file(str(encrypted_file), str(session_file))
            self.logger.info(f"Session déchiffrée: {session_id}")
    
    def export_session(self, session_id: str, export_path: str):
        """Exporte une session chiffrée"""
        encrypted_file = self.sessions_dir / f"{session_id}.enc"
        
        if not encrypted_file.exists():
            # Chiffrer d'abord si nécessaire
            self.encrypt_session_file(session_id)
        
        # Copier le fichier chiffré
        import shutil
        shutil.copy(encrypted_file, export_path)
        
        self.logger.info(f"Session exportée: {session_id} -> {export_path}")
    
    def import_session(self, import_path: str, session_info: Dict) -> str:
        """Importe une session chiffrée"""
        session_id = session_info["session_id"]
        encrypted_file = self.sessions_dir / f"{session_id}.enc"
        
        # Copier le fichier
        import shutil
        shutil.copy(import_path, encrypted_file)
        
        # Ajouter à l'index
        self.sessions_index[session_id] = session_info
        self._save_index()
        
        self.logger.info(f"Session importée: {session_id}")
        return session_id
    
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

