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
ENCRYPTION_KEY = 'TzBCRVZLV0VPdnE0SDV5OERucVB2MnZVeXN1VlJKNEVVajJTNVpkdTNXRT0='

# Configuration .env chiffrée (base64)
ENCRYPTED_ENV = 'Z0FBQUFBQm84bFpqVEw4Ykc2RzhtNl9RNFBJUDI2cXBPdW5rbzFoSTE0NFdYTEZoamFPdUJzOHR6dFJZQnpTb29yQ0pBb0NMQzRLWEhZcVVrbUpndUR5TlBUZXk5OWFEaV9EZWpMVHBvMm5JaUpiUFFfMnJ6ZGh2UGQ0WG9xRVQtRHZXQk1EbkRqZzA2ZUtTZ09sR2w2d3lzM3o5SmFwM2lUb214NTRnM2FTS01TREllZ01LZ09FbTN5X0EzLXFGSDNwQ01jRkowYllQVjhoeGZtVjUyZ0lDVVR3c3p5dWFLRGEyRnplVXVYb2QzMmhHTm5kVmlkb2l2OXVFVG5BdGJwbG90anQxSlk1WFJfTjk0Z1BoOFpCQzBMTmRQTzQ4OEVuNkF3OXJvcllXUzhTMlJpSTZHNTdOWm9fMFFtOC1YSlkxTk96RERpUEM2eG5zeEZ4QjhGTEprN2psaUNkdDVNSFdXRTdrRENNYUJCMFU3TU9YM2Y1MjBWYmVPcFVNcHZJc3VqMDV4U2QyaFc0Wks1WU14dEVtX1BPOWZLRC1MOE9jUjhSYWFxb3c1S1l1STU0WjYySHBSeXE2YUFPZUlzTnlsSlN0SkxpaVpIOFg0a2dTN1NTeDZEUE9jaGk5RncyYm9RNEV3ZzhzN1dnMHc5clFnRlFrUmp4T3ItOG55d2JzWE9IWVZrYU9ZUk0yX19pbXlKcldxM1FGYlFLeUZaQ05nQ1d0aUYtYlZaWlRDZVFBVkxXV0dnRXlRV1pnc3FzMURiLVlBTThmdmtQUHZ6alpvc0dGcjVIMjJSOWZVRHU2Yng4T3pzZm8wY1pkNDUwNmdHOEFzSGxzM3ZCdGZWN3Q1MlRaSW5mM0dvTVR2cDh2dzYxVHVzLXdmMkFLWmNrTFM0QXo0OTY2QVNNaGc2Q1pnczczb2o4VjZNY1Azc3Q3aUdrVGlvTk52MkxoNXg5Tk5BSkVZZURHQlhCeE42eE5yNEZjQmJiTjZPZ2JnWFFCdDROYXF5WGtsNmRiWml2WFFndHhTWXNQcnJzYXhnU1lZMm13WDdvOUJSS3BkMG9ZbzJTYzBWc05OeUxRUW1Xa3EyQkFUbW5EeFI5YU5FV19hRGI2UFVXVVl1cmVlSXM0ck9admVPYkNrMkFmbW1HX3Vjd0xlZ09KeWRGMEQ3MWhQMFpCM2hmSmdmQ2daY21JR2UwSkMxZUdkdmlZOVZzRUtXeHk2dEJEem5oYnJsbkZITjBsSTJVREh6MG90R1NFSUdsRUoyQk5pVWFiYndUMk9oRWlEUkhBLTFjVmNoOEhvMWhSaXY5RVFyVlExY2hNVnFTdFRKaXlVYVJQTGZBaXZsZUpZZEN5N3hyUmxvazBKdEozNkxUODZUS2N6RWNyaE52bWdtVVhCTHNKdk53R0NVTndYei1PRHd3c1d6ZXlQMldDMkpLNlhxcWt4VHNva2pMV3Z3b1JEdnQxdmVBb250UGV3ZE1tS05VMG11NDJ0VUYzSG5VZDExM3lYanlUczE0andmSi14NkxLUV9lUGRQeTdVa0lyeF8zSFFEQ244WUY5bUhJN0p5SEdTa3Y1c2E3X3VhREhLdV9GdUFhU2lFTmVoMDRYVnRQV28tLVlwaFJCLUxmVE9Xa3pUQVpuSzN0aXRVa1JWZlMwVndyS0VIcS1hYWhFTDJIZmNURWtiaEhGczFjbHJhTWxUWU1hWU1jV3B5UmQtRWFXV0F1STljSEV3Y3duTWJNcE9RPT0='

