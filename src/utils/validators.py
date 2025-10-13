"""Fonctions de validation pour l'application."""
import re
from typing import Tuple

# Type alias pour les résultats de validation
ValidationResult = Tuple[bool, str]


def _create_error(message: str) -> ValidationResult:
    """Crée un tuple d'erreur de validation."""
    return False, message


def _create_success() -> ValidationResult:
    """Crée un tuple de succès de validation."""
    return True, ""


def validate_phone_number(phone: str) -> ValidationResult:
    """
    Valide un numéro de téléphone au format international.

    Args:
        phone: Le numéro de téléphone à valider.

    Returns:
        ValidationResult: (is_valid, error_message).

    Examples:
        >>> validate_phone_number("+33612345678")
        (True, "")
        >>> validate_phone_number("0612345678")
        (False, "Le numéro doit commencer par + (ex: +33612345678)")
    """
    if not phone:
        return _create_error("Le numéro de téléphone est requis")

    phone = phone.strip()

    if not phone.startswith('+'):
        return _create_error(
            "Le numéro doit commencer par + (ex: +33612345678)"
        )

    if not re.match(r'^\+\d{10,15}$', phone):
        return _create_error("Format de numéro invalide")

    return _create_success()


def validate_account_name(name: str, min_length: int = 2,
                          max_length: int = 50) -> ValidationResult:
    """
    Valide un nom de compte.

    Args:
        name: Le nom du compte à valider.
        min_length: Longueur minimale autorisée.
        max_length: Longueur maximale autorisée.

    Returns:
        ValidationResult: (is_valid, error_message).
    """
    if not name:
        return _create_error("Le nom du compte est requis")

    name = name.strip()

    if len(name) < min_length:
        return _create_error(
            f"Le nom doit contenir au moins {min_length} caractères"
        )

    if len(name) > max_length:
        return _create_error(
            f"Le nom ne doit pas dépasser {max_length} caractères"
        )

    return _create_success()


def validate_verification_code(code: str,
                                min_length: int = 5) -> ValidationResult:
    """
    Valide un code de vérification.

    Args:
        code: Le code de vérification à valider.
        min_length: Longueur minimale du code.

    Returns:
        ValidationResult: (is_valid, error_message).
    """
    if not code:
        return _create_error("Le code de vérification est requis")

    code = code.strip()

    if not code.isdigit():
        return _create_error("Le code doit contenir uniquement des chiffres")

    if len(code) < min_length:
        return _create_error(
            f"Le code doit contenir au moins {min_length} chiffres"
        )

    return _create_success()


def validate_message(message: str, max_length: int = 4096) -> ValidationResult:
    """
    Valide un message.

    Args:
        message: Le message à valider.
        max_length: Longueur maximale autorisée.

    Returns:
        ValidationResult: (is_valid, error_message).
    """
    if not message:
        return _create_error("Le message ne peut pas être vide")

    message = message.strip()

    if len(message) > max_length:
        return _create_error(
            f"Le message ne doit pas dépasser {max_length} caractères"
        )

    return _create_success()


def validate_time_format(time_str: str) -> ValidationResult:
    """
    Valide un format d'heure HH:MM.

    Args:
        time_str: L'heure à valider (format HH:MM).

    Returns:
        ValidationResult: (is_valid, error_message).
    """
    if not time_str:
        return _create_error("L'heure est requise")

    time_str = time_str.strip()

    if not re.match(r'^\d{1,2}:\d{2}$', time_str):
        return _create_error("Format invalide (utilisez HH:MM)")

    try:
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1])

        if not (0 <= hour <= 23):
            return _create_error("L'heure doit être entre 0 et 23")

        if not (0 <= minute <= 59):
            return _create_error("Les minutes doivent être entre 0 et 59")

        return _create_success()
    except (ValueError, IndexError):
        return _create_error("Format invalide")


def format_time(time_str: str) -> str:
    """
    Formate une heure au format HH:MM.

    Args:
        time_str: L'heure à formater.

    Returns:
        str: L'heure formatée (HH:MM) ou la chaîne originale si invalide.
    """
    try:
        parts = time_str.split(':')
        hour = int(parts[0])
        minute = int(parts[1])
        return f"{hour:02d}:{minute:02d}"
    except (ValueError, IndexError):
        return time_str

