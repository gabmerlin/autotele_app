"""
Fonctions de validation pour l'application.
"""
import re
from typing import Tuple


def validate_phone_number(phone: str) -> Tuple[bool, str]:
    """
    Valide un numéro de téléphone.
    
    Args:
        phone: Le numéro de téléphone à valider
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not phone:
        return False, "Le numéro de téléphone est requis"
    
    phone = phone.strip()
    
    if not phone.startswith('+'):
        return False, "Le numéro doit commencer par + (ex: +33612345678)"
    
    # Vérifier que le reste contient uniquement des chiffres
    if not re.match(r'^\+\d{10,15}$', phone):
        return False, "Format de numéro invalide"
    
    return True, ""


def validate_account_name(name: str) -> Tuple[bool, str]:
    """
    Valide un nom de compte.
    
    Args:
        name: Le nom du compte à valider
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not name:
        return False, "Le nom du compte est requis"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Le nom doit contenir au moins 2 caractères"
    
    if len(name) > 50:
        return False, "Le nom ne doit pas dépasser 50 caractères"
    
    return True, ""


def validate_verification_code(code: str) -> Tuple[bool, str]:
    """
    Valide un code de vérification.
    
    Args:
        code: Le code de vérification à valider
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not code:
        return False, "Le code de vérification est requis"
    
    code = code.strip()
    
    if not code.isdigit():
        return False, "Le code doit contenir uniquement des chiffres"
    
    if len(code) < 5:
        return False, "Le code doit contenir au moins 5 chiffres"
    
    return True, ""


def validate_message(message: str, max_length: int = 4096) -> Tuple[bool, str]:
    """
    Valide un message.
    
    Args:
        message: Le message à valider
        max_length: Longueur maximale autorisée
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not message:
        return False, "Le message ne peut pas être vide"
    
    message = message.strip()
    
    if len(message) > max_length:
        return False, f"Le message ne doit pas dépasser {max_length} caractères"
    
    return True, ""


def validate_time_format(time_str: str) -> Tuple[bool, str]:
    """
    Valide un format d'heure HH:MM.
    
    Args:
        time_str: L'heure à valider (format HH:MM)
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not time_str:
        return False, "L'heure est requise"
    
    time_str = time_str.strip()
    
    if not re.match(r'^\d{1,2}:\d{2}$', time_str):
        return False, "Format invalide (utilisez HH:MM)"
    
    try:
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1])
        
        if not (0 <= hour <= 23):
            return False, "L'heure doit être entre 0 et 23"
        
        if not (0 <= minute <= 59):
            return False, "Les minutes doivent être entre 0 et 59"
        
        return True, ""
    except (ValueError, IndexError):
        return False, "Format invalide"


def format_time(time_str: str) -> str:
    """
    Formate une heure au format HH:MM.
    
    Args:
        time_str: L'heure à formater
        
    Returns:
        str: L'heure formatée (HH:MM)
    """
    try:
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1])
        return f"{hour:02d}:{minute:02d}"
    except (ValueError, IndexError):
        return time_str

