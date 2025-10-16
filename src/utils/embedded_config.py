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
ENCRYPTION_KEY = 'VEw5bEVGWVRuMC11N3cwOWFfaHR1Tlo1dzMyNHhZaFBMeDdVeVFzOWhsND0='

# Configuration .env chiffrée (base64)
ENCRYPTED_ENV = 'Z0FBQUFBQm84SnlCckI0WTNmdllSOVY5UUZFQ0k1VzhfN2JrSzlQV3Ixa3NYaU4zSV91b3FkN1VoTWtrX0E1RWd2emFsRXVBOFNPSUtZQ3VOQk5zejhfMzlxczlKOWYwOGl2VlRPelB4VlV4TUJGZk5lRjdRNjBxN1Q4dXk4S2NwX2tDNHNTejFLNnJwZ0Y4NVdsRWdIeERjSkVERnBva1RTRHJ2bkVleXdDckFJNTR3Uk1vb1FXaFhGaEM3Q1dXRU9iNTN2eFFhd1VqVi1hQVlYX19SbXJ1NTVBN3NTNEw1UzhXcGdFdzBydkNRaTl2THYtVVgzMC02VmVjTFcwUWNidEZUVkVxYmFoZzYxTmxHaHdzbjRaMHFTUjJhbENzVzdmbDBENXFmR0NIb2RFMWtrV3JnWlRKOTlNZ1Vod1RzMDZaLS1VZlZpYlFJdVcxSVVKZ251cWQ3cllUZFFMRkpfRVNfOTdPcG5iVEFMWUJJS3UxWFRuU08xbUxjTVB5dVVHWkxNMDM5SU1Bd1dsWUtUSFFNQWZaWGM5NHlTdGdxRmZFdE5mbUJBWmJqVVh2ZWZUV0VXaVZPRm5JMVhQa2U3SGFEb25MTnpTbElzQVBHNm16VVllN1k0R0xLV3Vsa3hhSTlLMmVScGpvVFhPMjBoOG1MRk9UMnNwejBuOWIzUC1qYkRxWERDem55OXF3UEVDTUNwQVhyVERIajVmLVFDOFU2cVFKVGxTVjJTclVkLURLTUQ0dU1sM194SEJsbTREdzB5NUF3SnFfblJBa3ZQS0VxOFFJVmh6YlhFaHdsRFo2Z1hvYk5qS09GTGtHZzEyVHhheEJDNmZ1ZDFmQlh6ZHNQU0c1S2h4VlhJZUlqTDFMSXY4TGl0WXo4dTFkSi1QT0EyYU1INzhveXM5T3FzdkFaUXNzT1lWdXlwRUMySjlpUlhRVlRHel9icjFpd1pWdF94SXdmUTJ6ODIzTWpmOEoyb3RDS19aVFpOVVZyTzlCMV9kdjlfSXlnd3lIZnlOX1BYa3hrVXRiV2Q4cHpRN0pXN2VfUFFNVnBmeUk5ZldfenhqVUZfcjVsYUl0RkhRWFdFbDdPc0JaMVFfUG9IVnQ4ZGJBZHhtenBpSlRTd3ZzUGIxcGRUUDFzN0xEU1NnTHZRZ1YtYXBSV256Qk12WTBwZk1qeVRBRUQ2aVRud2JhemFyeTQwdEZvZ3lndzlpZ0w2S2tUQUdGMHNMWjVGNlJFcjc3YVVob29hdzk5c3JmQkJYN2NXdUF2OEE0U01LUWpoTVNoSW1hb3BEeC12dVNEVlhvcG1rVnl4M0tzVjVGWDVWZVYxcGNZZjlQSkRzV1pSdnN4V2FVOUVaZEtxWkxYaDFSdnRETmRGLWo1RHVnR2tXV09aa29YZkd6aXkwRW1vUjdaTW9yZS11VkplV1F5ZWY3RjhqRDNiZVpRMUhVSHpRR0pIS1VrdG5jQXkxc1FEanoxZ1RVVFJBTFFod1NWZGx4SER3UmhGdWdXdGlvQ1o5dlFFaUtCeUVPZXc0S3NYRWhzd05zNkpXVDAyc0gwN0M1SzdGejdkeWZzb3hHNTA3YTMtOHZxMmtkYVY2UG90NXVpZHBacFR1Q3JfNUQ4djhpZFdtMnBBZXdHUC1BWFhtSTllQmxiUnJXRWwyRDNLcEVZaFE1LWE1WnZEVUVZa29XSjE3cEJERFRKdXR4Z0FzLVNYWGZEUlpocjlLcXRSVVVsbGM1d2Rtc0t3PT0='

