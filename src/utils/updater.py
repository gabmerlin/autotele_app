"""
Système de vérification des mises à jour pour AutoTele.

Vérifie auprès d'un serveur distant (GitHub ou serveur custom) 
si une nouvelle version est disponible.
"""
import asyncio
import requests
import json
from pathlib import Path
from typing import Optional, Tuple
from packaging import version

from utils.logger import get_logger
from utils.constants import APP_VERSION

logger = get_logger()


class AutoUpdater:
    """Gestionnaire de mises à jour automatiques."""
    
    # URL de téléchargement par défaut (configurée localement)
    DEFAULT_DOWNLOAD_URL = "https://github.com/gabmerlin/autotele_app/releases/latest"
    
    # GitHub Releases (optionnel - nécessite un repo GitHub public avec releases)
    GITHUB_API_URL = "https://api.github.com/repos/gabmerlin/autotele_app/releases/latest"
    
    def __init__(self):
        self.current_version = APP_VERSION
        self.latest_version: Optional[str] = None
        self.download_url: Optional[str] = None
        self.release_notes: Optional[str] = None
        self.is_required: bool = False
    
    async def check_for_updates(self, use_github: bool = False) -> Tuple[bool, str]:
        """
        Vérifie si une mise à jour est disponible.
        
        Args:
            use_github: Utiliser GitHub Releases (False par défaut, utilise version.json local)
        
        Returns:
            Tuple[bool, str]: (update_available, message)
        """
        try:
            # Par défaut, vérifier depuis le fichier local version.json
            if not use_github:
                return await self._check_local_version()
            
            # Sinon essayer GitHub (optionnel)
            return await self._check_github_releases()
        except Exception as e:
            logger.error(f"Erreur vérification mises à jour: {e}")
            # En cas d'erreur, essayer le fichier local
            try:
                return await self._check_local_version()
            except:
                return False, "Vérification des mises à jour désactivée"
    
    async def _check_local_version(self) -> Tuple[bool, str]:
        """Vérifie les mises à jour depuis le fichier local version.json."""
        try:
            # Exécuter la lecture du fichier dans un thread pour ne pas bloquer
            def read_local_version():
                version_file = Path("version.json")
                if not version_file.exists():
                    return None
                
                with open(version_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            data = await asyncio.to_thread(read_local_version)
            
            if not data:
                logger.debug("Fichier version.json introuvable")
                return False, "Pas de mise à jour disponible"
            
            self.latest_version = data.get('version', self.current_version)
            self.download_url = data.get('download_url', self.DEFAULT_DOWNLOAD_URL)
            self.release_notes = data.get('release_notes', 'Aucune note de version')
            self.is_required = data.get('required', False)
            
            # Comparer versions
            if version.parse(self.latest_version) > version.parse(self.current_version):
                prefix = "⚠️ MISE À JOUR OBLIGATOIRE" if self.is_required else "Nouvelle version disponible"
                message = (
                    f"{prefix} !\n\n"
                    f"Version actuelle : {self.current_version}\n"
                    f"Nouvelle version : {self.latest_version}\n\n"
                    f"{self.release_notes[:500]}"
                )
                logger.info(f"Mise à jour disponible : v{self.latest_version}")
                return True, message
            else:
                logger.debug("Application à jour")
                return False, "Vous avez la dernière version"
                
        except Exception as e:
            logger.error(f"Erreur lecture version.json : {e}")
            return False, "Vérification impossible"
    
    async def _check_github_releases(self) -> Tuple[bool, str]:
        """Vérifie les mises à jour via GitHub Releases."""
        try:
            # Exécuter la requête HTTP dans un thread pour ne pas bloquer
            def fetch_github():
                return requests.get(
                    self.GITHUB_API_URL,
                    timeout=10,
                    headers={'Accept': 'application/vnd.github.v3+json'}
                )
            
            response = await asyncio.to_thread(fetch_github)
            
            if response.status_code != 200:
                return False, f"Erreur serveur: {response.status_code}"
            
            data = response.json()
            
            # Récupérer les informations
            self.latest_version = data['tag_name'].lstrip('v')
            self.release_notes = data.get('body', 'Aucune note de version')
            
            # Trouver l'asset Windows (.exe)
            for asset in data.get('assets', []):
                if asset['name'].endswith('.exe') or 'Setup' in asset['name']:
                    self.download_url = asset['browser_download_url']
                    break
            
            # Comparer les versions
            if version.parse(self.latest_version) > version.parse(self.current_version):
                message = (
                    f"Mise à jour disponible !\n\n"
                    f"Version actuelle: {self.current_version}\n"
                    f"Nouvelle version: {self.latest_version}\n\n"
                    f"Nouveautés:\n{self.release_notes[:300]}..."
                )
                logger.info(f"Mise à jour disponible: v{self.latest_version}")
                return True, message
            else:
                logger.debug("Application à jour")
                return False, "Vous avez la dernière version"
        
        except requests.RequestException as e:
            logger.warning(f"Impossible de vérifier les mises à jour: {e}")
            return False, "Vérification impossible (pas de connexion)"
        except Exception as e:
            logger.error(f"Erreur GitHub API: {e}")
            return False, str(e)
    
    async def _check_custom_server(self, server_url: str) -> Tuple[bool, str]:
        """Vérifie les mises à jour via serveur personnalisé."""
        try:
            # Exécuter la requête HTTP dans un thread pour ne pas bloquer
            def fetch_server():
                return requests.get(server_url, timeout=10)
            
            response = await asyncio.to_thread(fetch_server)
            
            if response.status_code != 200:
                return False, "Serveur de mise à jour indisponible"
            
            data = response.json()
            
            # Format attendu du JSON:
            # {
            #   "version": "1.4.0",
            #   "download_url": "https://...",
            #   "release_notes": "...",
            #   "required": false
            # }
            
            self.latest_version = data['version']
            self.download_url = data['download_url']
            self.release_notes = data.get('release_notes', '')
            self.is_required = data.get('required', False)
            
            # Comparer versions
            if version.parse(self.latest_version) > version.parse(self.current_version):
                prefix = "⚠️ MISE À JOUR OBLIGATOIRE" if self.is_required else "Mise à jour disponible"
                message = (
                    f"{prefix} !\n\n"
                    f"Version actuelle: {self.current_version}\n"
                    f"Nouvelle version: {self.latest_version}\n\n"
                    f"{self.release_notes}"
                )
                logger.info(f"Mise à jour {'obligatoire' if self.is_required else 'disponible'}: v{self.latest_version}")
                return True, message
            else:
                return False, "Vous avez la dernière version"
        
        except Exception as e:
            logger.error(f"Erreur serveur custom: {e}")
            return False, str(e)
    
    def get_download_url(self) -> Optional[str]:
        """Retourne l'URL de téléchargement de la dernière version."""
        return self.download_url
    
    def is_update_required(self) -> bool:
        """Indique si la mise à jour est obligatoire."""
        return self.is_required


# Instance globale
_updater_instance: Optional[AutoUpdater] = None


def get_updater() -> AutoUpdater:
    """Récupère l'instance globale de l'updater."""
    global _updater_instance
    if _updater_instance is None:
        _updater_instance = AutoUpdater()
    return _updater_instance

