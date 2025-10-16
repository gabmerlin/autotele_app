"""
Système de logs pour AutoTele avec anonymisation RGPD
"""
import os
import logging
import csv
import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import json

from utils.anonymizer import (
    anonymize_phone,
    anonymize_username,
    sanitize_message_preview,
    anonymize_group_ids
)


class AutoTeleLogger:
    """Logger personnalisé pour AutoTele"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuration du logger principal
        self.logger = logging.getLogger("AutoTele")
        self.logger.setLevel(logging.DEBUG)  # Activer DEBUG pour voir tous les logs
        
        # Handler pour fichier
        log_file = self.log_dir / f"autotele_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # Fichier DEBUG
        
        # Handler pour console (afficher INFO et plus seulement)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)  # Console reste sur INFO pour ne pas polluer
        
        # Format pour fichier (détaillé)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        # Format pour console (simplifié et coloré)
        console_formatter = logging.Formatter(
            '[%(levelname)s] %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        # Fichier d'historique des envois
        self.history_file = self.log_dir / "send_history.json"
        self._init_history()
    
    def _init_history(self):
        """Initialise le fichier d'historique"""
        if not self.history_file.exists():
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump([], f)
    
    def info(self, message: str):
        """Log un message info"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """Log un avertissement"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info=False):
        """Log une erreur avec sanitisation des données sensibles."""
        # Sanitiser le message principal
        sanitized_message = self._sanitize_sensitive_data(message)
        
        if exc_info:
            # Capturer la stack trace complète
            exc_text = traceback.format_exc()
            sanitized_trace = self._sanitize_sensitive_data(exc_text)
            
            # Logger le message en ERROR
            self.logger.error(sanitized_message)
            
            # Logger la stack trace complète en DEBUG uniquement
            self.logger.debug(f"Stack trace:\n{sanitized_trace}")
        else:
            self.logger.error(sanitized_message)
    
    def debug(self, message: str):
        """Log un message debug"""
        self.logger.debug(message)
    
    def log_scheduled_message(self, account: str, groups: List[str], 
                             message: str, schedule_time: datetime,
                             status: str = "scheduled"):
        """
        Log un message planifié avec anonymisation RGPD.
        
        Les données sensibles sont anonymisées :
        - Nom de compte : masqué
        - Liste de groupes : remplacée par un compteur + échantillon hashé
        - Message : remplacé par des statistiques (pas de contenu)
        """
        # Anonymiser les données sensibles
        account_anon = anonymize_username(account)
        message_info = sanitize_message_preview(message)
        
        # Convertir les IDs en int si nécessaire
        group_ids = [int(g) if isinstance(g, str) else g for g in groups]
        groups_sample = anonymize_group_ids(group_ids[:3])  # Échantillon de 3 premiers
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "account": account_anon,  # Anonymisé
            "groups_count": len(groups),  # Compte uniquement
            "groups_sample": groups_sample,  # IDs hashés
            "message_info": message_info,  # Stats uniquement
            "schedule_time": schedule_time.isoformat(),
            "status": status
        }
        
        history = self._read_history()
        history.append(entry)
        self._write_history(history)
        
        # Log console aussi anonymisé
        self.info(
            f"Message planifié - Compte: {account_anon}, "
            f"Groupes: {len(groups)}, Heure: {schedule_time}"
        )
    
    def log_send_result(self, task_id: str, group: str, success: bool, error: str = None):
        """
        Log le résultat d'un envoi avec anonymisation.
        
        Le nom du groupe est anonymisé pour la conformité RGPD.
        """
        from utils.anonymizer import hash_identifier
        
        # Anonymiser l'ID du groupe
        group_anon = hash_identifier(group, "grp")
        
        status = "success" if success else "failed"
        message = f"Envoi {status} - Groupe: {group_anon}"  # Anonymisé
        if error:
            # Ne pas logger le message d'erreur complet s'il contient des données sensibles
            error_type = error.split(':')[0] if ':' in error else "Erreur inconnue"
            message += f" - Type: {error_type}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def _read_history(self) -> List[Dict]:
        """Lit l'historique"""
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return []
    
    def _write_history(self, history: List[Dict]):
        """Écrit l'historique"""
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def get_history(self, limit: int = 100) -> List[Dict]:
        """Récupère l'historique des envois"""
        history = self._read_history()
        return history[-limit:]
    
    def export_history_csv(self, output_path: str):
        """Exporte l'historique en CSV"""
        history = self._read_history()
        
        if not history:
            return
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=history[0].keys())
            writer.writeheader()
            writer.writerows(history)
        
        self.info(f"Historique exporté vers {output_path}")
    
    def clear_old_logs(self, days: int = 30):
        """Supprime les logs de plus de X jours"""
        cutoff = datetime.now().timestamp() - (days * 86400)
        
        for log_file in self.log_dir.glob("autotele_*.log"):
            if log_file.stat().st_mtime < cutoff:
                log_file.unlink()
                self.info(f"Log ancien supprimé: {log_file.name}")
    
    def _sanitize_sensitive_data(self, text: str) -> str:
        """
        Masque les données sensibles dans les logs.
        
        SÉCURITÉ: Retire les numéros de téléphone, chemins, tokens, etc.
        pour éviter l'exposition de données sensibles dans les logs.
        
        Args:
            text: Texte à sanitiser (message ou stack trace)
            
        Returns:
            str: Texte avec données sensibles masquées
        """
        if not text:
            return text
        
        # Masquer les numéros de téléphone (format international)
        text = re.sub(r'\+?\d{10,15}', '+XXX...XXX', text)
        
        # Masquer les IDs de session
        text = re.sub(r'session_\d+', 'session_XXX', text)
        
        # Masquer les chemins complets Windows
        text = re.sub(r'[A-Z]:\\Users\\[^\\]+', r'C:\\Users\\XXX', text)
        text = re.sub(r'[A-Z]:\\[^\\]+\\[^\\]+\\Desktop', r'C:\\XXX\\Desktop', text)
        
        # Masquer les chemins complets Unix
        text = re.sub(r'/home/[^/]+', '/home/XXX', text)
        text = re.sub(r'/Users/[^/]+', '/Users/XXX', text)
        
        # Masquer les tokens, clés, passwords dans les tracebacks
        # Pattern 1: key = "value" ou key: "value"
        text = re.sub(
            r'(token|key|password|secret|api_id|api_hash|encryption_key)(\s*[:=]\s*["\']?)([a-zA-Z0-9_\-\.]+)',
            r'\1\2XXX',
            text,
            flags=re.IGNORECASE
        )
        
        # Pattern 2: 'sk_live_xxxxx' ou autres tokens longs
        text = re.sub(
            r'(sk_|pk_|api_)[a-zA-Z0-9_]{10,}',
            r'\1XXX',
            text
        )
        
        # Masquer les emails
        text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 'email@XXX.com', text)
        
        # Masquer les adresses IP
        text = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'XXX.XXX.XXX.XXX', text)
        
        return text


# Instance globale
_logger = None

def get_logger() -> AutoTeleLogger:
    """Récupère l'instance du logger"""
    global _logger
    if _logger is None:
        _logger = AutoTeleLogger()
    return _logger

