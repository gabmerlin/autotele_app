"""
Système de logs pour AutoTele
"""
import os
import logging
import csv
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import json


class AutoTeleLogger:
    """Logger personnalisé pour AutoTele"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Configuration du logger principal
        self.logger = logging.getLogger("AutoTele")
        self.logger.setLevel(logging.DEBUG)  # ✅ Activer DEBUG pour voir tous les logs
        
        # Handler pour fichier
        log_file = self.log_dir / f"autotele_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)  # ✅ Fichier DEBUG
        
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
        """Log une erreur"""
        self.logger.error(message, exc_info=exc_info)
    
    def debug(self, message: str):
        """Log un message debug"""
        self.logger.debug(message)
    
    def log_scheduled_message(self, account: str, groups: List[str], 
                             message: str, schedule_time: datetime,
                             status: str = "scheduled"):
        """Log un message planifié"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "account": account,
            "groups": groups,
            "message_preview": message[:100],
            "schedule_time": schedule_time.isoformat(),
            "status": status
        }
        
        history = self._read_history()
        history.append(entry)
        self._write_history(history)
        
        self.info(f"Message planifié - Compte: {account}, Groupes: {len(groups)}, Heure: {schedule_time}")
    
    def log_send_result(self, task_id: str, group: str, success: bool, error: str = None):
        """Log le résultat d'un envoi"""
        status = "success" if success else "failed"
        message = f"Envoi {status} - Groupe: {group}"
        if error:
            message += f" - Erreur: {error}"
        
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


# Instance globale
_logger = None

def get_logger() -> AutoTeleLogger:
    """Récupère l'instance du logger"""
    global _logger
    if _logger is None:
        _logger = AutoTeleLogger()
    return _logger

