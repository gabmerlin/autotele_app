"""
Constantes globales de l'application.
"""
from typing import Final

# Version de l'application
APP_NAME: Final[str] = "AutoTele"
APP_VERSION: Final[str] = "2.0.0"

# Limites Telegram
TELEGRAM_MAX_MESSAGE_LENGTH: Final[int] = 4096

# Rate limiting global optimisé pour multi-comptes
TELEGRAM_GLOBAL_RATE_LIMIT: Final[int] = 25  # Limite GLOBALE stricte (tous comptes confondus)
TELEGRAM_SAFETY_MARGIN: Final[float] = 0.90  # Marge de sécurité (90% = 22.5 req/s réelles)

TELEGRAM_MIN_DELAY_PER_CHAT: Final[float] = 0.5  # 1 msg toutes les 0.5 sec/chat (optimisé)
TELEGRAM_MAX_SCHEDULED_MESSAGES_FETCH: Final[int] = 100  # Limite de récupération des messages

# Limites de fichiers
MAX_FILE_SIZE_MB: Final[float] = 2.5
MAX_FILE_SIZE_BYTES: Final[int] = int(MAX_FILE_SIZE_MB * 1024 * 1024)

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

# Icônes - Utilisation de SVG uniquement
ICON_ACCOUNT: Final[str] = "settings"
ICON_MESSAGE: Final[str] = "edit"
ICON_SCHEDULED: Final[str] = "schedule"
ICON_CALENDAR: Final[str] = "calendar_today"
ICON_SUCCESS: Final[str] = "check_circle"
ICON_ERROR: Final[str] = "error"
ICON_WARNING: Final[str] = "warning"
ICON_INFO: Final[str] = "info"
ICON_FILE: Final[str] = "attach_file"
ICON_DELETE: Final[str] = "close"
ICON_REFRESH: Final[str] = "sync"

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

# Types de fichiers - Utilisation de noms d'icônes SVG
FILE_ICONS: Final[dict[str, str]] = {
    # Images
    '.jpg': 'photo',
    '.jpeg': 'photo',
    '.png': 'photo',
    '.gif': 'photo',
    '.webp': 'photo',
    '.bmp': 'photo',
    '.svg': 'image',
    # Documents
    '.pdf': 'description',
    '.doc': 'description',
    '.docx': 'description',
    '.txt': 'description',
    '.odt': 'description',
    '.rtf': 'description',
    # Vidéos
    '.mp4': 'videocam',
    '.avi': 'videocam',
    '.mov': 'videocam',
    '.mkv': 'videocam',
    '.wmv': 'videocam',
    '.flv': 'videocam',
    # Audio
    '.mp3': 'audiotrack',
    '.wav': 'audiotrack',
    '.ogg': 'audiotrack',
    '.m4a': 'audiotrack',
    '.flac': 'audiotrack',
    # Archives
    '.zip': 'folder_open',
    '.rar': 'folder_open',
    '.7z': 'folder_open',
    '.tar': 'folder_open',
    '.gz': 'folder_open',
    # Défaut
    'default': 'attach_file'
}

