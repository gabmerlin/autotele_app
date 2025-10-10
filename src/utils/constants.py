"""
Constantes globales de l'application.
"""
from typing import Final

# Version de l'application
APP_NAME: Final[str] = "AutoTele"
APP_VERSION: Final[str] = "2.0.0"

# Limites Telegram
TELEGRAM_MAX_MESSAGE_LENGTH: Final[int] = 4096
TELEGRAM_RATE_LIMIT_PER_SECOND: Final[int] = 25
TELEGRAM_MIN_DELAY_BETWEEN_MESSAGES: Final[float] = 0.04  # 25 msg/sec
TELEGRAM_MIN_DELAY_PER_CHAT: Final[float] = 1.0  # 1 msg/sec/chat

# Configuration UI
DEFAULT_WINDOW_SIZE: Final[tuple[int, int]] = (1200, 800)
DEFAULT_HOST: Final[str] = "127.0.0.1"
DEFAULT_PORT: Final[int] = 8080

# Messages UI
MSG_NO_ACCOUNT: Final[str] = "Aucun compte configuré"
MSG_NO_CONNECTED_ACCOUNT: Final[str] = "Aucun compte connecté"
MSG_ACCOUNT_ADDED: Final[str] = "Compte ajouté avec succès !"
MSG_ACCOUNT_DELETED: Final[str] = "Compte supprimé"
MSG_CODE_SENT: Final[str] = "Code envoyé ! Vérifiez votre Telegram"
MSG_SELECT_ACCOUNT: Final[str] = "Veuillez sélectionner un compte"
MSG_SELECT_GROUP: Final[str] = "Veuillez sélectionner au moins un groupe"
MSG_ENTER_MESSAGE: Final[str] = "Veuillez entrer un message"
MSG_SELECT_DATE: Final[str] = "Veuillez ajouter au moins une date"

# Icônes
ICON_ACCOUNT: Final[str] = "⚙"
ICON_MESSAGE: Final[str] = "✎"
ICON_SCHEDULED: Final[str] = "⏱"
ICON_CALENDAR: Final[str] = "📅"
ICON_SUCCESS: Final[str] = "✅"
ICON_ERROR: Final[str] = "❌"
ICON_WARNING: Final[str] = "⚠️"
ICON_INFO: Final[str] = "ℹ️"
ICON_FILE: Final[str] = "📎"
ICON_DELETE: Final[str] = "✕"
ICON_REFRESH: Final[str] = "↻"

# Jours de la semaine
WEEKDAYS_SHORT: Final[list[str]] = ['L', 'M', 'M', 'J', 'V', 'S', 'D']
WEEKDAYS_LONG: Final[list[str]] = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']

# Mois
MONTHS_SHORT: Final[list[str]] = [
    'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin',
    'Juil', 'Août', 'Sep', 'Oct', 'Nov', 'Déc'
]
MONTHS_LONG: Final[list[str]] = [
    'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
]

# Types de fichiers
FILE_ICONS: Final[dict[str, str]] = {
    '.jpg': '🖼️',
    '.jpeg': '🖼️',
    '.png': '🖼️',
    '.gif': '🖼️',
    '.pdf': '📄',
    '.doc': '📝',
    '.docx': '📝',
    '.mp4': '🎥',
    '.avi': '🎥',
    '.mp3': '🎵',
    '.zip': '📦',
    'default': '📎'
}

