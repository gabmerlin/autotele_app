"""
AutoTele - Application de planification Telegram.

Point d'entrée principal de l'application.
"""
import sys
import threading
import time
from pathlib import Path

# Ajouter le répertoire src au path (compatible PyInstaller)
if getattr(sys, 'frozen', False):
    # Mode compilé - les modules sont déjà dans l'exe
    pass
else:
    # Mode développement
    sys.path.insert(0, str(Path(__file__).parent))

from nicegui import ui

from ui.app import AutoTeleApp
from utils.constants import (
    APP_NAME,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_WINDOW_SIZE
)
from utils.logger import get_logger
from utils.notification_manager import reset_notifications
from utils.paths import get_temp_dir

logger = get_logger()


def _find_and_maximize_window() -> None:
    """Trouve et maximise la fenêtre de l'application."""
    try:
        import win32con
        import win32gui

        def enum_windows_callback(hwnd, _) -> bool:
            """Callback pour énumérer les fenêtres."""
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if APP_NAME in window_title:
                    win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            return True

        win32gui.EnumWindows(enum_windows_callback, None)
    except Exception as e:
        logger.error(f"Erreur maximisation: {e}")


def maximize_window_on_startup() -> None:
    """Maximise la fenêtre au démarrage (Windows uniquement)."""
    time.sleep(1.5)
    _find_and_maximize_window()


def cleanup_temp_files() -> None:
    """Nettoie les fichiers temporaires au démarrage."""
    try:
        temp_dir = get_temp_dir()
        if not temp_dir.exists():
            return

        for file in temp_dir.iterdir():
            if not file.is_file():
                continue

            try:
                file.unlink()
            except Exception as e:
                logger.warning(
                    f"Impossible de supprimer {file.name}: {e}"
                )
    except Exception as e:
        logger.error(f"Erreur nettoyage fichiers temporaires: {e}")


def main() -> None:
    """Point d'entrée principal de l'application."""
    # Configurer le dossier temp pour servir les fichiers uploadés
    temp_dir = get_temp_dir()

    # Nettoyer les fichiers temporaires du démarrage précédent
    cleanup_temp_files()

    # Réinitialiser le compteur de notifications
    reset_notifications()

    # Ajouter le dossier temp comme dossier de fichiers statiques
    from nicegui import app as nicegui_app
    nicegui_app.add_static_files('/temp', str(temp_dir))

    # Ajouter le dossier static pour les CSS (compatible PyInstaller)
    if getattr(sys, 'frozen', False):
        # Mode compilé - static à côté de l'exe
        static_dir = Path(sys.executable).parent / 'ui' / 'static'
    else:
        # Mode développement
        static_dir = Path(__file__).parent / 'ui' / 'static'
    
    static_dir.mkdir(parents=True, exist_ok=True)
    nicegui_app.add_static_files('/static', str(static_dir))

    app = AutoTeleApp()

    # Ajouter Material Icons directement dans le head
    ui.add_head_html(
        '<link href="https://fonts.googleapis.com/icon?'
        'family=Material+Icons" rel="stylesheet">'
    )

    @ui.page('/')
    def index() -> None:
        """Page d'accueil avec menu latéral."""
        app.setup_ui()

    # Démarrer la maximisation en arrière-plan (Windows uniquement)
    threading.Thread(
        target=maximize_window_on_startup,
        daemon=True
    ).start()

    # Lancer l'application
    ui.run(
        title=f'{APP_NAME} - Planificateur Telegram',
        host=DEFAULT_HOST,
        port=DEFAULT_PORT,
        reload=False,
        show=False,
        native=True,
        window_size=DEFAULT_WINDOW_SIZE,
        dark=False,
    )


if __name__ == '__main__':
    main()

