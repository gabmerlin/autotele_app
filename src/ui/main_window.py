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

from ui.modern_styles import get_modern_style, get_colors
from ui.account_manager import AccountManagerWidget
from ui.message_wizard import MessageWizard
from ui.scheduled_messages import ScheduledMessagesWidget
from ui.active_tasks import ActiveTasksWidget
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
        self.setMinimumSize(800, 700)
        self.resize(800, 700)
        
        # Appliquer le style moderne
        self.setStyleSheet(get_modern_style())
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # En-tête
        header = self._create_header()
        layout.addWidget(header)
        
        # Onglets
        self.tabs = QTabWidget()
        
        # 1. Gestionnaire de comptes
        self.account_manager_widget = AccountManagerWidget(self.telegram_manager)
        self.tabs.addTab(self.account_manager_widget, "👤 Comptes Telegram")
        
        # 2. Tableau de bord (Gestion des messages programmés)
        self.scheduled_messages_widget = ScheduledMessagesWidget(self.telegram_manager)
        self.tabs.addTab(self.scheduled_messages_widget, "📊 Tableau de bord")
        
        # 3. Envois en cours
        self.active_tasks_widget = ActiveTasksWidget(self.telegram_manager, self.scheduler)
        self.tabs.addTab(self.active_tasks_widget, "📤 Envois en cours")
        
        # 4. Wizard de messages (étape par étape)
        self.message_wizard_widget = MessageWizard(
            self.telegram_manager, self.scheduler
        )
        self.tabs.addTab(self.message_wizard_widget, "✉️ Nouveau Message")
        
        # Connexion pour rafraîchir quand on change d'onglet
        self.tabs.currentChanged.connect(self._on_tab_changed)
        
        layout.addWidget(self.tabs)
        
        # Rafraîchir le premier onglet au démarrage avec un délai plus long
        QTimer.singleShot(2000, lambda: self._on_tab_changed(0))
        
        # Barre de statut
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status_bar()
        
        # Timer pour rafraîchir l'interface (seulement la barre de statut)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._update_status_bar)
        self.refresh_timer.start(10000)  # Toutes les 10 secondes (suffisant pour les stats)
    
    def _create_header(self) -> QWidget:
        """Crée l'en-tête de l'application"""
        header = QWidget()
        header.setObjectName("header")
        header.setStyleSheet("#header { background-color: #4A90E2; border-radius: 6px; padding: 8px; }")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Titre
        title = QLabel("📱 AutoTele")
        title.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(title)
        
        layout.addStretch()
        
        # Statut de la licence
        license_status = self.license_manager.get_license_status()
        if license_status["is_trial"]:
            status_text = f"⏱️ Essai : {license_status['trial_days_left']}j restants"
        else:
            status_text = "✅ Licence active"
        
        self.license_label = QLabel(status_text)
        self.license_label.setFont(QFont("Segoe UI", 9))
        self.license_label.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(self.license_label)
        
        # Bouton de licence
        license_btn = QPushButton("⚙️")
        license_btn.setMaximumWidth(35)
        license_btn.setToolTip("Gérer la licence")
        license_btn.setStyleSheet("background: white; color: #4A90E2; border: none; border-radius: 4px; padding: 5px;")
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
            self.message_wizard_widget.refresh_accounts()
        
        # Exécuter dans la boucle d'événements
        # asyncio.create_task(load())  # Commenté temporairement
        
        # Charger les sessions de manière synchrone
        try:
            # Debug des sessions
            self.telegram_manager.debug_sessions()
            
            # Charger les sessions (elles restent connectées)
            self.telegram_manager.load_existing_sessions()
            
            # Vérifier les connexions en arrière-plan
            def verify_connections_sync():
                try:
                    # Utiliser la boucle d'événements existante
                    loop = asyncio.get_event_loop()
                    
                    async def verify_connections():
                        await self.telegram_manager.verify_all_connections()
                        # Rafraîchir l'interface après vérification
                        self.account_manager_widget.refresh_accounts()
                        self.message_wizard_widget.refresh_accounts()
                        
                        accounts = self.telegram_manager.list_accounts()
                        connected_accounts = [a for a in accounts if a["is_connected"]]
                        self.logger.info(f"✅ {len(connected_accounts)} compte(s) réellement connecté(s) sur {len(accounts)}")
                    
                    # Créer la tâche dans la boucle existante
                    asyncio.create_task(verify_connections())
                    
                except Exception as e:
                    self.logger.error(f"Erreur vérification connexions: {e}")
            
            # Lancer la vérification en arrière-plan avec un délai
            QTimer.singleShot(1000, verify_connections_sync)
            
            # Rafraîchir l'interface immédiatement (avant vérification)
            self.account_manager_widget.refresh_accounts()
            self.message_wizard_widget.refresh_accounts()
            
            accounts = self.telegram_manager.list_accounts()
            self.logger.info(f"📁 {len(accounts)} compte(s) chargé(s) (vérification en cours...)")
            
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement des sessions: {e}")
    
    def _start_scheduler(self):
        """Démarre le scheduler de messages"""
        print("=" * 60)
        print("DEBUG: _start_scheduler appelé")
        print("=" * 60)
        
        async def start():
            print("DEBUG: Fonction async start() appelée")
            self.logger.info("🚀 Démarrage du scheduler...")
            await self.scheduler.start_scheduler()
        
        # Utiliser QTimer pour éviter les conflits asyncio
        import asyncio
        from PyQt6.QtCore import QTimer
        
        def launch():
            print("DEBUG: Fonction launch() appelée")
            self.logger.info("⏰ Lancement du scheduler dans 1 seconde...")
            task = asyncio.create_task(start())
            print(f"DEBUG: Task créée: {task}")
        
        QTimer.singleShot(1000, launch)
        self.logger.info("✅ Scheduler programmé pour démarrage")
        print("DEBUG: QTimer configuré")
    
    def _on_tab_changed(self, index):
        """Rafraîchit l'onglet quand on le sélectionne"""
        if index == 0:  # Comptes Telegram
            self.account_manager_widget.refresh_accounts()
        elif index == 1:  # Tableau de bord
            # Rafraîchir les comptes ET les messages programmés
            self.scheduled_messages_widget.refresh_accounts()
        elif index == 2:  # Envois en cours
            self.active_tasks_widget.refresh_tasks()
        elif index == 3:  # Nouveau Message
            self.message_wizard_widget.refresh_accounts()
    
    def _refresh_ui(self):
        """Rafraîchit l'interface utilisateur (désactivé - on utilise _on_tab_changed)"""
        # Cette méthode n'est plus utilisée - refresh seulement sur changement d'onglet
        pass
    
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

