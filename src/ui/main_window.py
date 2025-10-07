"""
Fenêtre principale de l'application AutoTele
"""
import sys
import asyncio
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QTabWidget, QMessageBox, QStatusBar, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QFont

from ui.styles import STYLE_SHEET, FONT_FAMILY
from ui.account_manager import AccountManagerWidget
from ui.message_editor import MessageEditorWidget
from ui.dashboard import DashboardWidget
from ui.license_dialog import LicenseDialog

from core.telegram_manager import TelegramManager
from core.scheduler import MessageScheduler
from core.license_manager import LicenseManager
from utils.logger import get_logger
from utils.config import get_config


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    # Signaux
    license_verified = pyqtSignal(bool)
    
    def __init__(self):
        super().__init__()
        
        self.logger = get_logger()
        self.config = get_config()
        
        # Gestionnaires
        self.telegram_manager = TelegramManager()
        self.scheduler = MessageScheduler(self.telegram_manager)
        self.license_manager = LicenseManager()
        
        # Vérifier la licence au démarrage
        if not self._check_license():
            return
        
        # Initialiser l'interface
        self.init_ui()
        
        # Charger les sessions Telegram existantes
        self._load_sessions()
        
        # Démarrer le scheduler
        self._start_scheduler()
        
        # Vérification périodique de la licence
        self.license_timer = QTimer()
        self.license_timer.timeout.connect(self._periodic_license_check)
        self.license_timer.start(3600000)  # Toutes les heures
    
    def _check_license(self) -> bool:
        """Vérifie la licence au démarrage"""
        if not self.license_manager.is_license_valid():
            dialog = LicenseDialog(self.license_manager, self)
            result = dialog.exec()
            
            if result != QMessageBox.DialogCode.Accepted:
                # Licence non activée, fermer l'application
                self.logger.info("Application fermée : licence non valide")
                sys.exit(0)
                return False
        
        return True
    
    def _periodic_license_check(self):
        """Vérification périodique de la licence"""
        is_valid = self.license_manager.check_license_validity()
        
        if not is_valid:
            QMessageBox.warning(
                self,
                "Licence expirée",
                "Votre licence a expiré. L'application va se fermer.\n\n"
                "Veuillez renouveler votre abonnement pour continuer à utiliser AutoTele.",
                QMessageBox.StandardButton.Ok
            )
            self.close()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("AutoTele - Planificateur de Messages Telegram")
        self.setMinimumSize(1200, 800)
        
        # Appliquer le style
        self.setStyleSheet(STYLE_SHEET)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # En-tête
        header = self._create_header()
        layout.addWidget(header)
        
        # Onglets
        self.tabs = QTabWidget()
        
        # Dashboard
        self.dashboard_widget = DashboardWidget(self.scheduler, self.telegram_manager)
        self.tabs.addTab(self.dashboard_widget, "📊 Tableau de bord")
        
        # Gestionnaire de comptes
        self.account_manager_widget = AccountManagerWidget(self.telegram_manager)
        self.tabs.addTab(self.account_manager_widget, "👤 Comptes Telegram")
        
        # Éditeur de messages
        self.message_editor_widget = MessageEditorWidget(
            self.telegram_manager, self.scheduler
        )
        self.tabs.addTab(self.message_editor_widget, "✉️ Nouveau Message")
        
        layout.addWidget(self.tabs)
        
        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()
        
        # Timer pour rafraîchir l'interface
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_ui)
        self.refresh_timer.start(5000)  # Toutes les 5 secondes
    
    def _create_header(self) -> QWidget:
        """Crée l'en-tête de l'application"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Titre
        title = QLabel("AutoTele")
        title.setProperty("class", "title")
        title.setFont(QFont(FONT_FAMILY, 24, QFont.Weight.Bold))
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Statut de la licence
        license_status = self.license_manager.get_license_status()
        if license_status["is_trial"]:
            status_text = f"⏱️ Période d'essai : {license_status['trial_days_left']} jours restants"
        else:
            status_text = "✅ Licence active"
        
        self.license_label = QLabel(status_text)
        self.license_label.setProperty("class", "subtitle")
        layout.addWidget(self.license_label)
        
        # Bouton de licence
        license_btn = QPushButton("Gérer la licence")
        license_btn.setProperty("class", "secondary")
        license_btn.clicked.connect(self._show_license_dialog)
        layout.addWidget(license_btn)
        
        return header
    
    def _show_license_dialog(self):
        """Affiche le dialogue de gestion de licence"""
        dialog = LicenseDialog(self.license_manager, self)
        dialog.exec()
        
        # Mettre à jour l'affichage
        license_status = self.license_manager.get_license_status()
        if license_status["is_trial"]:
            status_text = f"⏱️ Période d'essai : {license_status['trial_days_left']} jours restants"
        else:
            status_text = "✅ Licence active"
        self.license_label.setText(status_text)
    
    def _load_sessions(self):
        """Charge les sessions Telegram existantes"""
        async def load():
            await self.telegram_manager.load_existing_sessions()
            accounts = self.telegram_manager.list_accounts()
            self.logger.info(f"{len(accounts)} compte(s) chargé(s)")
            
            # Rafraîchir l'interface
            self.account_manager_widget.refresh_accounts()
            self.message_editor_widget.refresh_accounts()
        
        # Exécuter dans la boucle d'événements
        asyncio.create_task(load())
    
    def _start_scheduler(self):
        """Démarre le scheduler de messages"""
        async def start():
            await self.scheduler.start_scheduler()
        
        asyncio.create_task(start())
        self.logger.info("Scheduler démarré")
    
    def _refresh_ui(self):
        """Rafraîchit l'interface utilisateur"""
        self.dashboard_widget.refresh()
        self._update_status_bar()
    
    def _update_status_bar(self):
        """Met à jour la barre de statut"""
        accounts = self.telegram_manager.list_accounts()
        connected = len([a for a in accounts if a["is_connected"]])
        
        stats = self.scheduler.get_statistics()
        
        status_text = (
            f"Comptes : {connected}/{len(accounts)} connectés | "
            f"Tâches : {stats['pending']} en attente, "
            f"{stats['completed']} terminées"
        )
        
        self.status_bar.showMessage(status_text)
    
    def closeEvent(self, event):
        """Gestion de la fermeture de l'application"""
        reply = QMessageBox.question(
            self,
            "Quitter AutoTele",
            "Êtes-vous sûr de vouloir quitter l'application ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Arrêter le scheduler
            self.scheduler.stop_scheduler()
            
            # Déconnecter les comptes
            async def disconnect():
                await self.telegram_manager.disconnect_all()
            
            asyncio.create_task(disconnect())
            
            self.logger.info("Application fermée")
            event.accept()
        else:
            event.ignore()

