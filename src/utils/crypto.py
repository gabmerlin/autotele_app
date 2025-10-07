"""
Utilitaires de chiffrement pour sécuriser les sessions Telegram
"""
import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.backends import default_backend


class SessionEncryptor:
    """Chiffrement AES-256 pour les sessions Telegram"""
    
    def __init__(self, master_password: str = None):
        """
        Initialise le chiffreur avec un mot de passe maître.
        Si aucun mot de passe n'est fourni, utilise un dérivé de l'identifiant machine.
        """
        if master_password is None:
            # Générer une clé basée sur l'identifiant de la machine
            machine_id = self._get_machine_id()
            master_password = machine_id
        
        self.salt = self._get_or_create_salt()
        self.key = self._derive_key(master_password, self.salt)
        self.cipher = Fernet(self.key)
    
    def _get_machine_id(self) -> str:
        """Obtient un identifiant unique de la machine (Windows)"""
        try:
            import subprocess
            result = subprocess.run(
                ['wmic', 'csproduct', 'get', 'uuid'],
                capture_output=True,
                text=True,
                check=True
            )
            uuid = result.stdout.split('\n')[1].strip()
            return uuid
        except Exception:
            # Fallback : utiliser le nom de la machine + username
            import getpass
            import platform
            return f"{platform.node()}-{getpass.getuser()}"
    
    def _get_or_create_salt(self) -> bytes:
        """Récupère ou crée un salt pour le dérivation de clé"""
        salt_file = "config/.salt"
        os.makedirs("config", exist_ok=True)
        
        if os.path.exists(salt_file):
            with open(salt_file, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(32)
            with open(salt_file, 'wb') as f:
                f.write(salt)
            return salt
    
    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Dérive une clé de chiffrement à partir du mot de passe"""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key
    
    def encrypt_session(self, session_data: bytes) -> bytes:
        """Chiffre les données de session"""
        return self.cipher.encrypt(session_data)
    
    def decrypt_session(self, encrypted_data: bytes) -> bytes:
        """Déchiffre les données de session"""
        return self.cipher.decrypt(encrypted_data)
    
    def encrypt_file(self, input_path: str, output_path: str):
        """Chiffre un fichier de session"""
        with open(input_path, 'rb') as f:
            data = f.read()
        
        encrypted = self.encrypt_session(data)
        
        with open(output_path, 'wb') as f:
            f.write(encrypted)
    
    def decrypt_file(self, input_path: str, output_path: str):
        """Déchiffre un fichier de session"""
        with open(input_path, 'rb') as f:
            encrypted = f.read()
        
        decrypted = self.decrypt_session(encrypted)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted)


def hash_password(password: str) -> str:
    """Hash un mot de passe avec SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_token(length: int = 32) -> str:
    """Génère un token aléatoire sécurisé"""
    return base64.urlsafe_b64encode(os.urandom(length)).decode()[:length]

