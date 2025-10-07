"""
Widget de gestion des comptes Telegram
"""
import asyncio
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QDialog, QLineEdit, QMessageBox,
    QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.telegram_manager import TelegramManager
from ui.styles import FONT_FAMILY


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
        self.setMinimumSize(500, 400)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Titre
        title = QLabel("Connecter un Compte Telegram")
        title.setProperty("class", "subtitle")
        title.setFont(QFont(FONT_FAMILY, 14, QFont.Weight.Bold))
        layout.addWidget(title)
        
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
        
        # Formulaire simplifié
        form_group = QGroupBox("Informations du Compte")
        form_layout = QFormLayout(form_group)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Mon compte recrutement")
        form_layout.addRow("Nom du compte :", self.name_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+33612345678")
        form_layout.addRow("Numéro de téléphone :", self.phone_input)
        
        layout.addWidget(form_group)
        
        # Zone de vérification (cachée au départ)
        self.verification_group = QGroupBox("Vérification")
        verification_layout = QFormLayout(self.verification_group)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("12345")
        verification_layout.addRow("Code de vérification :", self.code_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe 2FA (si activé)")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        verification_layout.addRow("Mot de passe 2FA :", self.password_input)
        
        self.verification_group.hide()
        layout.addWidget(self.verification_group)
        
        # Message d'erreur
        self.error_label = QLabel()
        self.error_label.setProperty("class", "error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        self.send_code_btn = QPushButton("Envoyer le code")
        self.send_code_btn.clicked.connect(self._send_code)
        buttons_layout.addWidget(self.send_code_btn)
        
        self.verify_btn = QPushButton("Vérifier")
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
        
        # Envoyer le code (utilise les credentials par défaut)
        async def send():
            success, message, session_id = await self.telegram_manager.add_account(
                phone, name
            )
            
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
        
        asyncio.create_task(send())
    
    def _verify_code(self):
        """Vérifie le code"""
        code = self.code_input.text().strip()
        password = self.password_input.text().strip() or None
        
        if not code:
            self.error_label.setText("⚠️ Veuillez entrer le code de vérification")
            self.error_label.show()
            return
        
        async def verify():
            success, message = await self.telegram_manager.verify_account(
                self.session_id, code, password
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Succès",
                    "Compte ajouté avec succès !",
                    QMessageBox.StandardButton.Ok
                )
                self.accept()
            else:
                self.error_label.setText(f"❌ {message}")
                self.error_label.show()
                
                # Si 2FA requis, afficher le champ password
                if "2FA" in message or "password" in message.lower():
                    self.password_input.setFocus()
        
        asyncio.create_task(verify())


class AccountManagerWidget(QWidget):
    """Widget de gestion des comptes"""
    
    def __init__(self, telegram_manager: TelegramManager):
        super().__init__()
        
        self.telegram_manager = telegram_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # En-tête
        header_layout = QHBoxLayout()
        
        title = QLabel("Gestion des Comptes Telegram")
        title.setProperty("class", "subtitle")
        title.setFont(QFont(FONT_FAMILY, 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        add_btn = QPushButton("➕ Ajouter un compte")
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
        
        self.remove_btn = QPushButton("🗑️ Supprimer")
        self.remove_btn.setProperty("class", "danger")
        self.remove_btn.clicked.connect(self._remove_account)
        self.remove_btn.setEnabled(False)
        actions_layout.addWidget(self.remove_btn)
        
        layout.addLayout(actions_layout)
        
        # Connexions
        self.accounts_list.itemSelectionChanged.connect(self._on_selection_changed)
        
        # Charger les comptes
        self.refresh_accounts()
    
    def refresh_accounts(self):
        """Rafraîchit la liste des comptes"""
        self.accounts_list.clear()
        
        accounts = self.telegram_manager.list_accounts()
        
        if not accounts:
            item = QListWidgetItem("Aucun compte configuré")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.accounts_list.addItem(item)
            return
        
        for account in accounts:
            status = "🟢 Connecté" if account["is_connected"] else "🔴 Déconnecté"
            text = f"{account['account_name']} ({account['phone']}) - {status}"
            
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, account["session_id"])
            self.accounts_list.addItem(item)
    
    def _add_account(self):
        """Ouvre le dialogue d'ajout de compte"""
        dialog = AddAccountDialog(self.telegram_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.refresh_accounts()
    
    def _remove_account(self):
        """Supprime le compte sélectionné"""
        selected = self.accounts_list.selectedItems()
        if not selected:
            return
        
        reply = QMessageBox.question(
            self,
            "Supprimer le compte",
            "Êtes-vous sûr de vouloir supprimer ce compte ?\n\n"
            "Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            session_id = selected[0].data(Qt.ItemDataRole.UserRole)
            
            async def remove():
                await self.telegram_manager.remove_account(session_id)
                self.refresh_accounts()
            
            asyncio.create_task(remove())
    
    def _on_selection_changed(self):
        """Gère le changement de sélection"""
        has_selection = len(self.accounts_list.selectedItems()) > 0
        self.remove_btn.setEnabled(has_selection)

