#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de chiffrement des configurations pour AutoTele.
Chiffre les fichiers .env et app_config.json et les intègre dans embedded_config.py
"""

import os
import json
from pathlib import Path
from cryptography.fernet import Fernet
import base64

def generate_key():
    """Génère une clé de chiffrement"""
    return Fernet.generate_key()

def encrypt_file(file_path, key):
    """Chiffre un fichier avec la clé fournie"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    fernet = Fernet(key)
    encrypted_content = fernet.encrypt(content.encode('utf-8'))
    
    return base64.b64encode(encrypted_content).decode('utf-8')

def update_embedded_config(env_encrypted, config_encrypted, key_b64):
    """Met à jour le fichier embedded_config.py avec les configurations chiffrées"""
    
    embedded_config_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration chiffrée embarquée pour AutoTele.
Ce fichier est généré automatiquement par encrypt_env.py
"""

import base64
from cryptography.fernet import Fernet

# Clé de déchiffrement (base64)
ENCRYPTION_KEY = {repr(key_b64)}

# Configuration .env chiffrée (base64)
ENCRYPTED_ENV = {repr(env_encrypted)}

# Configuration app_config.json chiffrée (base64)
ENCRYPTED_APP_CONFIG = {repr(config_encrypted)}

def get_decrypted_env():
    """Déchiffre et retourne le contenu du fichier .env"""
    try:
        key = base64.b64decode(ENCRYPTION_KEY)
        fernet = Fernet(key)
        encrypted_data = base64.b64decode(ENCRYPTED_ENV)
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')
    except Exception as e:
        print(f"Erreur lors du déchiffrement du .env: {{e}}")
        return ""

def get_decrypted_app_config():
    """Déchiffre et retourne le contenu du fichier app_config.json"""
    try:
        key = base64.b64decode(ENCRYPTION_KEY)
        fernet = Fernet(key)
        encrypted_data = base64.b64decode(ENCRYPTED_APP_CONFIG)
        decrypted_data = fernet.decrypt(encrypted_data)
        return json.loads(decrypted_data.decode('utf-8'))
    except Exception as e:
        print(f"Erreur lors du déchiffrement de app_config.json: {{e}}")
        return {{}}

def save_decrypted_files():
    """Sauvegarde les fichiers déchiffrés pour le développement"""
    import os
    
    # Créer le dossier config s'il n'existe pas
    os.makedirs('config', exist_ok=True)
    
    # Sauvegarder .env
    env_content = get_decrypted_env()
    if env_content:
        with open('config/.env', 'w', encoding='utf-8') as f:
            f.write(env_content)
        print("[OK] Fichier .env restauré dans config/")
    
    # Sauvegarder app_config.json
    config_content = get_decrypted_app_config()
    if config_content:
        with open('config/app_config.json', 'w', encoding='utf-8') as f:
            json.dump(config_content, f, indent=2, ensure_ascii=False)
        print("[OK] Fichier app_config.json restauré dans config/")

if __name__ == "__main__":
    # Mode développement : restaurer les fichiers
    save_decrypted_files()
'''

    with open('src/utils/embedded_config.py', 'w', encoding='utf-8') as f:
        f.write(embedded_config_content)

def main():
    """Fonction principale de chiffrement"""
    print("=" * 40)
    print("CHIFFREMENT DES CONFIGURATIONS")
    print("=" * 40)
    
    # Vérifier que les fichiers existent
    env_path = Path('config/.env')
    config_path = Path('config/app_config.json')
    
    if not env_path.exists():
        print("[ERROR] Fichier config/.env non trouvé")
        return False
    
    if not config_path.exists():
        print("[ERROR] Fichier config/app_config.json non trouvé")
        return False
    
    try:
        # Générer une clé de chiffrement
        print("\\n[1/4] Génération de la clé de chiffrement...")
        key = generate_key()
        key_b64 = base64.b64encode(key).decode('utf-8')
        print("[OK] Clé générée")
        
        # Chiffrer le fichier .env
        print("\\n[2/4] Chiffrement du fichier .env...")
        print(f"Lecture de {env_path}...")
        with open(env_path, 'r', encoding='utf-8') as f:
            env_content = f.read()
        print(f"Taille: {len(env_content)} caractères")
        
        env_encrypted = encrypt_file(env_path, key)
        print(f"Chiffrement .env terminé: {len(env_encrypted)} bytes")
        
        # Chiffrer le fichier app_config.json
        print("\\n[3/4] Chiffrement du fichier app_config.json...")
        print(f"Lecture de {config_path}...")
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()
        print(f"Taille: {len(config_content)} caractères")
        
        config_encrypted = encrypt_file(config_path, key)
        print(f"Chiffrement app_config.json terminé: {len(config_encrypted)} bytes")
        
        # Mettre à jour embedded_config.py
        print("\\n[4/4] Mise à jour de embedded_config.py...")
        update_embedded_config(env_encrypted, config_encrypted, key_b64)
        
        print("\\n" + "=" * 40)
        print("[SUCCESS] SUCCÈS !")
        print("=" * 40)
        print("Le fichier src\\utils\\embedded_config.py a été mis à jour")
        print("Les configurations sont maintenant chiffrées et embarquées dans l'application")
        print("\\nIMPORTANT:")
        print("1. Recompilez l'application avec PyInstaller")
        print("2. Le .env ET app_config.json seront chargés automatiquement depuis la mémoire")
        print("3. Aucun fichier de config visible sur le disque de l'utilisateur final")
        
        return True
        
    except Exception as e:
        print(f"\\n[ERROR] ERREUR: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)
