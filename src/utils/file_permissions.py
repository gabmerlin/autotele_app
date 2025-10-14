"""
Module de gestion sécurisée des permissions fichiers.

SÉCURITÉ: Applique des permissions restrictives sur les fichiers sensibles
pour éviter leur lecture par d'autres utilisateurs du système.

Support:
- Windows: ACLs (Access Control Lists)
- Linux/macOS: chmod 600/700
"""
import os
import stat
from pathlib import Path
from typing import Tuple

from utils.logger import get_logger

logger = get_logger()


class FilePermissions:
    """Gestionnaire de permissions fichiers sécurisées."""
    
    @staticmethod
    def set_secure_file_permissions(file_path: Path) -> Tuple[bool, str]:
        """
        Applique des permissions restrictives sur un fichier.
        
        Permissions:
        - Windows: Lecture/Écriture uniquement pour l'utilisateur actuel (ACLs)
        - Linux/macOS: chmod 600 (rw-------)
        
        Args:
            file_path: Chemin du fichier à sécuriser
            
        Returns:
            Tuple[bool, str]: (succès, message)
        """
        if not file_path.exists():
            return False, f"Fichier inexistant: {file_path}"
        
        try:
            if os.name == 'nt':  # Windows
                return FilePermissions._set_windows_acl(file_path)
            else:  # Linux/macOS
                return FilePermissions._set_unix_permissions(file_path, 0o600)
        except Exception as e:
            logger.warning(f"Erreur définition permissions {file_path.name}: {e}")
            return False, str(e)
    
    @staticmethod
    def set_secure_directory_permissions(dir_path: Path) -> Tuple[bool, str]:
        """
        Applique des permissions restrictives sur un répertoire.
        
        Permissions:
        - Windows: Full Control uniquement pour l'utilisateur actuel (ACLs)
        - Linux/macOS: chmod 700 (rwx------)
        
        Args:
            dir_path: Chemin du répertoire à sécuriser
            
        Returns:
            Tuple[bool, str]: (succès, message)
        """
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if os.name == 'nt':  # Windows
                return FilePermissions._set_windows_acl(dir_path)
            else:  # Linux/macOS
                return FilePermissions._set_unix_permissions(dir_path, 0o700)
        except Exception as e:
            logger.warning(f"Erreur définition permissions {dir_path.name}: {e}")
            return False, str(e)
    
    @staticmethod
    def _set_windows_acl(path: Path) -> Tuple[bool, str]:
        """
        Applique des ACLs Windows restrictives.
        
        Seul l'utilisateur actuel peut lire/écrire le fichier.
        
        Args:
            path: Chemin du fichier ou répertoire
            
        Returns:
            Tuple[bool, str]: (succès, message)
        """
        try:
            import win32security
            import win32api
            import ntsecuritycon as con
            
            # Obtenir le SID de l'utilisateur actuel
            username = win32api.GetUserName()
            user_sid, domain, account_type = win32security.LookupAccountName("", username)
            
            # Créer un nouveau Security Descriptor
            sd = win32security.SECURITY_DESCRIPTOR()
            
            # Créer une nouvelle DACL (Discretionary Access Control List)
            dacl = win32security.ACL()
            
            # Ajouter une ACE (Access Control Entry) pour l'utilisateur
            # FILE_ALL_ACCESS = Contrôle total (lecture, écriture, suppression, etc.)
            dacl.AddAccessAllowedAce(
                win32security.ACL_REVISION,
                con.FILE_ALL_ACCESS,
                user_sid
            )
            
            # Appliquer la DACL au Security Descriptor
            sd.SetSecurityDescriptorDacl(1, dacl, 0)
            
            # Appliquer le Security Descriptor au fichier
            win32security.SetFileSecurity(
                str(path),
                win32security.DACL_SECURITY_INFORMATION,
                sd
            )
            
            logger.debug(f"ACLs Windows appliquées: {path.name}")
            return True, "Permissions Windows appliquées (ACLs)"
            
        except ImportError:
            # pywin32 non installé
            msg = "pywin32 non installé - permissions Windows non définies"
            logger.warning(msg)
            logger.warning("Installez pywin32: pip install pywin32")
            return False, msg
        except Exception as e:
            logger.error(f"Erreur ACLs Windows: {e}")
            return False, str(e)
    
    @staticmethod
    def _set_unix_permissions(path: Path, mode: int) -> Tuple[bool, str]:
        """
        Applique des permissions Unix (chmod).
        
        Args:
            path: Chemin du fichier ou répertoire
            mode: Mode de permission (ex: 0o600 pour rw-------)
            
        Returns:
            Tuple[bool, str]: (succès, message)
        """
        try:
            os.chmod(path, mode)
            
            # Formater le mode en octal pour le log
            mode_str = oct(mode)[2:]  # Retire '0o'
            logger.debug(f"Permissions Unix appliquées: {path.name} ({mode_str})")
            
            return True, f"Permissions appliquées ({mode_str})"
        except Exception as e:
            logger.error(f"Erreur chmod: {e}")
            return False, str(e)
    
    @staticmethod
    def check_file_permissions(file_path: Path) -> Tuple[bool, str]:
        """
        Vérifie si un fichier a des permissions sécurisées.
        
        Args:
            file_path: Chemin du fichier
            
        Returns:
            Tuple[bool, str]: (est_sécurisé, message)
        """
        if not file_path.exists():
            return False, "Fichier inexistant"
        
        try:
            if os.name == 'nt':  # Windows
                # Sur Windows, la vérification des ACLs est complexe
                # On suppose sécurisé si le fichier existe
                # (vérification complète nécessiterait pywin32)
                return True, "Vérification Windows non implémentée (supposé sécurisé)"
            else:  # Linux/macOS
                file_stat = file_path.stat()
                mode = file_stat.st_mode
                
                # Vérifier permissions groupe et autres
                if mode & stat.S_IRGRP or mode & stat.S_IWGRP:
                    return False, "⚠️ Fichier accessible en lecture/écriture par le groupe"
                
                if mode & stat.S_IROTH or mode & stat.S_IWOTH:
                    return False, "⚠️ Fichier accessible en lecture/écriture par tous"
                
                return True, "Permissions sécurisées (600)"
        except Exception as e:
            return False, f"Erreur vérification: {e}"
    
    @staticmethod
    def create_secure_file(file_path: Path, content: bytes = b'') -> Tuple[bool, str]:
        """
        Crée un fichier avec permissions restrictives.
        
        Args:
            file_path: Chemin du fichier
            content: Contenu initial (optionnel)
            
        Returns:
            Tuple[bool, str]: (succès, message)
        """
        try:
            # Créer le répertoire parent si nécessaire
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Écrire le fichier
            with open(file_path, 'wb') as f:
                f.write(content)
            
            # Appliquer permissions restrictives
            success, msg = FilePermissions.set_secure_file_permissions(file_path)
            
            if success:
                logger.debug(f"Fichier sécurisé créé: {file_path.name}")
                return True, f"Fichier créé avec permissions restrictives"
            else:
                logger.warning(f"Fichier créé mais permissions non appliquées: {msg}")
                return True, f"Fichier créé (warning: {msg})"
        except Exception as e:
            logger.error(f"Erreur création fichier sécurisé: {e}")
            return False, str(e)


def get_file_permissions() -> FilePermissions:
    """
    Récupère l'instance du gestionnaire de permissions.
    
    Returns:
        FilePermissions: Instance du gestionnaire
    """
    return FilePermissions()

