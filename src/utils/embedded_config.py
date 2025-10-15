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
ENCRYPTION_KEY = 'bWxyeWRJaXR5X1ZiNXJEbC1xYnd3Skc2bEtXRDBCOEs3RWVwY0x2UG91UT0='

# Configuration .env chiffrée (base64)
ENCRYPTED_ENV = 'Z0FBQUFBQm83My1zbjFXS0JXZUgxWTFfU2RTZ19FNS0zdVd1c01OUFQ3MFVPMFp4VXNINENnSE5VU29saVpnTVh0RDhhZGd0SWFsRk9ZdzBLcHF2Mi1zY1llbmxvMXBpZm5UdWtDME5KcU5kZmZER05acFhYcGVaZUxkVHZGT3llMlhRbWV5T2RMQkFIZ0dYWDRXZGdXcWNCQUpZTFE3d2g4NzBhSWIyTmFzVUdYaUsxZ01ab3l2VmdwWk9jVHQ5UllPQTB6WGdFMUktQ01mREtZUmgycTVCd2p6cWFXNDFITHp1YUZ5cnFoRTAtVHpYVjRZNERtWmJ5U0h2YVNOSk03UUhiWUZRYmM1d3R4NUthc21sUWJBWlV1UXlBTHFqdURBZ2xYY0dUWUt3SzJfSW5Dby1wOTcwV2trSVZLQ1dxYzdFcVBOZ3RTQ1J1b0gyMlE2bGg3bE9CNTl4VVBvanhCZ2p6N1pUZEtHVGUxZklQcURkQ2NsVnNKdkk2NDRTQk9oOHNOX3hReDNDRWVwSTNqNG5WYmFOcGZEM3BVNUlHcGx2UjJGcXI3Q2tYUV9WRC1uRUw0YkdlY1h3V2hhRXZ3YkprSEFtc3FDeEQxdTFWMEZXaG9sRVJESG1DUFZuUkd1OE5oZW42MVpjbjYzendEbVlZaG5lWWVtSWNHQk9odHBlejBPd1dzOHk2UHFNZDN6WVprQzVGVk5GODZQdWgxMDhTcEpmV1ZBTy1WSVlhbTBWYVJua05kNHRtMGxxdzdEcWJralZWMFJWSHJRb2o5WG1rWGJ1ajRMaWhuRXlzS1RzVDRZMHY5VGFnY1YwTXFvdVhYU1NpR3k3emdXLUluT09LbHlQOThZTm5hWlZUVURTcVRRaFRFVFhieS03ajl3Uk5IMG5od1l1ZkJueXpYdHZBc21ZdFloTWwxLUdOTWp6OWYyMjktbklsZFVSSUlHTEtKSzBNSkczTWlzbkpPbnF0bjFqdjZOb0owV2ppNWJrZTJLUjZESEMtUFVta1VtRTdRVEdSNm0wUzNpLTB0dlBYczJHak9PdEM1enVmaENBdF90WnpfMnFvMFVrVURGVllwSGR3YTJpVk9adVdNYWdDdk5kR0l5bmdwaGhKRVVqSGMzbWE5YnUxalhzYk1XZVkyd2U3U2ZRcDFPcE5WNWwwYUVOelFoYU0tZkFjMnZiQXlBaTc0dU9HQ25mbUxPc1ZLRHB2b1kwdEM1SWIxcUVUSG1zRThwb0NENnA2cjBDMVkyOHNnUWlrVWtEQ3FVVHFZR3gtcVd1UTdhVUdOU3lOQVNKVGN4bk9JVGpVX1VreDQ3Z0JZNWtQSVJfa0xmd0tkT2owbmJjcW5YQ3ZfQlR3ZW8tWVlWUTZhNHBtZ0FlNEFJQ1NaRG42Z1ZNQWRpOHRRRXVUc3pFVVRvaGszTjVYUG5aZXJ5S2tyNEdxbTVwaEZndlpNeUxoOVp1b1BCRzFRN0o1LU9jR1RzbDM3bXZaSFg5WHNsZUZYRmUtVVRyRVhSTHFSa2hQWjAzcHJiNHl1Q3M2ejJ3dVhadVZZeWJoaURmdmk5QmI2RUpNZFIxa0I3TjNNSmJTbUJZVHVxakZKa1J5d0E3VnNZUTZuV1V6LXdZaUtPTlhEYmpXR29mcjJRbVR2NklqdDB5MkNwTWVlUFRHbFJDTDJFblhibW9Ob0RKX2k5al9ZR2dla1dFX1RzR3RSRzVsUVZxM0lzb2hxT1A4TUhMUjNta1F3PT0='