# Configuration app_config.json chiffrée (base64)
ENCRYPTED_APP_CONFIG = 'Z0FBQUFBQm84SnlCQ1MwM2VPMng0bmdRZzVNMkkyWVVLQnNIcjZfN3R1UkZ3ZGlzeTR5TXMyN0theTY3d2Z4UjdvRXpyM0NFWFdSUGo2Sldnc2dBSGhNQ3ZSV0NYN0JVYUs2ZEVLS25zZXpMclp5MGVEMDVUcjdZamNRbG1pdm9VRk9OSGt5X2ZHMHJ2NEJkLTBBSkhGUWF5UEJ1dWtUUVk5RTVtZmhjQ0ZvbS1rakt3R2pfMV9zWmZQNGZRVXptbWR4NWNUTl9UdTJDUWxtQzVvdzBXS3drUnF4UllKMGpLb2dMY1EyZnBwV21XaW5haVNGSkZGallmazQ4a2pCMVRzR2tVRlYtUnBGOXlUWi1JeGxHcGpoY3BtODh6aDh2UDVhTE5oTVVSRjBVOFl5ZlJnVkd0enlCVEZIakNpX0tfeDhMZzR3NXNPQW1hQjBjVTVUbHpIdmJTeC1faUh2MkxkaUpZSTVuS1d2SEtiOWtacGpxNzNWWlhXR2ZGNjc1bV9oczVfYXlkZjZUWUJIclJNdmVYV2xTcjZBbk1lZVlfdE5XVjhnOEc3LW5jNVJvekJacHk0emd4TlIwaXpXckJqVGN4MFNPN2FYdHJBYnNIMGdOY1VuVDB2NWhYQ01mTUpuVC1kcDU5UC15LW5Iak5CN3Bkb09wMG00Z1plYmxac1Q5a2NVYUFCaHY3SXpITVhBOTFiYmI2d05oendUdFp3Rll3a25zZU5FdkJPOG0xR0p3SlEwOFdyVzE2Nnp5MjZERllJbDhrZnRlNmItbXVISk9nQTJFNzE3bmpFVXhCcUJiNC1ZWGlxblhGX1huLW05MUZKQkMxdGh2dkp3OWxpN01tM1ZmVW16WTc4UjU3Q0JpaV9yeHdWNE1qaTN5Zjg4dUY1djJ0em9lOXJreWhOdkljZE1fZEpSTzhqWUtlbzRVU3hFVHhiUmJGcUFEX3pZX0E3ZExJSnR0QWdVenFkZ0EyMmJfRmprSjFWX05XMnpzMkwyZ0N5b1F6eTBZMTQyNWlBQ2stYWZDT292ZHB6c002QW9nNGFiYkpJQnM2MTBIRTdObEZFcTYzdnMzVmdjMDFXT2RMcTh0V0s0MVdQVVY3ak1TMzF6UlNLOUd5dXUwZElMUnhlRFZwZjRYYjQ3Um9ONlQtV0t5YUhkeVVBQjhmOTVWcGJKMU1CYW5kRmQ5a2RhaWdwQ0NNSkF1ck9waVh1M2lSZVNlZ2N1Rzc0VmpFd2tKXy0yUjNwSDVfdzJtZ3Jaa0ZrOEozT053TXk3YWhyNzJCZmZLVnlhNFhLVlhYbWptMGFGa0RtV1pOV19nYmExbzAxc09fbFRKemU1RGFMaGVDNVJ5SURaSGlMUFMtMHBqaE0tQnhzVjNRdVNMeU4wNXM1aVgyZWtXbHg4bTNYRC1rWTkxMnd2NFZsamtOUjMzeXQ0dTNRNWpzWWdqX1V1RkRaU0w1bmpXaWY1MFgwLTNVYXZFX1c2V3k5SGRhLVRKcjM1eGIyY0VBc25JLU1Eak5TbFNSZGJOMGFDTzhtU3dOR1V0UzZjN1RhenlfTWlsZmpXSS1NS0JOWTV3UW5WdDFNU1pHLWhBS21obHU3SGZ1cE9yWVVtN3o1V1ZXR19CbU1kNWdYbmlUSGt5ajc3UFBUWTB0UXpFR0RpZkplLVhSdG42dFpWQlBMcW5RNWItWmc2YVlyRWV1ODdkNE5ILXdyRkkzNFdBbDRkbzhVWk4xVDRsOTVVNDl5UElVLV90QThpRVV5V2gwTWNKejJaWWtvcDZrT19OR293N2VrYzJWMThaaUhoS0tsU0phczhTY0lRUWJ5cXAwZU1mZ0UyUUtvQnlaWUhMQXVUQ2JmbWV0ZU1ZZnNUUGU1aUxOdWpnX01EMkhFZUhPWG1nNGthbElscXZ0bk1uWWJ4akJBLTNob0dTTnFCTmZyM1B0VHBtX1VsRlRUdlNNaDRMT3dyVFBiU0M1SEZjY0YxME9iVC1pRGZvZTJ3MHY5d2V0YXIzLWZ3MGJJS2pxYndsQ3ZRPQ=='

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
    """Injecte les variables d'environnement déchiffrées dans os.environ"""
    try:
        env_content = get_decrypted_env()
        if not env_content:
            print("Attention : Aucune configuration .env trouvée")
            return
        
        # Parser le contenu .env et injecter dans os.environ
        for line in env_content.split('\n'):
            line = line.strip()
            # Ignorer les lignes vides et les commentaires
            if not line or line.startswith('#'):
                continue
            
            # Parser la ligne KEY=VALUE
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                # Retirer les guillemets si présents
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                os.environ[key] = value
        
        print("[OK] Variables d'environnement chargées depuis la configuration embarquée")
    except Exception as e:
        print(f"Erreur lors du chargement des variables d'environnement: {e}")

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