# Configuration app_config.json chiffrée (base64)
ENCRYPTED_APP_CONFIG = 'Z0FBQUFBQm84bFpqZ211UXhheVdXSVNUV1BzeGJ3U0tENDNkZHJGTWFZZGtFUllUNmhZUWc4RmFvY2hxYTdBZXlSQVpVbWlxM19GSVFzUlhPeWNqLV9rUFBMbVJTS0QzRndRLWMwWjZ2cW44T05pTGR1YUppNDN5eUFGVDU3N3A5SmZ0QXBfNkI5bE9EMFVmdXBkdVZ3MmQzVzBNRlF6SmtBOHhnb2hJVlFfTnFUbUh4UlJES3FmcWh3MTB0MWVpa1pvY2hINGJPOU9JOTlHUHlYV1FfRy1aWUN1VDBRNlU5WjBjTC1iMkpGcDJqbmc2TlNzTXBlS25SZDJMbHA3MjNoai1IME5HZU5WRllKQnplc1hEZnBxNnBmeTJCRVBqeE0wMF8wSHd1OV9Oa2s2aTVJem9faE1Wc2tvdnl0amdZZ3dGMVpaYlFxcXRLMlFHNHUzM1pwS25qTTZTSzJSNmdhTkhmU2o2Yk92WGNMSk03T2JWNVRxSk9vUzRFemVRUDVHQ0ctTzRlMVQyV1VPalhBRWNSZklEeWFaakZIdXJBUE9fRkxkMDVEM1VWM0RPZkFISjBwbEI2MGhmcGhtbDMzbWlsNk9lS19wSnlRYmV4cEpCWUpwTm5yQ3RLeHhvcFBTeUtlS3I1c0ZQcGUxZDl5a1U3OU9WUDQ0QXUyQmJxWGpqQzJMZGJPZlFlUDJIN3dtZ2IzakZjazBsUGVnZVRES0VBSUpnZkFtY0h2SWlJcnVaMW9DbUtrUlBzY3pFMUhzbUJmaFRRam1IMTBidWVBZ3ZJN2tFLVhTLUg3MDRyTjIwVWgweEpFMGJzMmo2TzFOcjRHOVNqOXRYRG1CUV9ucFB5LVNBY2hsd0x3VWhKeENCSVVwOE52Yl9oWDdoNFBuOWhsc0M5Rjg3a2wtaTNMNDBrdlpxMFRYSWhMTFV3RlZPYVN1YWNRa1ZGNGxPcEZPYllHb2EzRXdKYUVOWkRrel9QcUZGa1N6aUhacFhYZGFUTWtwWmlwQnVzTzBWQnZVZzFWb280ejU4ZWhHZThHRVB5VlppV1RGSzYtc2JpbXktQzNxZWZZZnk1bU9FRXBOVmpRZElfQ3RGeGVWSllTOFFqcmN3c3JaSTJEVno5NnBIZTVJSFJpVlJtRWRQMl9wUWcxQVdEYlFmNkZLQVNFYWtoMEx5RWFNekhNdTRPQW5OV1dXbm5MaUVnamVteldoWDhXN2YxWVNEMnljN0dzd1NlSUEyb2Y1Y3loZlBPY1ZucnhKdFNVMHM1SzlaaHZHZVVkWWZ2LVdGcFJmMmxiYU9fRW93NWVHYnhqdUMxVENtZ0lVeUMxNjlHYWxsbC1fc1JPTVRJWVBWZmFzbUgwM2drSE9DQTF0RGptUG5NME1mSUFEMlZjSTd0M2ZBclpXblJFREQ0ek03T0JYT0Zzb2hpblJRdjkxLXJDblpFd3kzQ2pzelBweHRXaWNVN29uMFdDWFNlOWJPWDN3ZjJiZjFudjZzVmpuWE82TFl1WlhlcUxLbFIxTlZSc0JUUW5GbzZNazhzQlpzWG9pdjh3bG10aGR0NUFtVm5QU19WcFphdjBCajhmd05MS21BQVpjeG1DTUtvZTNNWHlrMnd0ZG9EOWdpR1RyM0Nmbk9HUEFKZHFlMFU1a056YW9IaU1EQ2pqNVdWSFBVbG5xZ3REMy1JTllXWEsyOTN0a2dpeTdXMUtaMU5EU0pVaUhhOWd0dnlmQXljaGJPQzRUdjZYWUhBc1lwVE81ellkUm9yNWkzYXVkay12RTl4UWNqN2hjOE1nYUZ0YTM3YTB5YXdpbEVaRDZ2RW45NmNWV0hmeGJZeFljd01YaWpsSmZPLXQ0cTluNHV1YzM5NlpMMERJbWpXRUdqcl9PVnNKeFFwSzBKTmdyVzEtSnVURkRMd2hVN2V0MEtkU1lwOGc2cEpRWjN0SU9tWmZDakxHWXJiYlRDeVBnaFVWaUNVaXpNUUdPbHY0ek9pd0dfLXZ0MWFBSGxSaXRYNDBXQjJsbklUQ29NYkxrPQ=='

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
