"""
Widget de gestion des comptes Telegram
"""
import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QDialog, QLineEdit, QMessageBox,
    QGroupBox, QFormLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from core.telegram_manager import TelegramManager
from ui.modern_styles import get_colors


class AddAccountDialog(QDialog):
    """Dialogue pour ajouter un compte Telegram"""
    
    def __init__(self, telegram_manager: TelegramManager, parent=None):
        super().__init__(parent)
        
        self.telegram_manager = telegram_manager
        self.session_id = None
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        self.setWindowTitle("Ajouter un Compte Telegram")
        self.setMinimumSize(550, 550)  # Taille minimale plus grande
        self.resize(550, 550)  # Taille initiale plus grande
        self.setModal(True)
        
        # Forcer le redimensionnement après un court délai
        QTimer.singleShot(100, self._force_resize)
        
        # S'assurer que la fenêtre est centrée et visible
        QTimer.singleShot(200, self._center_and_show)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title = QLabel("📱 Connecter un Compte Telegram")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        subtitle = QLabel("Authentification simplifiée en 2 étapes")
        subtitle.setFont(QFont("Segoe UI", 9))
        subtitle.setStyleSheet("color: #7F8C8D;")
        layout.addWidget(subtitle)
        
        # Instructions
        info = QLabel(
            "Connectez votre compte Telegram en quelques secondes !\n\n"
            "📱 Vous aurez besoin de :\n"
            "• Votre numéro de téléphone Telegram\n"
            "• Le code de vérification que vous recevrez sur Telegram\n"
            "• Votre mot de passe 2FA (si activé)"
        )
        info.setProperty("class", "hint")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Formulaire simplifié - COMPACT
        form_group = QGroupBox("Informations du Compte")
        form_layout = QFormLayout(form_group)
        form_layout.setSpacing(8)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Mon compte recrutement")
        self.name_input.setMaximumHeight(30)
        self.name_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 13px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        form_layout.addRow("Nom :", self.name_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+33612345678")
        self.phone_input.setMaximumHeight(30)
        self.phone_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 13px;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        form_layout.addRow("Téléphone :", self.phone_input)
        
        layout.addWidget(form_group)
        
        # Zone de vérification (cachée au départ) - COMPACTE
        self.verification_group = QGroupBox("Vérification")
        verification_layout = QVBoxLayout(self.verification_group)
        verification_layout.setSpacing(8)
        
        # Code de vérification - COMPACT
        code_layout = QHBoxLayout()
        code_label = QLabel("Code :")
        code_label.setMinimumWidth(80)
        code_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        code_layout.addWidget(code_label)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Code reçu sur Telegram")
        self.code_input.setMaximumHeight(32)
        self.code_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 13px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        code_layout.addWidget(self.code_input)
        verification_layout.addLayout(code_layout)
        
        # Mot de passe 2FA - COMPACT
        password_layout = QHBoxLayout()
        password_label = QLabel("2FA :")
        password_label.setMinimumWidth(80)
        password_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        password_layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe 2FA (si activé)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMaximumHeight(32)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 8px;
                font-size: 13px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #3498db;
                background-color: #f8f9fa;
            }
        """)
        password_layout.addWidget(self.password_input)
        verification_layout.addLayout(password_layout)
        
        self.verification_group.hide()
        layout.addWidget(self.verification_group)
        
        # Message d'erreur
        self.error_label = QLabel()
        self.error_label.setProperty("class", "error")
        self.error_label.setWordWrap(True)
        self.error_label.setStyleSheet("""
            QLabel {
                background-color: #ffebee;
                border: 2px solid #f44336;
                border-radius: 8px;
                padding: 10px;
                color: #d32f2f;
                font-weight: bold;
            }
        """)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.send_code_btn = QPushButton("Envoyer le code")
        self.send_code_btn.clicked.connect(self._send_code)
        buttons_layout.addWidget(self.send_code_btn)
        
        self.verify_btn = QPushButton("✅ Vérifier")
        self.verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.verify_btn.clicked.connect(self._verify_code)
        self.verify_btn.hide()
        buttons_layout.addWidget(self.verify_btn)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def _send_code(self):
        """Envoie le code de vérification"""
        # Validation
        phone = self.phone_input.text().strip()
        name = self.name_input.text().strip() or phone
        
        if not phone:
            self.error_label.setText("⚠️ Veuillez entrer votre numéro de téléphone")
            self.error_label.show()
            return
        
        # Envoyer le code (approche simplifiée)
        def send_sync():
            try:
                # Afficher un message de chargement
                self.error_label.setText("🔄 Envoi du code en cours...")
                self.error_label.show()
                self.send_code_btn.setEnabled(False)
                self.send_code_btn.setText("🔄 Envoi...")
                
                # Utiliser la boucle d'événements existante
                import asyncio
                loop = asyncio.get_event_loop()
                
                async def send():
                    try:
                        success, message, session_id = await self.telegram_manager.add_account(
                            phone, name
                        )
                        
                        # Utiliser QTimer pour les mises à jour UI (thread-safe)
                        def update_ui():
                            if success:
                                self.session_id = session_id
                                self.error_label.hide()
                                self.verification_group.show()
                                self.send_code_btn.hide()
                                self.verify_btn.show()
                                
                                QMessageBox.information(
                                    self,
                                    "Code envoyé",
                                    f"Un code de vérification a été envoyé sur votre Telegram.\n\n"
                                    f"Entrez le code ci-dessous pour continuer.",
                                    QMessageBox.StandardButton.Ok
                                )
                            else:
                                self.error_label.setText(f"❌ Erreur : {message}")
                                self.error_label.show()
                                self.send_code_btn.setEnabled(True)
                                self.send_code_btn.setText("Envoyer le code")
                        
                        QTimer.singleShot(0, update_ui)
                        
                    except Exception as e:
                        def show_error():
                            self.error_label.setText(f"❌ Erreur : {str(e)}")
                            self.error_label.show()
                            self.send_code_btn.setEnabled(True)
                            self.send_code_btn.setText("Envoyer le code")
                        
                        QTimer.singleShot(0, show_error)
                
                # Créer la tâche dans la boucle existante
                asyncio.create_task(send())
                
            except Exception as e:
                self.error_label.setText(f"❌ Erreur : {str(e)}")
                self.error_label.show()
                self.send_code_btn.setEnabled(True)
                self.send_code_btn.setText("Envoyer le code")
        
        # Utiliser QTimer pour éviter les conflits asyncio
        QTimer.singleShot(0, send_sync)
    
    def _verify_code(self):
        """Vérifie le code"""
        code = self.code_input.text().strip()
        password = self.password_input.text().strip() or None
        
        if not code:
            self.error_label.setText("⚠️ Veuillez entrer le code de vérification")
            self.error_label.show()
            return
        
        def verify_sync():
            try:
                # Afficher un message de chargement
                self.error_label.setText("🔄 Vérification en cours...")
                self.error_label.show()
                self.verify_btn.setEnabled(False)
                self.verify_btn.setText("🔄 Vérification...")
                
                # Utiliser la boucle d'événements existante
                import asyncio
                loop = asyncio.get_event_loop()
                
                async def verify():
                    try:
                        success, message = await self.telegram_manager.verify_account(
                            self.session_id, code, password
                        )
                        
                        # Utiliser QTimer pour les mises à jour UI (thread-safe)
                        def update_ui():
                            if success:
                                # Sauvegarder la session après connexion réussie
                                async def save_session():
                                    await self.telegram_manager.save_session_after_login(self.session_id)
                                
                                asyncio.create_task(save_session())
                                
                                QMessageBox.information(
                                    self,
                                    "Succès",
                                    "Compte ajouté avec succès !\n\nVotre session sera automatiquement restaurée au prochain démarrage.",
                                    QMessageBox.StandardButton.Ok
                                )
                                self.accept()
                            else:
                                self.error_label.setText(f"❌ {message}")
                                self.error_label.show()
                                self.verify_btn.setEnabled(True)
                                self.verify_btn.setText("✅ Vérifier")
                                
                                # Si 2FA requis, afficher le champ password
                                if "2FA" in message or "password" in message.lower():
                                    self.password_input.setFocus()
                        
                        QTimer.singleShot(0, update_ui)
                        
                    except Exception as e:
                        def show_error():
                            self.error_label.setText(f"❌ Erreur : {str(e)}")
                            self.error_label.show()
                            self.verify_btn.setEnabled(True)
                            self.verify_btn.setText("✅ Vérifier")
                        
                        QTimer.singleShot(0, show_error)
                
                # Créer la tâche dans la boucle existante
                asyncio.create_task(verify())
                
            except Exception as e:
                self.error_label.setText(f"❌ Erreur : {str(e)}")
                self.error_label.show()
                self.verify_btn.setEnabled(True)
                self.verify_btn.setText("✅ Vérifier")
        
        # Utiliser QTimer pour éviter les conflits asyncio
        QTimer.singleShot(0, verify_sync)
    
    def _force_resize(self):
        """Force le redimensionnement de la fenêtre"""
        # Forcer la mise à jour de la taille
        self.adjustSize()
        self.resize(550, 550)
        self.update()
    
    def _center_and_show(self):
        """Centre la fenêtre et s'assure qu'elle est visible"""
        # Centrer la fenêtre sur l'écran
        if self.parent():
            # Centrer par rapport à la fenêtre parent
            parent_geometry = self.parent().geometry()
            x = parent_geometry.x() + (parent_geometry.width() - 550) // 2
            y = parent_geometry.y() + (parent_geometry.height() - 550) // 2
            self.move(x, y)
        else:
            # Centrer sur l'écran
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - 550) // 2
            y = (screen.height() - 550) // 2
            self.move(x, y)
        
        # S'assurer que la fenêtre est visible
        self.show()
        self.raise_()
        self.activateWindow()


class ReconnectDialog(QDialog):
    """Dialogue pour reconnecter un compte"""
    
    def __init__(self, telegram_manager: TelegramManager, session_id: str, account_text: str, parent=None):
        super().__init__(parent)
        
        self.telegram_manager = telegram_manager
        self.session_id = session_id
        self.account_text = account_text
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        self.setWindowTitle("Reconnecter un Compte")
        self.setMinimumSize(450, 300)
        self.resize(450, 300)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Titre
        title = QLabel("🔄 Reconnecter un Compte")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Informations du compte
        info = QLabel(f"Compte : {self.account_text}")
        info.setStyleSheet("color: #666; font-size: 14px;")
        layout.addWidget(info)
        
        # Instructions
        instructions = QLabel(
            "Pour reconnecter ce compte :\n\n"
            "1. Un code de vérification sera envoyé automatiquement\n"
            "2. Entrez le code reçu sur Telegram\n"
            "3. Entrez votre mot de passe 2FA (si activé)\n\n"
            "Les autres comptes resteront connectés."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("background-color: #f0f8ff; padding: 15px; border-radius: 8px;")
        layout.addWidget(instructions)
        
        # Formulaire
        form_layout = QFormLayout()
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Code de vérification")
        self.code_input.setMinimumHeight(35)
        self.code_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        form_layout.addRow("Code de vérification :", self.code_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe 2FA (si activé)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setMinimumHeight(35)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                font-size: 14px;
                border: 2px solid #ddd;
                border-radius: 6px;
            }
            QLineEdit:focus {
                border: 2px solid #2196F3;
            }
        """)
        form_layout.addRow("Mot de passe 2FA :", self.password_input)
        
        layout.addLayout(form_layout)
        
        # Message d'erreur
        self.error_label = QLabel()
        self.error_label.setStyleSheet("""
            QLabel {
                background-color: #ffebee;
                border: 2px solid #f44336;
                border-radius: 8px;
                padding: 10px;
                color: #d32f2f;
                font-weight: bold;
            }
        """)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.reconnect_btn = QPushButton("🔄 Reconnecter")
        self.reconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.reconnect_btn.clicked.connect(self._reconnect)
        buttons_layout.addWidget(self.reconnect_btn)
        
        cancel_btn = QPushButton("Annuler")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        # Envoyer automatiquement le code de reconnexion
        QTimer.singleShot(500, self._send_reconnect_code)
    
    def _reconnect(self):
        """Tente de reconnecter le compte"""
        code = self.code_input.text().strip()
        password = self.password_input.text().strip() or None
        
        if not code:
            self.error_label.setText("⚠️ Veuillez entrer le code de vérification")
            self.error_label.show()
            return
        
        # Afficher un message de chargement
        self.error_label.setText("🔄 Reconnexion en cours...")
        self.error_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 2px solid #2196F3;
                border-radius: 8px;
                padding: 10px;
                color: #1976D2;
                font-weight: bold;
            }
        """)
        self.error_label.show()
        self.reconnect_btn.setEnabled(False)
        self.reconnect_btn.setText("🔄 Reconnexion...")
        
        def reconnect_sync():
            try:
                # Utiliser la boucle d'événements existante
                import asyncio
                loop = asyncio.get_event_loop()
                
                async def reconnect():
                    try:
                        # Tenter de reconnecter avec le code
                        success, message = await self.telegram_manager.verify_account(
                            self.session_id, code, password
                        )
                        
                        # Utiliser QTimer pour les mises à jour UI (thread-safe)
                        def update_ui():
                            if success:
                                QMessageBox.information(
                                    self,
                                    "✅ Succès",
                                    f"Compte reconnecté avec succès !\n\n{message}"
                                )
                                self.accept()
                            else:
                                self.error_label.setText(f"❌ {message}")
                                self.error_label.setStyleSheet("""
                                    QLabel {
                                        background-color: #ffebee;
                                        border: 2px solid #f44336;
                                        border-radius: 8px;
                                        padding: 10px;
                                        color: #d32f2f;
                                        font-weight: bold;
                                    }
                                """)
                                self.reconnect_btn.setEnabled(True)
                                self.reconnect_btn.setText("🔄 Reconnecter")
                                
                                # Si 2FA requis, afficher le champ password
                                if "2FA" in message or "password" in message.lower():
                                    self.password_input.setFocus()
                        
                        QTimer.singleShot(0, update_ui)
                        
                    except Exception as e:
                        def show_error():
                            self.error_label.setText(f"❌ Erreur : {str(e)}")
                            self.error_label.setStyleSheet("""
                                QLabel {
                                    background-color: #ffebee;
                                    border: 2px solid #f44336;
                                    border-radius: 8px;
                                    padding: 10px;
                                    color: #d32f2f;
                                    font-weight: bold;
                                }
                            """)
                            self.reconnect_btn.setEnabled(True)
                            self.reconnect_btn.setText("🔄 Reconnecter")
                        
                        QTimer.singleShot(0, show_error)
                
                # Créer la tâche dans la boucle existante
                asyncio.create_task(reconnect())
                
            except Exception as e:
                self.error_label.setText(f"❌ Erreur : {str(e)}")
                self.error_label.setStyleSheet("""
                    QLabel {
                        background-color: #ffebee;
                        border: 2px solid #f44336;
                        border-radius: 8px;
                        padding: 10px;
                        color: #d32f2f;
                        font-weight: bold;
                    }
                """)
                self.reconnect_btn.setEnabled(True)
                self.reconnect_btn.setText("🔄 Reconnecter")
        
        # Utiliser QTimer pour éviter les conflits asyncio
        QTimer.singleShot(0, reconnect_sync)
    
    def _send_reconnect_code(self):
        """Envoie automatiquement le code de reconnexion"""
        # Afficher un message de chargement
        self.error_label.setText("📤 Envoi du code de reconnexion...")
        self.error_label.setStyleSheet("""
            QLabel {
                background-color: #e3f2fd;
                border: 2px solid #2196F3;
                border-radius: 8px;
                padding: 10px;
                color: #1976D2;
                font-weight: bold;
            }
        """)
        self.error_label.show()
        
        def send_code_sync():
            try:
                # Utiliser la boucle d'événements existante
                import asyncio
                loop = asyncio.get_event_loop()
                
                async def send_code():
                    try:
                        # Envoyer le code de reconnexion
                        success, message, _ = await self.telegram_manager.add_account(
                            self.telegram_manager.accounts[self.session_id].phone,
                            self.telegram_manager.accounts[self.session_id].account_name
                        )
                        
                        # Utiliser QTimer pour les mises à jour UI (thread-safe)
                        def update_ui():
                            if success:
                                self.error_label.setText("✅ Code envoyé ! Entrez le code reçu sur Telegram")
                                self.error_label.setStyleSheet("""
                                    QLabel {
                                        background-color: #e8f5e8;
                                        border: 2px solid #4CAF50;
                                        border-radius: 8px;
                                        padding: 10px;
                                        color: #2e7d32;
                                        font-weight: bold;
                                    }
                                """)
                                self.code_input.setFocus()
                            else:
                                self.error_label.setText(f"❌ Erreur envoi code : {message}")
                                self.error_label.setStyleSheet("""
                                    QLabel {
                                        background-color: #ffebee;
                                        border: 2px solid #f44336;
                                        border-radius: 8px;
                                        padding: 10px;
                                        color: #d32f2f;
                                        font-weight: bold;
                                    }
                                """)
                        
                        QTimer.singleShot(0, update_ui)
                        
                    except Exception as e:
                        def show_error():
                            self.error_label.setText(f"❌ Erreur envoi code : {str(e)}")
                            self.error_label.setStyleSheet("""
                                QLabel {
                                    background-color: #ffebee;
                                    border: 2px solid #f44336;
                                    border-radius: 8px;
                                    padding: 10px;
                                    color: #d32f2f;
                                    font-weight: bold;
                                }
                            """)
                        
                        QTimer.singleShot(0, show_error)
                
                # Créer la tâche dans la boucle existante
                asyncio.create_task(send_code())
                
            except Exception as e:
                self.error_label.setText(f"❌ Erreur envoi code : {str(e)}")
                self.error_label.setStyleSheet("""
                    QLabel {
                        background-color: #ffebee;
                        border: 2px solid #f44336;
                        border-radius: 8px;
                        padding: 10px;
                        color: #d32f2f;
                        font-weight: bold;
                    }
                """)
        
        # Utiliser QTimer pour éviter les conflits asyncio
        QTimer.singleShot(0, send_code_sync)


class AccountManagerWidget(QWidget):
    """Widget de gestion des comptes"""
    
    def __init__(self, telegram_manager: TelegramManager):
        super().__init__()
        
        self.telegram_manager = telegram_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # En-tête
        header_layout = QHBoxLayout()
        
        header_layout.addStretch()
        
        # Bouton ajout
        add_btn = QPushButton("➕ Nouveau Compte")
        add_btn.clicked.connect(self._add_account)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Liste des comptes
        self.accounts_list = QListWidget()
        self.accounts_list.setAlternatingRowColors(True)
        layout.addWidget(self.accounts_list)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.reconnect_btn = QPushButton("🔄 Se reconnecter")
        self.reconnect_btn.setProperty("class", "primary")
        self.reconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.reconnect_btn.clicked.connect(self._reconnect_account)
        self.reconnect_btn.setEnabled(False)
        actions_layout.addWidget(self.reconnect_btn)
        
        self.remove_btn = QPushButton("🗑️ Supprimer")
        self.remove_btn.setProperty("class", "danger")
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        self.remove_btn.clicked.connect(self._remove_account)
        self.remove_btn.setEnabled(False)
        actions_layout.addWidget(self.remove_btn)
        
        layout.addLayout(actions_layout)
        
        # Connexions
        self.accounts_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.accounts_list.itemClicked.connect(self._on_item_clicked)
        
        # Charger les comptes
        self.refresh_accounts()
    
    def refresh_accounts(self):
        """Rafraîchit la liste des comptes (optimisé)"""
        # Sauvegarder la sélection actuelle
        current_selection = None
        if self.accounts_list.currentItem():
            current_selection = self.accounts_list.currentItem().data(Qt.ItemDataRole.UserRole)
        
        # Vider la liste
        self.accounts_list.clear()
        
        # Afficher un indicateur de chargement
        loading_item = QListWidgetItem("🔄 Chargement des comptes...")
        loading_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.accounts_list.addItem(loading_item)
        
        # Charger les comptes en arrière-plan avec restauration de sélection
        QTimer.singleShot(0, lambda: self._load_accounts_async(current_selection))
    
    def _load_accounts_async(self, previous_selection=None):
        """Charge les comptes de manière asynchrone avec restauration de sélection"""
        try:
            accounts = self.telegram_manager.list_accounts()
            
            # Vider et remplir
            self.accounts_list.clear()
            
            if not accounts:
                item = QListWidgetItem("Aucun compte configuré")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.accounts_list.addItem(item)
                return
            
            selected_item = None
            for account in accounts:
                status = "🟢 Connecté" if account["is_connected"] else "🔴 Déconnecté"
                text = f"{account['account_name']} ({account['phone']}) - {status}"
                
                item = QListWidgetItem(text)
                item.setData(Qt.ItemDataRole.UserRole, account["session_id"])
                self.accounts_list.addItem(item)
                
                # Restaurer la sélection si c'est le même compte
                if previous_selection and account["session_id"] == previous_selection:
                    selected_item = item
            
            # Restaurer la sélection
            if selected_item:
                self.accounts_list.setCurrentItem(selected_item)
                self.remove_btn.setEnabled(True)
                
        except Exception as e:
            self.accounts_list.clear()
            error_item = QListWidgetItem(f"❌ Erreur: {str(e)[:50]}")
            error_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.accounts_list.addItem(error_item)
    
    def _add_account(self):
        """Ouvre le dialogue d'ajout de compte"""
        dialog = AddAccountDialog(self.telegram_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_accounts()
    
    def _remove_account(self):
        """Supprime le compte sélectionné"""
        selected = self.accounts_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Aucun compte sélectionné")
            return
        
        # Récupérer les infos du compte
        session_id = selected[0].data(Qt.ItemDataRole.UserRole)
        account_text = selected[0].text()
        
        reply = QMessageBox.question(
            self,
            "🗑️ Supprimer le compte",
            f"Êtes-vous sûr de vouloir supprimer ce compte ?\n\n"
            f"📱 {account_text}\n\n"
            f"⚠️ Cette action est irréversible et supprimera :\n"
            f"• La session Telegram\n"
            f"• L'historique des messages\n"
            f"• Toutes les données du compte",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Désactiver le bouton pendant la suppression
            self.remove_btn.setEnabled(False)
            self.remove_btn.setText("🔄 Suppression...")
            
            async def remove():
                try:
                    success = await self.telegram_manager.remove_account(session_id)
                    
                    # Utiliser QTimer pour les messages UI (éviter conflits asyncio)
                    def show_result():
                        if success:
                            QMessageBox.information(
                                self,
                                "✅ Succès",
                                "Compte supprimé avec succès !"
                            )
                        else:
                            QMessageBox.warning(
                                self,
                                "❌ Erreur",
                                "Échec de la suppression du compte"
                            )
                        # Réactiver le bouton
                        self.remove_btn.setText("🗑️ Supprimer")
                        self.remove_btn.setEnabled(True)
                        self.refresh_accounts()
                    
                    QTimer.singleShot(100, show_result)
                    
                except Exception as e:
                    def show_error():
                        QMessageBox.critical(
                            self,
                            "❌ Erreur",
                            f"Erreur lors de la suppression :\n{str(e)}"
                        )
                        # Réactiver le bouton
                        self.remove_btn.setText("🗑️ Supprimer")
                        self.remove_btn.setEnabled(True)
                    
                    QTimer.singleShot(100, show_error)
            
            # Utiliser QTimer pour éviter les conflits asyncio
            QTimer.singleShot(0, lambda: asyncio.create_task(remove()))
    
    def _reconnect_account(self):
        """Reconnecte le compte sélectionné"""
        selected = self.accounts_list.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Attention", "Aucun compte sélectionné")
            return
        
        # Récupérer les infos du compte
        session_id = selected[0].data(Qt.ItemDataRole.UserRole)
        account_text = selected[0].text()
        
        # Ouvrir le dialogue de reconnexion
        dialog = ReconnectDialog(self.telegram_manager, session_id, account_text, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_accounts()
            # Rafraîchir aussi les autres widgets qui utilisent les comptes
            self._refresh_all_widgets()
    
    def _on_selection_changed(self):
        """Gère le changement de sélection"""
        has_selection = len(self.accounts_list.selectedItems()) > 0
        
        # Activer/désactiver les boutons
        self.remove_btn.setEnabled(has_selection)
        
        # Activer le bouton reconnecter seulement si le compte est déconnecté
        if has_selection:
            selected_item = self.accounts_list.selectedItems()[0]
            session_id = selected_item.data(Qt.ItemDataRole.UserRole)
            account = self.telegram_manager.accounts.get(session_id)
            
            if account and not account.is_connected:
                self.reconnect_btn.setEnabled(True)
                self.reconnect_btn.setText("🔄 Se reconnecter")
            else:
                self.reconnect_btn.setEnabled(False)
                self.reconnect_btn.setText("✅ Connecté")
        else:
            self.reconnect_btn.setEnabled(False)
            self.reconnect_btn.setText("🔄 Se reconnecter")
    
    def _on_item_clicked(self, item):
        """Gère le clic sur un item"""
        # S'assurer que l'item est sélectionné
        if item:
            self.accounts_list.setCurrentItem(item)
            self.remove_btn.setEnabled(True)
    
    def _refresh_all_widgets(self):
        """Rafraîchit tous les widgets qui utilisent les comptes"""
        try:
            # Trouver la fenêtre principale
            main_window = self.window()
            if hasattr(main_window, 'scheduled_messages_widget'):
                main_window.scheduled_messages_widget.refresh_accounts()
            if hasattr(main_window, 'message_wizard_widget'):
                main_window.message_wizard_widget.refresh_accounts()
        except Exception as e:
            print(f"Erreur rafraîchissement widgets: {e}")

