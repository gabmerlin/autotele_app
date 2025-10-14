"""
Système de vérification des mises à jour pour AutoTele.

Vérifie auprès d'un serveur distant (GitHub ou serveur custom) 
si une nouvelle version est disponible.
"""
import requests
import json
from typing import Optional, Tuple
from packaging import version

from utils.logger import get_logger
from utils.constants import APP_VERSION

logger = get_logger()


class AutoUpdater:
    """Gestionnaire de mises à jour automatiques."""
    
    # URL de votre serveur de versions (à personnaliser)
    UPDATE_SERVER_URL = "https://votre-serveur.com/autotele/version.json"
    
    # Ou GitHub Releases (recommandé)
    GITHUB_API_URL = "https://api.github.com/repos/votre-username/autotele/releases/latest"
    
    def __init__(self):
        self.current_version = APP_VERSION
        self.latest_version: Optional[str] = None
        self.download_url: Optional[str] = None
        self.release_notes: Optional[str] = None
        self.is_required: bool = False
    
    async def check_for_updates(self, use_github: bool = True) -> Tuple[bool, str]:
        """
        Vérifie si une mise à jour est disponible.
        
        Args:
            use_github: Utiliser GitHub Releases (True) ou serveur custom (False)
        
        Returns:
            Tuple[bool, str]: (update_available, message)
        """
        try:
            if use_github:
                return await self._check_github_releases()
            else:
                return await self._check_custom_server()
        except Exception as e:
            logger.error(f"Erreur vérification mises à jour: {e}")
            return False, f"Erreur de vérification: {e}"
    
    async def _check_github_releases(self) -> Tuple[bool, str]:
        """Vérifie les mises à jour via GitHub Releases."""
        try:
            response = requests.get(
                self.GITHUB_API_URL,
                timeout=10,
                headers={'Accept': 'application/vnd.github.v3+json'}
            )
            
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
    
    async def _check_custom_server(self) -> Tuple[bool, str]:
        """Vérifie les mises à jour via serveur personnalisé."""
        try:
            response = requests.get(self.UPDATE_SERVER_URL, timeout=10)
            
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