# Configuration app_config.json chiffrée (base64)
ENCRYPTED_APP_CONFIG = 'Z0FBQUFBQm83My1zaUN5Y1hKUzlianFpZTROX3ZuUlhwaE9GMlpBdURxN0hGTUQtSkRjTTk5eDVGa1NpSi1PdEk0ZlgzQXE2UlpFd2NZUjdjU3JubTF5U28zWkR6X0Y3cVRpbDF1ZER0MUMzMDVYSzh3Rk5HcFY5Tm5LY2xMYU1MNVZFNFhGeW5NWUVxbllsR1RkRVhHamFFb2FXeHBUZGExQTU2UTF3LThpbG9IcUVaMU93Njc4NzU1ei1lQkJhSVRaclpsd1UzVXc4c0JDbkxPck5xeGx4YlBUeEtjallvYkFUcU9KNnVUeHlsM2c1N2VzUzZlUUpvY1NuNHQxbWdjbkFYX0hzZG4ySFBrZUwwUG1tajBSVFUzZS0wODZ4VlJ1N2dCbG4ycDd1NjZfZ0wxaHN4dkxZZWxBTGxleXFrNERYRjIyM0wxM1NWUEFtcTlnVG02Q1JWaWxCbmlkYWhVN1NwNXl4S3NOdktLUE1wckQzSlBCZnZWTGFDeDBRMzUzOFV4N0FnVE0ya2Q1SE1QOWt5REVUSmpSRXBWS1picHR4WEtQNTdrTExoWEhFNFM5VloxMmNuTHdqX0QtLWdEdExpV1gzLUs2cDlIM21qR3Z3QW5xWDlqUC0yai1NWWtoV0JqNzR1ZXlHMklVLWdlaUtLeGpyeU1RSlg5Y1M4blUwYTZ0R1Nyd3pScjEzb2lmbjVhQWlGNWJaU1RtbDQ2aklwZlA1MnFuYTYtT0dycmFHLVhYOWNYMjRxdjdIX0YxbUNkZVg5X2paZGh0dHo3eUQ5a0pqNno5c0Z4bGpySEdGVzJLM3lfYWVsQ3ljelVFSGpMVC1nU21ZMmZqS2Y3Z2R3UllMZlE0aEotNkU0a0FZeXhoeGdUVmFzZ0wyREFCcWI3ZEo5TXRTS2NhQXVxQUlrSnNPakhKb3ROdEtNYUFSb0taaUNSRVhkR3F6NFota2x4bTgzV19VOFBaRHZQOWl0Ni1TX1dQVGRObVI3ZndOLWx5VGFJZEx3Z2R3aDA0bjI4NXdHR3NuQ0htb0xiTW5SZm1YTENPZ3ZiOGxjT28xZVczTzhHaFMtTExqRkNZb0MtLUljRlVLa20tR1ppRElLLV9aRkk3R3JpRlNlcW05Z1NLd3o1bF95Xzh1RGJ3YUxWR1ZYa01ocUU1ZjBYaEJCZmE5TEE3eTA2SkkyUlk5eGU3ZmlnWW1HSlRod080eXI0Q29HZDdFYjBfbWFVOVJWV3pzblFJRG43d3Z6TThmWXpOb29xR2NjbHU1OFZ6MU5EYS1pUnA2bkd5aWMxZjJnR0h3a1VtakdoazZ6b3p3NmxoUmhfSDRUd2VkZTFYWkJTZmVYa1JQbTV6MXh2WjBOS0NvUVUwTlk2R3RFNUVkY1A3a2JUaTlyWjRsWGlsWXUtU2MxV1FSWGQ0WlhmSDdPYmhPX0hDdGlaZ0ZfUmU2VFoxTm9VbEMwSHZwTmRmcndWSDFiOWpFUXFHZXlQQUg0SkI4bUFkcUJBdG5MX3JEQkxCcjRQQUQxZkRaNEhra044OEFZYkNMeWdVRmlVZFl6TWNRVkI2VDI0ZTA0eEJmODVHVW1hRkFTLVBoaklOd0lJSkhvQ2xHMnNQaVVrT3VQSEYwN2x5Vk1LdE5ieWdfci00WXdtNFJ6T0haRXhrZ1hzZTJfSE9pWVUyZ0Uyb3hmUGlLSG1mZlVZZHFIR1g2SGtiOHJLaXRJY2NWS2dEbWJUbWxBZ0d1Rm8zSU9PTmpnNjJCMWNrVGpvUlRBVTdidHhnT1NCUTF4SVBEUHRldzJ1NTlzRHU2MHJtQXlqRjZ2SHpBRzV3YVhsVGltck93WUJkVEI0VlItZE9TYUpYNmdVX1BZVUxUNTh0OGpmRmZkUzFqcGN1bV9Xdno3WFU5QTVkQVpwNS0tcTctN1Vjc2hLMXBIQm5ibks4MzYxTThrbU43M1VkaFc1OE9LWWxFakNrVVFnUmRsOE5EMXY3TFdFZGVLRnh2VkpOT2RuUHVLTklmdnZycGdpemxTNUFocVg0PQ=='

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
    """Configure les variables d'environnement depuis la configuration chiffrée"""
    try:
        env_content = get_decrypted_env()
        if env_content:
            # Parser le contenu .env et définir les variables d'environnement
            for line in env_content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip().strip('"\'')
            return True
    except Exception as e:
        print(f"Erreur lors du chargement des variables d'environnement: {e}")
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
