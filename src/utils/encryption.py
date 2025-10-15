"""
Module de chiffrement pour les sessions Telegram.

SÉCURITÉ : Ce module chiffre les fichiers de session Telegram pour protéger
les credentials des comptes en cas de vol du disque ou d'accès non autorisé.

Algorithme : AES-256 via Fernet (cryptography)
Dérivation de clé : PBKDF2-HMAC-SHA256 avec 100,000 itérations
"""
import os
import base64
from pathlib import Path
from typing import Optional, Tuple
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from utils.logger import get_logger

logger = get_logger()


class SessionEncryption:
    """Gère le chiffrement et déchiffrement des sessions Telegram."""
    
    # Nombre d'itérations pour PBKDF2 (100k = bon compromis sécurité/performance)
    ITERATIONS = 100_000
    
    # Chemin du fichier de salt (unique par installation)
    SALT_FILE = Path("config/.encryption_salt")
    
    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialise le système de chiffrement.
        
        Args:
            encryption_key: Clé de chiffrement (depuis .env)
                           Si None, essaie de charger depuis l'environnement
        
        Raises:
            ValueError: Si la clé de chiffrement n'est pas définie
        """
        if encryption_key is None:
            encryption_key = os.getenv('AUTOTELE_ENCRYPTION_KEY')
        
        if not encryption_key:
            raise ValueError(
                "ERREUR: Clé de chiffrement non définie.\n"
                "Ajoutez AUTOTELE_ENCRYPTION_KEY dans votre fichier .env\n"
                "Générez-en une avec : python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        
        self.encryption_key = encryption_key
        
        # Récupérer ou créer un salt unique pour cette installation
        self.salt = self._get_or_create_salt()
        
        self._fernet = self._derive_fernet_key(encryption_key)
    
    def _get_or_create_salt(self) -> bytes:
        """
        Récupère ou crée un salt unique pour cette installation.
        
        SÉCURITÉ: Le salt est généré aléatoirement une seule fois et stocké
        de manière sécurisée. Cela évite les attaques par rainbow tables.
        
        Returns:
            bytes: Salt de 32 bytes
        """
        try:
            # Vérifier si le salt existe déjà
            if self.SALT_FILE.exists():
                with open(self.SALT_FILE, 'rb') as f:
                    salt = f.read()
                
                # Valider la longueur
                if len(salt) == 32:
                    logger.debug("Salt de chiffrement chargé depuis le fichier")
                    return salt
                else:
                    logger.warning(f"Salt corrompu (longueur: {len(salt)}), régénération...")
            
            # Générer un nouveau salt aléatoire (cryptographiquement sécurisé)
            import secrets
            new_salt = secrets.token_bytes(32)
            
            # Créer le répertoire si nécessaire
            self.SALT_FILE.parent.mkdir(parents=True, exist_ok=True)
            
            # Stocker le salt
            with open(self.SALT_FILE, 'wb') as f:
                f.write(new_salt)
            
            # Permissions restrictives (Windows et Unix)
            try:
                from utils.file_permissions import FilePermissions
                success, msg = FilePermissions.set_secure_file_permissions(self.SALT_FILE)
                if success:
                    logger.debug(f"Permissions salt sécurisées: {msg}")
                else:
                    logger.warning(f"Permissions salt non appliquées: {msg}")
            except Exception as perm_error:
                logger.warning(f"Impossible de définir les permissions du salt: {perm_error}")
            
            logger.info("🔑 Nouveau salt de chiffrement généré et sauvegardé")
            return new_salt
            
        except Exception as e:
            logger.error(f"Erreur lors de la gestion du salt: {e}")
            # Fallback: générer un salt temporaire (moins sécurisé)
            logger.warning("ATTENTION: Utilisation d'un salt temporaire (non persistant)")
            import secrets
            return secrets.token_bytes(32)
    
    def _derive_fernet_key(self, password: str) -> Fernet:
        """
        Dérive une clé Fernet depuis un mot de passe avec PBKDF2.
        
        Args:
            password: Mot de passe/clé de chiffrement
            
        Returns:
            Fernet: Instance Fernet avec la clé dérivée
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,  # 256 bits
            salt=self.salt,  # Utilise le salt unique
            iterations=self.ITERATIONS
        )
        
        # Dériver la clé depuis le mot de passe
        key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
        
        return Fernet(key)
    
    def encrypt_session_file(self, session_path: Path) -> Tuple[bool, str]:
        """
        Chiffre un fichier de session Telegram.
        
        Args:
            session_path: Chemin vers le fichier .session
            
        Returns:
            Tuple[bool, str]: (succès, message)
        """
        try:
            if not session_path.exists():
                return False, f"Fichier introuvable: {session_path}"
            
            # Lire le fichier non chiffré
            with open(session_path, 'rb') as f:
                plaintext = f.read()
            
            if len(plaintext) == 0:
                return False, "Fichier vide"
            
            # Chiffrer
            encrypted = self._fernet.encrypt(plaintext)
            
            # Sauvegarder avec extension .enc (SANS .session à la fin)
            base_name = str(session_path).replace('.session', '')
            encrypted_path = Path(f"{base_name}.enc")
            
            with open(encrypted_path, 'wb') as f:
                f.write(encrypted)
            
            # Supprimer l'original non chiffré
            session_path.unlink()
            
            return True, f"Session chiffrée: {encrypted_path.name}"
            
        except Exception as e:
            logger.error(f"Erreur chiffrement {session_path.name}: {e}")
            return False, str(e)
    
    def decrypt_session_file(self, encrypted_path: Path, output_path: Optional[Path] = None) -> Tuple[bool, str, Optional[Path]]:
        """
        Déchiffre un fichier de session Telegram.
        
        Args:
            encrypted_path: Chemin vers le fichier .session.enc
            output_path: Chemin de sortie (optionnel, par défaut = .session)
            
        Returns:
            Tuple[bool, str, Optional[Path]]: (succès, message, chemin_déchiffré)
        """
        try:
            if not encrypted_path.exists():
                return False, f"Fichier chiffré introuvable: {encrypted_path}", None
            
            # Lire le fichier chiffré
            with open(encrypted_path, 'rb') as f:
                encrypted = f.read()
            
            # Déchiffrer
            try:
                plaintext = self._fernet.decrypt(encrypted)
            except InvalidToken:
                return False, "Clé de chiffrement invalide ou fichier corrompu", None
            
            # Déterminer le chemin de sortie
            if output_path is None:
                # Retirer .enc pour obtenir .session
                output_path = encrypted_path.with_suffix('')
                if output_path.suffix != '.session':
                    output_path = output_path.with_suffix('.session')
            
            # Sauvegarder le fichier déchiffré
            with open(output_path, 'wb') as f:
                f.write(plaintext)
            
            logger.debug(f"Session déchiffrée: {encrypted_path.name} -> {output_path.name}")
            return True, "Session déchiffrée", output_path
            
        except Exception as e:
            logger.error(f"Erreur déchiffrement {encrypted_path.name}: {e}")
            return False, str(e), None
    
    def is_encrypted(self, path: Path) -> bool:
        """
        Vérifie si un fichier de session est chiffré.
        
        Args:
            path: Chemin du fichier
            
        Returns:
            bool: True si le fichier est chiffré
        """
        path_str = str(path)
        return (path.suffix == '.enc' or 
                path_str.endswith('.session.enc') or 
                path_str.endswith('.enc.session'))
    
    def get_encrypted_path(self, session_path: Path) -> Path:
        """
        Retourne le chemin du fichier chiffré correspondant.
        
        Args:
            session_path: Chemin du fichier .session
            
        Returns:
            Path: Chemin du fichier .enc (SANS .session à la fin)
        """
        # Retirer l'extension .session et ajouter .enc
        base_name = str(session_path).replace('.session', '')
        return Path(f"{base_name}.enc")
    
    def get_decrypted_path(self, encrypted_path: Path) -> Path:
        """
        Retourne le chemin du fichier déchiffré correspondant.
        
        Args:
            encrypted_path: Chemin du fichier .enc
            
        Returns:
            Path: Chemin du fichier .session
        """
        # Retirer .enc et ajouter .session
        base_name = str(encrypted_path).replace('.enc', '')
        return Path(f"{base_name}.session")


def generate_encryption_key() -> str:
    """
    Génère une clé de chiffrement aléatoire sécurisée.
    
    Returns:
        str: Clé de chiffrement en base64url
    """
    import secrets
    return secrets.token_urlsafe(32)


# Instance globale (lazy loading)
_encryption_instance: Optional[SessionEncryption] = None


def get_encryption() -> SessionEncryption:
    """
    Récupère l'instance globale du système de chiffrement.
    
    Returns:
        SessionEncryption: Instance du système de chiffrement
        
    Raises:
        ValueError: Si la clé de chiffrement n'est pas configurée
    """
    global _encryption_instance
    
    if _encryption_instance is None:
        _encryption_instance = SessionEncryption()
    
    return _encryption_instance

