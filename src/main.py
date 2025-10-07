"""
Point d'entrée principal de l'application AutoTele
"""
import sys
import asyncio
from pathlib import Path

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
import qasync

from ui.main_window import MainWindow
from utils.logger import get_logger
from utils.config import get_config


def main():
    """Fonction principale"""
    # Initialiser la configuration
    config = get_config()
    logger = get_logger()
    
    logger.info("=" * 50)
    logger.info("Démarrage d'AutoTele")
    logger.info(f"Version : {config.get('app.version')}")
    logger.info("=" * 50)
    
    # Créer l'application Qt
    app = QApplication(sys.argv)
    app.setApplicationName("AutoTele")
    app.setOrganizationName("AutoTele")
    
    # Créer la boucle d'événements asyncio pour Qt
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Créer et afficher la fenêtre principale
    try:
        window = MainWindow()
        window.show()
        
        logger.info("Interface utilisateur chargée")
        
        # Exécuter l'application
        with loop:
            loop.run_forever()
    
    except Exception as e:
        logger.error(f"Erreur fatale : {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

