"""
Gestion de la configuration de l'application
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env (fallback si pas de config embarquée)
load_dotenv()


class Config:
    """Gestionnaire de configuration avec validation."""
    
    # Règles de validation pour les valeurs de configuration
    VALIDATION_RULES = {
        'telegram.rate_limit_delay': {
            'type': (int, float),
            'min': 0.01,
            'max': 60,
            'description': 'Délai entre les requêtes (secondes)'
        },
        'telegram.max_messages_per_minute': {
            'type': int,
            'min': 1,
            'max': 100,
            'description': 'Nombre maximum de messages par minute'
        },
        'telegram.max_groups_warning': {
            'type': int,
            'min': 1,
            'max': 10000,
            'description': 'Seuil d\'avertissement pour le nombre de groupes'
        },
        'telegram.max_parallel_tasks': {
            'type': int,
            'min': 1,
            'max': 20,
            'description': 'Nombre maximum de tâches parallèles'
        },
        'telegram.scheduler_interval': {
            'type': (int, float),
            'min': 0.1,
            'max': 60,
            'description': 'Intervalle du planificateur (secondes)'
        },
        'btcpay.trial_days': {
            'type': int,
            'min': 0,
            'max': 365,
            'description': 'Jours d\'essai gratuit'
        },
        'btcpay.check_interval_hours': {
            'type': (int, float),
            'min': 0.1,
            'max': 720,
            'description': 'Intervalle de vérification (heures)'
        },
        'security.auto_logout_minutes': {
            'type': int,
            'min': 0,
            'max': 1440,
            'description': 'Déconnexion automatique (minutes, 0=désactivé)'
        },
        'ui.font_size': {
            'type': int,
            'min': 6,
            'max': 72,
            'description': 'Taille de police'
        },
    }
    
    DEFAULT_CONFIG = {
        "app": {
            "name": "AutoTele",
            "version": "1.0.0",
            "language": "fr"
        },
        "telegram": {
            "max_groups_warning": 50,
            "rate_limit_delay": 0.05,  # 50ms entre messages (20 req/sec)
            "max_parallel_tasks": 5,   # Maximum 5 comptes en parallèle
            "scheduler_interval": 2    # Vérification toutes les 2 secondes
        },
        "btcpay": {
            "_note": "SÉCURITÉ : server_url, store_id, api_key, webhook_secret, subscription_price et currency sont dans .env CHIFFRÉ",
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
        """
        Charge la configuration depuis la config embarquée (chiffrée) ou le fichier.
        PRIORITÉ : 1. Config embarquée chiffrée, 2. Fichier JSON, 3. Valeurs par défaut
        """
        # Essayer de charger depuis la config embarquée (chiffrée)
        try:
            from utils.embedded_config import get_embedded_app_config
            embedded_config = get_embedded_app_config()
            
            if embedded_config:
                # Config embarquée trouvée - l'utiliser
                merged = self._merge_configs(self.DEFAULT_CONFIG.copy(), embedded_config)
                self._validate_config(merged)
                print("Configuration chargee depuis config embarquee (chiffree)")
                return merged
        except Exception as e:
            print(f"Impossible de charger config embarquee: {e}")
        
        # Fallback : charger depuis le fichier JSON (dev uniquement)
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # Merge avec les valeurs par défaut
                    merged = self._merge_configs(self.DEFAULT_CONFIG.copy(), loaded)
                    # Valider la configuration
                    self._validate_config(merged)
                    print(f"Configuration chargee depuis fichier: {self.config_file}")
                    return merged
            except Exception as e:
                print(f"Erreur lors du chargement de la config: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Créer la configuration par défaut (dev uniquement)
            print("Aucune config trouvee - Utilisation valeurs par defaut")
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
        Définit une valeur de configuration avec validation.
        Ex: config.set("btcpay.server_url", "https://...")
        """
        # Valider la valeur avant de l'affecter
        if not self._validate_value(key_path, value):
            raise ValueError(f"Valeur invalide pour {key_path}: {value}")
        
        keys = key_path.split('.')
        config = self.config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        self._save_config(self.config)
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Valide l'ensemble de la configuration.
        
        Args:
            config: Configuration à valider
        
        Returns:
            bool: True si valide
        """
        is_valid = True
        
        for key_path, rules in self.VALIDATION_RULES.items():
            value = self._get_nested_value(config, key_path)
            
            if value is not None:
                if not self._validate_value(key_path, value, silent=True):
                    is_valid = False
                    # Remplacer par la valeur par défaut
                    default_value = self._get_nested_value(self.DEFAULT_CONFIG, key_path)
                    if default_value is not None:
                        print(f"ATTENTION: Config invalide pour {key_path}, utilisation de la valeur par defaut: {default_value}")
                        self._set_nested_value(config, key_path, default_value)
        
        return is_valid
    
    def _validate_value(self, key_path: str, value: Any, silent: bool = False) -> bool:
        """
        Valide une valeur de configuration selon les règles.
        
        Args:
            key_path: Chemin de la clé (ex: "telegram.rate_limit_delay")
            value: Valeur à valider
            silent: Si True, ne log pas les erreurs
        
        Returns:
            bool: True si la valeur est valide
        """
        # Si pas de règle de validation, accepter la valeur
        if key_path not in self.VALIDATION_RULES:
            return True
        
        rules = self.VALIDATION_RULES[key_path]
        description = rules.get('description', key_path)
        
        # Validation du type
        expected_type = rules.get('type')
        if expected_type:
            # Gérer le cas où plusieurs types sont acceptés
            if isinstance(expected_type, tuple):
                if not isinstance(value, expected_type):
                    if not silent:
                        print(f"ERREUR {description}: type invalide (attendu {expected_type}, obtenu {type(value).__name__})")
                    return False
            else:
                if not isinstance(value, expected_type):
                    if not silent:
                        print(f"ERREUR {description}: type invalide (attendu {expected_type.__name__}, obtenu {type(value).__name__})")
                    return False
        
        # Validation de la valeur minimale
        if 'min' in rules:
            if value < rules['min']:
                if not silent:
                    print(f"ERREUR {description}: valeur trop petite (min: {rules['min']}, obtenu: {value})")
                return False
        
        # Validation de la valeur maximale
        if 'max' in rules:
            if value > rules['max']:
                if not silent:
                    print(f"ERREUR {description}: valeur trop grande (max: {rules['max']}, obtenu: {value})")
                return False
        
        # Validation de pattern regex
        if 'pattern' in rules and isinstance(value, str):
            import re
            if not re.match(rules['pattern'], value):
                if not silent:
                    print(f"ERREUR {description}: format invalide (pattern: {rules['pattern']})")
                return False
        
        return True
    
    def _get_nested_value(self, config: Dict, key_path: str) -> Any:
        """Récupère une valeur imbriquée dans la config."""
        keys = key_path.split('.')
        value = config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _set_nested_value(self, config: Dict, key_path: str, value: Any):
        """Définit une valeur imbriquée dans la config."""
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def get_supabase_config(self) -> Dict[str, str]:
        """
        Récupère la configuration Supabase depuis les variables d'environnement.
        
        SÉCURITÉ : Les secrets Supabase sont chargés depuis .env, 
        PAS depuis app_config.json
        
        Returns:
            Dict avec 'url' et 'anon_key'
        
        Raises:
            ValueError: Si les variables d'environnement ne sont pas définies
        """
        url = os.getenv('SUPABASE_URL')
        anon_key = os.getenv('SUPABASE_ANON_KEY')
        
        if not url or not anon_key:
            raise ValueError(
                "Configuration Supabase manquante !\n\n"
                "Veuillez définir dans votre fichier .env :\n"
                "  SUPABASE_URL=votre_url\n"
                "  SUPABASE_ANON_KEY=votre_cle\n\n"
                "Consultez .env.example pour un modèle"
            )
        
        return {
            'url': url,
            'anon_key': anon_key
        }
    
    def get_btcpay_config(self) -> Dict[str, Any]:
        """
        Récupère la configuration BTCPay depuis les variables d'environnement.
        
        SÉCURITÉ : Les secrets BTCPay sont chargés depuis .env,
        PAS depuis app_config.json
        
        Returns:
            Dict avec 'server_url', 'store_id', 'api_key', 'webhook_secret'
            et les paramètres non-sensibles depuis app_config.json
        """
        # Charger les secrets depuis .env
        server_url = os.getenv('BTCPAY_SERVER_URL', '')
        store_id = os.getenv('BTCPAY_STORE_ID', '')
        api_key = os.getenv('BTCPAY_API_KEY', '')
        webhook_secret = os.getenv('BTCPAY_WEBHOOK_SECRET', '')
        
        # SÉCURITÉ : Charger subscription_price et currency depuis .env CHIFFRÉ (pas depuis app_config.json modifiable)
        subscription_price = float(os.getenv('SUBSCRIPTION_PRICE', '24.99'))
        currency = os.getenv('SUBSCRIPTION_CURRENCY', 'USD')
        
        # Charger les paramètres non-sensibles depuis app_config.json
        config_params = self.config.get("btcpay", {})
        
        # Merger : secrets + prix depuis .env, autres paramètres depuis fichier
        return {
            'server_url': server_url,
            'store_id': store_id,
            'api_key': api_key,
            'webhook_secret': webhook_secret,
            'subscription_price': subscription_price,  # Depuis .env chiffré
            'currency': currency,  # Depuis .env chiffré
            'trial_days': config_params.get('trial_days', 7),
            'check_interval_hours': config_params.get('check_interval_hours', 24)
        }
    
    def set_btcpay_config(self, **kwargs):
        """
        Configure les paramètres BTCPay NON-SENSIBLES.
        
        IMPORTANT : Cette méthode ne doit être utilisée que pour les paramètres
        non-sensibles (délais, etc.). Les secrets (API keys) ET le prix/currency
        doivent être définis dans .env CHIFFRÉ.
        """
        # Filtrer pour éviter de sauvegarder des secrets par erreur
        # SÉCURITÉ : subscription_price et currency ont été retirés - ils doivent rester dans .env chiffré
        safe_keys = ['trial_days', 'check_interval_hours']
        
        for key, value in kwargs.items():
            if key in safe_keys:
                self.set(f"btcpay.{key}", value)
            else:
                print(f"ATTENTION: '{key}' devrait etre defini dans .env, pas dans app_config.json")
    
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

