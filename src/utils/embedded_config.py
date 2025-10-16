#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Configuration chiffrée embarquée pour AutoTele.
Ce fichier est généré automatiquement par encrypt_env.py
"""

import base64
import json
import os
from cryptography.fernet import Fernet

# Clé de déchiffrement (base64)
ENCRYPTION_KEY = 'QnMzTkdUZ3YxOXVQUElCRVVxM3FQR09mNHpzMG1lR0t2NEk5STV5WE85bz0='

# Configuration .env chiffrée (base64)
ENCRYPTED_ENV = 'Z0FBQUFBQm84UjhKVW9mcTBJMEJpNDdMYWNMMEVnb3pYcGxvdjRFSnZ2TllWVHBKbnd5enYzaC1kbFNPcEs2eXNhMk9GbEl4bnVma1NRVENXc05taWY1N0JXUXFXZFZQZUhfTXA2VTBjczA4VUpfc3VNM1NkeXdHdXNWUGF2RkQ2YnpQYUtfcFJBUXdDaXhNQkdYQzdISWxzZmlRUll6TU9jeWZMeGhUa1Y2WWwzd0tCcFhsUjFOTVYtLWxOQlZmV1VJeXJaYmZ4ZXprMFFXNGxnOWpPcWlUTHl4UUZqVm9ENndUNjh1YWVabE1zeWFGS19tUlY3M25hekg5Skc4SGZNaTVTT2FaOWRsajZCc1M1YTlXalEtcFNkUDdJLUJZaXNNckwtbE45UzNwQUxpU2RsSmdUX2RvajQ2QXpRa2Y4eGlIcDhZSTltN3Qta3NHR0x5cHo2a0hrQlVJU1RsQ0N6R3p6bWlUNnpjLTI0dFRVZUpqZEE5VkEtQWlVVUprTHRLeThTc0M0QVhXUFRjTnRSS0VSdF9UMW5tNDBLeWNMSjRPOWZsMVAzZEVjRi1lTmNpTU5veE9jOXJKdUFJSUd3ZnRYMldHMEhqbEZucHBISjBBdVZVT2lDMHBORjRwS19zUDNXdXQyZl9wNi03b1pIbjN5VU5yMV9xOEVwUUVwRzg5UW1NN0JGa0tQRzZTa0JlRmY1c1hXMUMwRnVfOThySE1URlBRRV9fSHdQOUtMQ09OSDluREdXMUp4eUV2UzdzR2UyUU5ianYwQm1sYmJmWVppbFdpWTFGQnJPUUdrSXRLY1FZQkR5bDFhdnB2bVlSUWU2RkdPemkxV3IydzFWVlJZMFI1c0pXeE83RWIxYlBnWUxmZkQ3cTZUZktQT3dUU0c2UnZUS1ljZFZsM0NmZWFvemtTYmtybTFGNUhUUUdPNUE1X3RrTzFfSXpWeHRKV1pYM0RUS29PSHBqR0k5eHpNRXJuVnVXdWZXNVdwd1dKTVNudG1YemFlbjN2YU5oVjA1SGRPc2EteGptU1E1XzByMmViX3RaREVUQV9zU0F6emViLXA3VWh6N09RRE9NSGludS1KdVBWM2tvcHJrZ1hMOVAxdkEtNXhMXzFPeTFVSmtUSVNSa1BiRHB6Z2I2RHAtS09pZV9Rb1hiNUlDR0VOTEFTbG5SMDB6QWx1bDBFaFRJczdpaU1XNFhWRG55WkxzYnd5TkZPUm5zWWQ4eFZzbFlFVnN2NDhOWUZkMjlPYXZMNGgySnRNMENqR1BTb2lUbUtUeEVEM3FKRTlRYmtTLUh4bXZnS2RYY1R6R1hvUXk3bE5JVldKdlp6UG9uR3F6SVluZDhPYmpEc0JMazVWM2dnX2Q0WG1kTUlUbEI5U3p1VkNqNE9tVkVpY2NvdUpxYmx0b0VwWjFkQkZmRFRFaW9JdlFVYU1abmVGcjV6eWY3SmpvdHRaa0dza3d1VXlvRlZrN29jTDBBTTBtTkV5Sm5NcFBRWUVXc2s4RGh3OUJxUWtkUGxOajFrdF9NbGZIUlloV1lBNWFXR0NhWXYwRFItbzJSMUdnR18yR0twRzVOT09vOHoyU25jNk1vWUg2bl93bDNGUG5MYVUxMnpqQXM3NnJoUW1BZFc0SHpsU01mSVBEU3VnV29Gd3NrQnZTbmZ1b01TTTJlSW5TdWhyb0J3UE1iVTVvVkNfLV84TWhXaGt2dkhzZEI1X1FGZkhDM0l0SUtGTVFaU0lBPT0='

# Configuration app_config.json chiffrée (base64)
ENCRYPTED_APP_CONFIG = 'Z0FBQUFBQm84UjhKaWRUSW8xcEd4YXo0ZHdZeTNfek5WVWlBZ0NZWGRUcVNjZXY4LTdybWpWemI1VDNkclZPZ2YxZkhGQ2RTRFRVRUhYUUFEd1J4Ul9vclBSRmtGV1dYWkQ0cmFHN0JmMUhGRkhwdGhKUS1ZV0RkY0xtbVFickl4aEZIaWdTZ01FTGthcHMyWFRhRFRVQWducjdrWkhQN0E1NExlVnJxY2dNZldhX1p1dGl1Nll4RVNGMmJ1TzRZcG5vY0lHNVFxa1JRcVVsSjJYWklyeHZnZHpoelBiY190T2NkMVBqTkIwVG1hRVBuenk5OUtzUjZXQW5vZ2hYdXpXT2ZwMXhqeF81R28yZ0hmcGtZM2NfUFRVQ3ZGdVZnTG01bmJnanM0czM4RWhNcGxWVTFVRUR1T09jTG5UemZGa0dFbjZsZVp2enZQSzM3bjBtdkNuWWpNUllzU1Uxc2lOWm1BWGVYYVhuLUpCemFIZlVQR0hhYlVkT0ZtdFVkVXJiYy0zbzdaX1pYRWNlOUlUalNMNHNTU1NpMDVWd2RhUUVCZ19rYWwwQ2ExUmhYaU9NTjN6cVluaEVXQkZOWWQ3NGtYNWZNQVFSWElaNHBPdlRJa3NQeHV1TXpIaVlqTGloVll3TFZRZ0FiakN0el9JaTlrZUxwOTBwTi13MnFLOEs2eVBlbDFWV1Q1dkZrbEk1SFhZaWR4dVdNRzFKTWl2b29DLU1jbDNkOHVMZzNXQ2doQms0dFpHX2lpVFdIbWpINHdDS3JyY3hGVlVra1E4cWRhZXVaUjhsWldmZktkLVZwWDQ1Smx3UU5YMkFlaER1MG9mYXlZZWdOLS12S1hXYm9SWXJRbmdBaDk3cHFqWTdCaVE3dm1TZjZha1NVek1iU05zSkdpcXpLYXgzQ1BwSzFHeUZ2WWhIZWFyTVJ4MHhreEllVDZfN1hrSTBINmpfdXFJeHB1enNCakpXdkNXSnFGYzFPUkRLSlN2RkJPZVViNXpXQTZ5czE0WDhqQm1TcUFWNzRiRUJ3ZmtNYzV3MlppQi1fUG5iSnY5WEY1UmZmWUFFbm01SFN3cjNLOXh3VDgtYUNTZnlnUWRiSkZ5amtRTXBQSWZyTFFaR1l3MHNrVVhSWENyNjg4elpFMnZYMnNxQllBTEFwcmlFQVkwZUZNWkhaSmRzRkFmNDQxZWNGaWN2c0hkVmpVNWo4YllXVzQ1WExpUTVUQ2JCX3JJNWp0cUUtU2pFRUxTUDhmSmJjbXo3WlU0OUd1QzhaZFZXS3pCZl9JcnY1ckFGcThQenZ0LUpZbHM5ZG0yWHMtekNxY2ZMS3FfdGcwdlB5anV2bzM4amc1R0x5ejQtVHpxOHBxZjMycWt1MUFQRWF5YjIya1ZaZHExT0xLb2w3VFJTX2d2eVNKeGJVNzQ4RGNGWm5TWU1ldXQyM3FKRi1WVzhoTWdmanN4S3lacTM3QllkM3AwblNGQkgtNVkzd2Rmdi1XRWVxVjZZUV8yUzQzbnpHaF8yWUlhVHZLQjVuSkJrVS1WYXdzem1Sa1lzTkEtNzlwTXl5Nl9kQkZOdFB6Ym1TQVpnZ1dEZndGZ1piUS1hNHAtR2JiUjk0b0wxY1p1QnFhN19XbGt5aWYtcE9NVlc5M09RTXVQUjJFV2JVMlVoYnpTQU8zSVdoODU3NnJ1RlBlbUtJdW5WejV1THl5VWxFcW0zQ25hTlhRWU1kdVlMLWU3SFE3U3JjelNqcWs4Ml95YXRidVR6RDJ1WC15U3cwR0hhRTZaNUM3SkplQWlzSFVZZzVUVFZLS1hmTW94VVFiSnYwV21YX1J5aXl3VEdwak9yblNWRE5obHZLMVBqWUN1b0tUMWttNzQ5aWpTSGNMYTRreFNBbFF6ajQ0ZDliLWJBZXhlMHRCZVM2a3U1MUpYYVZWNjdPRWlnZVRnSFVNY0JrQXExOXF0dE1Vdl9GZVpFZGpDeDROSFhJUFpjVFlqRm51VmxRVGlEWGR4LXFsTG9XcGJuT3dPWmNDZlRnN3JJPQ=='

def get_decrypted_env():
    """Déchiffre et retourne le contenu du fichier .env"""
    try:
        key = base64.b64decode(ENCRYPTION_KEY)
        fernet = Fernet(key)
        encrypted_data = base64.b64decode(ENCRYPTED_ENV)
        decrypted_data = fernet.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')
    except Exception as e:
        print(f"Erreur lors du déchiffrement du .env: {e}")
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
        print(f"Erreur lors du déchiffrement de app_config.json: {e}")
        return {}

def set_env_from_embedded():
    """
    Injecte les variables d'environnement déchiffrées dans os.environ.
    Cette fonction charge la config chiffrée et la met en mémoire.
    """
    try:
        env_content = get_decrypted_env()
        if not env_content:
            print("[ERREUR] Impossible de déchiffrer le .env")
            return False
        
        # Parser le contenu du .env et injecter dans os.environ
        for line in env_content.split('\n'):
            line = line.strip()
            # Ignorer les commentaires et lignes vides
            if not line or line.startswith('#'):
                continue
            
            # Parser KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Retirer les guillemets si présents
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Injecter dans os.environ
                os.environ[key] = value
        
        print("[OK] Configuration déchiffrée et chargée en mémoire")
        return True
        
    except Exception as e:
        print(f"[ERREUR] Échec du chargement de la config: {e}")
        return False

def save_decrypted_files():
    """Sauvegarde les fichiers déchiffrés pour le développement"""
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
