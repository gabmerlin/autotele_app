"""
Module d'anonymisation des données sensibles pour la conformité RGPD.

Ce module fournit des fonctions pour anonymiser les données personnelles
avant qu'elles ne soient loguées ou stockées.
"""
import hashlib
import re
from typing import List, Union


def anonymize_phone(phone: str) -> str:
    """
    Anonymise un numéro de téléphone.
    
    Args:
        phone: Numéro de téléphone (ex: +33612345678)
        
    Returns:
        str: Numéro anonymisé (ex: +33***78)
        
    Examples:
        >>> anonymize_phone("+33612345678")
        '+33***78'
        >>> anonymize_phone("John Doe")
        'Jo***oe'
    """
    if not phone:
        return "***"
    
    if len(phone) <= 6:
        return "***"
    
    # Garder le début et la fin
    return f"{phone[:3]}***{phone[-2:]}"


def anonymize_username(username: str) -> str:
    """
    Anonymise un nom d'utilisateur ou nom de compte.
    
    Args:
        username: Nom d'utilisateur
        
    Returns:
        str: Nom anonymisé
        
    Examples:
        >>> anonymize_username("JohnDoe123")
        'Jo***23'
    """
    if not username:
        return "***"
    
    if len(username) <= 4:
        return "***"
    
    return f"{username[:2]}***{username[-2:]}"


def hash_identifier(identifier: Union[str, int], prefix: str = "") -> str:
    """
    Hash un identifiant avec SHA256 (tronqué pour lisibilité).
    
    Args:
        identifier: Identifiant à hasher (ID de groupe, etc.)
        prefix: Préfixe optionnel pour identifier le type
        
    Returns:
        str: Hash tronqué (12 caractères)
        
    Examples:
        >>> hash_identifier(123456789, "grp")
        'grp_a1b2c3d4e5f6'
    """
    hash_obj = hashlib.sha256(str(identifier).encode())
    hash_hex = hash_obj.hexdigest()[:12]
    
    if prefix:
        return f"{prefix}_{hash_hex}"
    return hash_hex


def anonymize_group_ids(group_ids: List[int]) -> List[str]:
    """
    Anonymise une liste d'IDs de groupes.
    
    Args:
        group_ids: Liste d'IDs de groupes
        
    Returns:
        List[str]: Liste d'IDs hashés
        
    Examples:
        >>> anonymize_group_ids([123, 456, 789])
        ['grp_...', 'grp_...', 'grp_...']
    """
    return [hash_identifier(gid, "grp") for gid in group_ids]


def sanitize_message_preview(message: str, max_length: int = 100) -> str:
    """
    Nettoie un aperçu de message pour les logs (sans contenu sensible).
    
    Au lieu de logger le contenu réel, on log juste des statistiques.
    
    Args:
        message: Message complet
        max_length: Longueur maximale (par défaut 100)
        
    Returns:
        str: Description sanitisée du message
        
    Examples:
        >>> sanitize_message_preview("Bonjour, voici mon numéro: +33612345678")
        '[Message: 42 chars, 6 words, contains: URLs=0, Phones=1, Emails=0]'
    """
    if not message:
        return "[Message vide]"
    
    # Statistiques du message (sans révéler le contenu)
    char_count = len(message)
    word_count = len(message.split())
    
    # Détecter les éléments sensibles
    url_count = len(re.findall(r'https?://\S+', message))
    phone_count = len(re.findall(r'\+?\d{10,}', message))
    email_count = len(re.findall(r'\S+@\S+\.\S+', message))
    
    return (
        f"[Message: {char_count} chars, {word_count} words, "
        f"contains: URLs={url_count}, Phones={phone_count}, Emails={email_count}]"
    )


def anonymize_email(email: str) -> str:
    """
    Anonymise une adresse email.
    
    Args:
        email: Adresse email
        
    Returns:
        str: Email anonymisé
        
    Examples:
        >>> anonymize_email("john.doe@example.com")
        'jo***@ex***.com'
    """
    if not email or '@' not in email:
        return "***@***.***"
    
    local, domain = email.split('@', 1)
    
    # Anonymiser la partie locale
    if len(local) > 4:
        local_anon = f"{local[:2]}***"
    else:
        local_anon = "***"
    
    # Anonymiser le domaine
    if '.' in domain:
        domain_parts = domain.split('.')
        domain_anon = f"{domain_parts[0][:2]}***.{domain_parts[-1]}"
    else:
        domain_anon = "***"
    
    return f"{local_anon}@{domain_anon}"


def get_anonymized_summary(data: dict) -> dict:
    """
    Crée un résumé anonymisé d'un dictionnaire de données.
    
    Args:
        data: Dictionnaire contenant des données potentiellement sensibles
        
    Returns:
        dict: Dictionnaire avec données anonymisées
        
    Examples:
        >>> get_anonymized_summary({
        ...     'phone': '+33612345678',
        ...     'groups': [123, 456],
        ...     'message': 'Hello world'
        ... })
        {
            'phone': '+33***78',
            'groups_count': 2,
            'message_info': '[Message: 11 chars, 2 words, ...]'
        }
    """
    anonymized = {}
    
    for key, value in data.items():
        if key in ['phone', 'telephone', 'number']:
            anonymized[key] = anonymize_phone(str(value))
        elif key in ['username', 'account', 'user']:
            anonymized[key] = anonymize_username(str(value))
        elif key in ['email', 'mail']:
            anonymized[key] = anonymize_email(str(value))
        elif key in ['groups', 'group_ids', 'chats']:
            if isinstance(value, list):
                anonymized[f'{key}_count'] = len(value)
                anonymized[f'{key}_sample'] = anonymize_group_ids(value[:3])
            else:
                anonymized[key] = value
        elif key in ['message', 'text', 'content']:
            anonymized[f'{key}_info'] = sanitize_message_preview(str(value))
        else:
            # Pour les autres champs, les garder tels quels
            anonymized[key] = value
    
    return anonymized


# Exemples d'utilisation
if __name__ == "__main__":
    # Test des fonctions
    print("Anonymisation des données sensibles:")
    print(f"Téléphone: {anonymize_phone('+33612345678')}")
    print(f"Username: {anonymize_username('JohnDoe123')}")
    print(f"Email: {anonymize_email('john.doe@example.com')}")
    print(f"Group ID: {hash_identifier(123456789, 'grp')}")
    print(f"Message: {sanitize_message_preview('Bonjour, contactez-moi au +33612345678')}")

