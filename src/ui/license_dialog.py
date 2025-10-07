"""
Dialogue de gestion de licence
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import webbrowser

from core.license_manager import LicenseManager
from ui.styles import FONT_FAMILY


class LicenseDialog(QDialog):
    """Dialogue pour activer et gérer la licence"""
    
    def __init__(self, license_manager: LicenseManager, parent=None):
        super().__init__(parent)
        
        self.license_manager = license_manager
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        self.setWindowTitle("Gestion de la Licence")
        self.setMinimumSize(600, 500)
        self.setModal(True)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Titre
        title = QLabel("Gestion de la Licence AutoTele")
        title.setProperty("class", "title")
        title.setFont(QFont(FONT_FAMILY, 18, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Statut actuel
        status_group = self._create_status_group()
        layout.addWidget(status_group)
        
        # Activation de licence
        if not self.license_manager.is_license_valid() or self.license_manager.license_data.get("status") == "trial":
            activation_group = self._create_activation_group()
            layout.addWidget(activation_group)
        
        # Informations
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setPlainText(
            "ℹ️ À propos de la licence :\n\n"
            "• Période d'essai gratuite de 7 jours\n"
            "• Abonnement mensuel : 29.99 EUR\n"
            "• Paiement sécurisé via BTCPay Server\n"
            "• Une licence = une machine\n"
            "• Renouvellement automatique\n\n"
            "Pour toute question, contactez le support."
        )
        layout.addWidget(info_text)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        if self.license_manager.is_license_valid():
            ok_btn = QPushButton("Fermer")
            ok_btn.clicked.connect(self.accept)
            buttons_layout.addWidget(ok_btn)
        else:
            cancel_btn = QPushButton("Quitter l'application")
            cancel_btn.setProperty("class", "danger")
            cancel_btn.clicked.connect(self.reject)
            buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_status_group(self) -> QGroupBox:
        """Crée le groupe d'affichage du statut"""
        group = QGroupBox("Statut de la Licence")
        layout = QVBoxLayout(group)
        
        status = self.license_manager.get_license_status()
        
        if status["is_trial"]:
            status_label = QLabel(
                f"📋 Statut : Période d'essai\n"
                f"⏱️ Jours restants : {status['trial_days_left']}\n"
                f"📅 Fin de l'essai : {status['trial_end_date']}"
            )
            status_label.setStyleSheet("font-size: 11pt; line-height: 1.6;")
        elif status["is_valid"]:
            expiry_info = ""
            if "expiry_date" in status:
                expiry_info = (
                    f"\n📅 Date d'expiration : {status['expiry_date']}\n"
                    f"⏱️ Jours restants : {status['expiry_days_left']}"
                )
            
            status_label = QLabel(
                f"✅ Statut : Licence active{expiry_info}"
            )
            status_label.setStyleSheet("font-size: 11pt; color: #34c759; line-height: 1.6;")
        else:
            status_label = QLabel(
                "❌ Statut : Aucune licence valide\n\n"
                "Activez une licence pour utiliser AutoTele."
            )
            status_label.setStyleSheet("font-size: 11pt; color: #ff3b30; line-height: 1.6;")
        
        layout.addWidget(status_label)
        
        return group
    
    def _create_activation_group(self) -> QGroupBox:
        """Crée le groupe d'activation de licence"""
        group = QGroupBox("Activer une Licence")
        layout = QVBoxLayout(group)
        
        # Bouton pour créer une facture
        purchase_btn = QPushButton("🛒 Acheter un Abonnement (29.99 EUR/mois)")
        purchase_btn.clicked.connect(self._create_invoice)
        layout.addWidget(purchase_btn)
        
        # Séparateur
        separator = QLabel("ou")
        separator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        separator.setStyleSheet("margin: 10px 0; color: #86868b;")
        layout.addWidget(separator)
        
        # Activation manuelle
        manual_label = QLabel("Entrez votre clé de licence :")
        layout.addWidget(manual_label)
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Collez votre clé de licence ici...")
        layout.addWidget(self.license_input)
        
        activate_btn = QPushButton("Activer")
        activate_btn.clicked.connect(self._activate_license)
        layout.addWidget(activate_btn)
        
        return group
    
    def _create_invoice(self):
        """Crée une facture BTCPay"""
        success, invoice_url, order_id = self.license_manager.create_payment_invoice()
        
        if success:
            msg = QMessageBox(self)
            msg.setWindowTitle("Paiement")
            msg.setText(
                f"Facture créée avec succès !\n\n"
                f"Votre clé de licence (à conserver) :\n{order_id}\n\n"
                f"La page de paiement va s'ouvrir dans votre navigateur.\n"
                f"Après le paiement, revenez ici et entrez votre clé de licence pour activer l'application."
            )
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            
            # Copier la clé dans le champ
            self.license_input.setText(order_id)
            
            msg.exec()
            
            # Ouvrir l'URL dans le navigateur
            if invoice_url:
                webbrowser.open(invoice_url)
        else:
            QMessageBox.warning(
                self,
                "Erreur",
                "Impossible de créer la facture.\n\n"
                "Vérifiez votre connexion Internet et la configuration BTCPay.",
                QMessageBox.StandardButton.Ok
            )
    
    def _activate_license(self):
        """Active la licence"""
        license_key = self.license_input.text().strip()
        
        if not license_key:
            QMessageBox.warning(
                self,
                "Erreur",
                "Veuillez entrer une clé de licence.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        success, message = self.license_manager.activate_license(license_key)
        
        if success:
            QMessageBox.information(
                self,
                "Succès",
                "Licence activée avec succès !\n\nVous pouvez maintenant utiliser AutoTele.",
                QMessageBox.StandardButton.Ok
            )
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Erreur d'activation",
                f"Impossible d'activer la licence :\n\n{message}\n\n"
                "Vérifiez que :\n"
                "• La clé de licence est correcte\n"
                "• Le paiement a été confirmé\n"
                "• Votre connexion Internet fonctionne",
                QMessageBox.StandardButton.Ok
            )

