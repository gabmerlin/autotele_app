"""
Widget d'édition et planification de messages
"""
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QComboBox, QListWidget, QListWidgetItem, QDateTimeEdit,
    QFileDialog, QMessageBox, QGroupBox, QFormLayout, QCheckBox,
    QProgressBar
)
from PyQt6.QtCore import Qt, QDateTime
from PyQt6.QtGui import QFont

from core.telegram_manager import TelegramManager
from core.scheduler import MessageScheduler
from ui.styles import FONT_FAMILY


class MessageEditorWidget(QWidget):
    """Widget pour créer et planifier des messages"""
    
    def __init__(self, telegram_manager: TelegramManager, scheduler: MessageScheduler):
        super().__init__()
        
        self.telegram_manager = telegram_manager
        self.scheduler = scheduler
        self.selected_file = None
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Titre
        title = QLabel("Créer un Message Planifié")
        title.setProperty("class", "subtitle")
        title.setFont(QFont(FONT_FAMILY, 16, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Sélection du compte
        account_group = QGroupBox("1️⃣ Sélectionner le Compte")
        account_layout = QVBoxLayout(account_group)
        
        self.account_combo = QComboBox()
        self.account_combo.currentIndexChanged.connect(self._on_account_changed)
        account_layout.addWidget(self.account_combo)
        
        layout.addWidget(account_group)
        
        # Sélection des groupes
        groups_group = QGroupBox("2️⃣ Sélectionner les Groupes/Canaux")
        groups_layout = QVBoxLayout(groups_group)
        
        groups_header = QHBoxLayout()
        groups_info = QLabel("Cochez les groupes où envoyer le message")
        groups_info.setProperty("class", "hint")
        groups_header.addWidget(groups_info)
        
        groups_header.addStretch()
        
        select_all_btn = QPushButton("Tout sélectionner")
        select_all_btn.setProperty("class", "secondary")
        select_all_btn.clicked.connect(self._select_all_groups)
        groups_header.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Tout désélectionner")
        deselect_all_btn.setProperty("class", "secondary")
        deselect_all_btn.clicked.connect(self._deselect_all_groups)
        groups_header.addWidget(deselect_all_btn)
        
        groups_layout.addLayout(groups_header)
        
        self.groups_list = QListWidget()
        self.groups_list.setMaximumHeight(200)
        groups_layout.addWidget(self.groups_list)
        
        self.groups_count_label = QLabel("0 groupe(s) sélectionné(s)")
        self.groups_count_label.setProperty("class", "hint")
        groups_layout.addWidget(self.groups_count_label)
        
        layout.addWidget(groups_group)
        
        # Contenu du message
        message_group = QGroupBox("3️⃣ Contenu du Message")
        message_layout = QVBoxLayout(message_group)
        
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText(
            "Rédigez votre message ici...\n\n"
            "Exemple :\n"
            "🔔 Nouvelle Offre d'Emploi\n\n"
            "Nous recherchons un Développeur Python senior.\n\n"
            "📍 Localisation : Paris\n"
            "💰 Salaire : 50-60K€\n\n"
            "Postulez via : recrutement@entreprise.com"
        )
        self.message_edit.setMinimumHeight(150)
        self.message_edit.textChanged.connect(self._update_char_count)
        message_layout.addWidget(self.message_edit)
        
        self.char_count_label = QLabel("0 caractères")
        self.char_count_label.setProperty("class", "hint")
        message_layout.addWidget(self.char_count_label)
        
        # Fichier joint
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("Aucun fichier sélectionné")
        self.file_label.setProperty("class", "hint")
        file_layout.addWidget(self.file_label)
        
        file_layout.addStretch()
        
        select_file_btn = QPushButton("📎 Joindre un fichier")
        select_file_btn.setProperty("class", "secondary")
        select_file_btn.clicked.connect(self._select_file)
        file_layout.addWidget(select_file_btn)
        
        clear_file_btn = QPushButton("❌")
        clear_file_btn.setProperty("class", "secondary")
        clear_file_btn.clicked.connect(self._clear_file)
        file_layout.addWidget(clear_file_btn)
        
        message_layout.addLayout(file_layout)
        
        layout.addWidget(message_group)
        
        # Planification
        schedule_group = QGroupBox("4️⃣ Planifier l'Envoi")
        schedule_layout = QFormLayout(schedule_group)
        
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))  # +1h par défaut
        self.datetime_edit.setMinimumDateTime(QDateTime.currentDateTime())
        schedule_layout.addRow("Date et heure :", self.datetime_edit)
        
        # Boutons rapides
        quick_layout = QHBoxLayout()
        
        in_1h_btn = QPushButton("+1h")
        in_1h_btn.setProperty("class", "secondary")
        in_1h_btn.clicked.connect(lambda: self._set_time_offset(1))
        quick_layout.addWidget(in_1h_btn)
        
        in_3h_btn = QPushButton("+3h")
        in_3h_btn.setProperty("class", "secondary")
        in_3h_btn.clicked.connect(lambda: self._set_time_offset(3))
        quick_layout.addWidget(in_3h_btn)
        
        tomorrow_9am_btn = QPushButton("Demain 9h")
        tomorrow_9am_btn.setProperty("class", "secondary")
        tomorrow_9am_btn.clicked.connect(self._set_tomorrow_9am)
        quick_layout.addWidget(tomorrow_9am_btn)
        
        quick_layout.addStretch()
        
        schedule_layout.addRow("Raccourcis :", quick_layout)
        
        layout.addWidget(schedule_group)
        
        # Message d'erreur
        self.error_label = QLabel()
        self.error_label.setProperty("class", "error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        clear_btn = QPushButton("🗑️ Réinitialiser")
        clear_btn.setProperty("class", "secondary")
        clear_btn.clicked.connect(self._clear_form)
        actions_layout.addWidget(clear_btn)
        
        self.schedule_btn = QPushButton("📅 Planifier le Message")
        self.schedule_btn.clicked.connect(self._schedule_message)
        actions_layout.addWidget(self.schedule_btn)
        
        layout.addLayout(actions_layout)
        
        # Espaceur
        layout.addStretch()
        
        # Charger les comptes
        self.refresh_accounts()
    
    def refresh_accounts(self):
        """Rafraîchit la liste des comptes"""
        self.account_combo.clear()
        
        accounts = self.telegram_manager.list_accounts()
        connected_accounts = [a for a in accounts if a["is_connected"]]
        
        if not connected_accounts:
            self.account_combo.addItem("Aucun compte connecté")
            self.account_combo.setEnabled(False)
            self.schedule_btn.setEnabled(False)
            return
        
        self.account_combo.setEnabled(True)
        self.schedule_btn.setEnabled(True)
        
        for account in connected_accounts:
            self.account_combo.addItem(
                f"{account['account_name']} ({account['phone']})",
                account["session_id"]
            )
    
    def _on_account_changed(self, index):
        """Gère le changement de compte"""
        if index < 0 or not self.account_combo.isEnabled():
            return
        
        session_id = self.account_combo.itemData(index)
        if not session_id:
            return
        
        # Charger les groupes
        account = self.telegram_manager.get_account(session_id)
        if account:
            async def load_dialogs():
                dialogs = await account.get_dialogs()
                
                self.groups_list.clear()
                
                for dialog in dialogs:
                    if dialog["can_send"]:
                        item = QListWidgetItem(f"{'📢' if dialog['type'] == 'channel' else '👥'} {dialog['title']}")
                        item.setData(Qt.ItemDataRole.UserRole, dialog)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Unchecked)
                        self.groups_list.addItem(item)
                
                if self.groups_list.count() == 0:
                    item = QListWidgetItem("Aucun groupe disponible")
                    item.setFlags(Qt.ItemFlag.NoItemFlags)
                    self.groups_list.addItem(item)
                
                self._update_groups_count()
            
            asyncio.create_task(load_dialogs())
    
    def _select_all_groups(self):
        """Sélectionne tous les groupes"""
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Checked)
        self._update_groups_count()
    
    def _deselect_all_groups(self):
        """Désélectionne tous les groupes"""
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(Qt.CheckState.Unchecked)
        self._update_groups_count()
    
    def _update_groups_count(self):
        """Met à jour le compteur de groupes"""
        count = sum(
            1 for i in range(self.groups_list.count())
            if self.groups_list.item(i).checkState() == Qt.CheckState.Checked
        )
        self.groups_count_label.setText(f"{count} groupe(s) sélectionné(s)")
    
    def _update_char_count(self):
        """Met à jour le compteur de caractères"""
        text = self.message_edit.toPlainText()
        count = len(text)
        self.char_count_label.setText(f"{count} caractères")
    
    def _select_file(self):
        """Sélectionne un fichier à joindre"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner un fichier",
            "",
            "Tous les fichiers (*.*)"
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(f"📎 {Path(file_path).name}")
    
    def _clear_file(self):
        """Supprime le fichier sélectionné"""
        self.selected_file = None
        self.file_label.setText("Aucun fichier sélectionné")
    
    def _set_time_offset(self, hours: int):
        """Définit l'heure à +X heures"""
        new_time = QDateTime.currentDateTime().addSecs(hours * 3600)
        self.datetime_edit.setDateTime(new_time)
    
    def _set_tomorrow_9am(self):
        """Définit l'heure à demain 9h"""
        tomorrow = QDateTime.currentDateTime().addDays(1)
        tomorrow.setTime(tomorrow.time().fromString("09:00:00", "hh:mm:ss"))
        self.datetime_edit.setDateTime(tomorrow)
    
    def _schedule_message(self):
        """Planifie le message"""
        # Validation
        if self.account_combo.currentIndex() < 0:
            self._show_error("Veuillez sélectionner un compte")
            return
        
        selected_groups = []
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_groups.append(item.data(Qt.ItemDataRole.UserRole))
        
        if not selected_groups:
            self._show_error("Veuillez sélectionner au moins un groupe")
            return
        
        message = self.message_edit.toPlainText().strip()
        if not message:
            self._show_error("Veuillez rédiger un message")
            return
        
        schedule_time = self.datetime_edit.dateTime().toPyDateTime()
        if schedule_time <= datetime.now():
            self._show_error("L'heure de planification doit être dans le futur")
            return
        
        # Confirmer
        reply = QMessageBox.question(
            self,
            "Confirmer la planification",
            f"Planifier ce message dans {len(selected_groups)} groupe(s) ?\n\n"
            f"Heure d'envoi : {schedule_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            f"Le message apparaîtra comme planifié dans votre Telegram.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.No:
            return
        
        # Créer la tâche
        session_id = self.account_combo.currentData()
        account_name = self.account_combo.currentText()
        
        try:
            task_id = self.scheduler.create_task(
                session_id,
                account_name,
                selected_groups,
                message,
                schedule_time,
                self.selected_file
            )
            
            QMessageBox.information(
                self,
                "Succès",
                f"Message planifié avec succès !\n\n"
                f"Tâche ID : {task_id}\n"
                f"Groupes : {len(selected_groups)}\n"
                f"Heure : {schedule_time.strftime('%d/%m/%Y à %H:%M')}",
                QMessageBox.StandardButton.Ok
            )
            
            self._clear_form()
            
        except Exception as e:
            self._show_error(f"Erreur lors de la planification : {e}")
    
    def _show_error(self, message: str):
        """Affiche un message d'erreur"""
        self.error_label.setText(f"❌ {message}")
        self.error_label.show()
    
    def _clear_form(self):
        """Réinitialise le formulaire"""
        self.message_edit.clear()
        self._clear_file()
        self._deselect_all_groups()
        self.datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        self.error_label.hide()

