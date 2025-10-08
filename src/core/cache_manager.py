"""
Gestionnaire de cache pour optimiser les performances
"""
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional


class CacheManager:
    """Gestionnaire de cache intelligent"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache en mémoire pour ultra rapidité
        self._memory_cache = {}
        self._cache_timestamps = {}
        
        # Durées de cache (en secondes)
        self.CACHE_DURATIONS = {
            "accounts": 300,      # 5 minutes
            "groups": 180,        # 3 minutes
            "scheduled_messages": 60,  # 1 minute
            "dialogs": 120,       # 2 minutes
        }
    
    def get(self, key: str, category: str = "default") -> Optional[Any]:
        """Récupère une valeur du cache"""
        cache_key = f"{category}:{key}"
        
        # Vérifier le cache mémoire d'abord
        if cache_key in self._memory_cache:
            if self._is_cache_valid(cache_key, category):
                return self._memory_cache[cache_key]
            else:
                # Cache expiré, le supprimer
                del self._memory_cache[cache_key]
                if cache_key in self._cache_timestamps:
                    del self._cache_timestamps[cache_key]
        
        # Vérifier le cache fichier
        return self._get_from_file(cache_key, category)
    
    def set(self, key: str, value: Any, category: str = "default") -> None:
        """Met une valeur en cache"""
        cache_key = f"{category}:{key}"
        
        # Mettre en cache mémoire (ultra rapide)
        self._memory_cache[cache_key] = value
        self._cache_timestamps[cache_key] = datetime.now()
        
        # Mettre en cache fichier (persistant)
        self._save_to_file(cache_key, value, category)
    
    def _is_cache_valid(self, cache_key: str, category: str) -> bool:
        """Vérifie si le cache est encore valide"""
        if cache_key not in self._cache_timestamps:
            return False
        
        duration = self.CACHE_DURATIONS.get(category, 60)
        age = (datetime.now() - self._cache_timestamps[cache_key]).total_seconds()
        return age < duration
    
    def _get_from_file(self, cache_key: str, category: str) -> Optional[Any]:
        """Récupère depuis le cache fichier"""
        try:
            cache_file = self.cache_dir / f"{category}.json"
            if not cache_file.exists():
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if cache_key in data:
                cache_data = data[cache_key]
                # Vérifier l'âge
                cache_time = datetime.fromisoformat(cache_data['timestamp'])
                duration = self.CACHE_DURATIONS.get(category, 60)
                
                if (datetime.now() - cache_time).total_seconds() < duration:
                    return cache_data['value']
                else:
                    # Cache expiré, le supprimer
                    del data[cache_key]
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
            
            return None
            
        except Exception:
            return None
    
    def _save_to_file(self, cache_key: str, value: Any, category: str) -> None:
        """Sauvegarde dans le cache fichier"""
        try:
            cache_file = self.cache_dir / f"{category}.json"
            
            # Charger les données existantes
            data = {}
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            
            # Ajouter la nouvelle entrée
            data[cache_key] = {
                'value': value,
                'timestamp': datetime.now().isoformat()
            }
            
            # Sauvegarder
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception:
            pass  # Ignorer les erreurs de cache
    
    def clear(self, category: str = None) -> None:
        """Vide le cache"""
        if category:
            # Vider une catégorie spécifique
            keys_to_remove = [k for k in self._memory_cache.keys() if k.startswith(f"{category}:")]
            for key in keys_to_remove:
                del self._memory_cache[key]
                if key in self._cache_timestamps:
                    del self._cache_timestamps[key]
            
            # Vider le fichier
            cache_file = self.cache_dir / f"{category}.json"
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Vider tout
            self._memory_cache.clear()
            self._cache_timestamps.clear()
            
            # Vider tous les fichiers
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
    
    def preload_accounts(self, telegram_manager) -> None:
        """Précharge les comptes en arrière-plan"""
        async def preload():
            try:
                accounts = telegram_manager.get_all_accounts()
                self.set("all_accounts", accounts, "accounts")
                print("🚀 Comptes préchargés dans le cache")
            except Exception as e:
                print(f"⚠️ Erreur préchargement comptes: {e}")
        
        asyncio.create_task(preload())
    
    def preload_groups(self, account_id: str, telegram_manager) -> None:
        """Précharge les groupes d'un compte en arrière-plan"""
        async def preload():
            try:
                account = telegram_manager.get_account(account_id)
                if account and account.is_connected:
                    dialogs = await account.get_dialogs()
                    self.set(f"dialogs_{account_id}", dialogs, "dialogs")
                    print(f"🚀 Groupes préchargés pour {account_id}")
            except Exception as e:
                print(f"⚠️ Erreur préchargement groupes: {e}")
        
        asyncio.create_task(preload())


# Instance globale
cache_manager = CacheManager()
