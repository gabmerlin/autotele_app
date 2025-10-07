"""
Gestion de la configuration de l'application
"""
import json
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Gestionnaire de configuration"""
    
    DEFAULT_CONFIG = {
        "app": {
            "name": "AutoTele",
            "version": "1.0.0",
            "language": "fr"
        },
        "telegram": {
            "rate_limit_delay": 3,  # secondes entre chaque message
            "max_messages_per_minute": 20,
            "max_groups_warning": 50
        },
        "btcpay": {
            "server_url": "",
            "store_id": "",
            "api_key": "",
            "webhook_secret": "",
            "subscription_price": 29.99,
            "currency": "EUR",
            "trial_days": 7,
            "check_interval_hours": 24
        },
        "security": {
            "session_encryption": True,
            "auto_logout_minutes": 0,  # 0 = désactivé
            "require_password": False
        },
        "ui": {
            "theme": "light",
            "font_family": "Segoe UI",
            "font_size": 10,
            "show_notifications": True
        },
        "paths": {
            "sessions_dir": "sessions",
            "logs_dir": "logs",
            "config_dir": "config",
            "temp_dir": "temp"
        }
    }
    
    def __init__(self, config_file: str = "config/app_config.json"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Charge la configuration depuis le fichier"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge avec les valeurs par défaut
                    return self._merge_configs(self.DEFAULT_CONFIG.copy(), loaded)
            except Exception as e:
                print(f"Erreur lors du chargement de la config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Créer la configuration par défaut
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Merge récursif des configurations"""
        for key, value in loaded.items():
            if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                default[key] = self._merge_configs(default[key], value)
            else:
                default[key] = value
        return default
    
    def _save_config(self, config: Dict[str, Any]):
        """Sauvegarde la configuration"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
    
    def get(self, key_path: str, default=None):
        """
        Récupère une valeur de configuration
        Ex: config.get("btcpay.server_url")
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Définit une valeur de configuration
        Ex: config.set("btcpay.server_url", "https://...")
        """
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self._save_config(self.config)
    
    def get_btcpay_config(self) -> Dict[str, Any]:
        """Récupère la configuration BTCPay"""
        return self.config.get("btcpay", {})
    
    def set_btcpay_config(self, **kwargs):
        """Configure BTCPay"""
        for key, value in kwargs.items():
            self.set(f"btcpay.{key}", value)
    
    def ensure_directories(self):
        """Crée les répertoires nécessaires"""
        for dir_key in ["sessions_dir", "logs_dir", "config_dir", "temp_dir"]:
            dir_path = Path(self.get(f"paths.{dir_key}"))
            dir_path.mkdir(parents=True, exist_ok=True)


# Instance globale
_config = None

def get_config() -> Config:
    """Récupère l'instance de configuration"""
    global _config
    if _config is None:
        _config = Config()
        _config.ensure_directories()
    return _config

