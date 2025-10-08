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
    QProgressBar, QScrollArea
)
from PyQt6.QtCore import Qt, QDateTime, QTime
from PyQt6.QtGui import QFont

from core.telegram_manager import TelegramManager
from core.scheduler import MessageScheduler
from ui.modern_styles import get_modern_style, get_colors
from ui.multi_schedule_dialog import MultiScheduleDialog
from utils.logger import get_logger


class MessageEditorWidget(QWidget):
    """Widget pour créer et planifier des messages"""
    
    def __init__(self, telegram_manager: TelegramManager, scheduler: MessageScheduler):
        super().__init__()
        
        self.telegram_manager = telegram_manager
        self.scheduler = scheduler
        self.selected_file = None
        self._loading_groups = False  # Flag pour éviter les rechargements intempestifs
        self._current_account = None  # Compte actuellement sélectionné
        self.logger = get_logger()
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Sélection du compte (sans GroupBox)
        account_label = QLabel("🔹 Compte:")
        account_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        layout.addWidget(account_label)
        
        self.account_combo = QComboBox()
        self.account_combo.currentIndexChanged.connect(self._on_account_changed)
        layout.addWidget(self.account_combo)
        
        # Sélection des groupes (sans GroupBox)
        groups_header = QHBoxLayout()
        
        groups_label = QLabel("🔹 Groupes:")
        groups_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        groups_header.addWidget(groups_label)
        
        reload_btn = QPushButton("🔄")
        reload_btn.setMaximumWidth(30)
        reload_btn.setToolTip("Recharger")
        reload_btn.clicked.connect(self._reload_groups)
        groups_header.addWidget(reload_btn)
        
        select_all_btn = QPushButton("✓")
        select_all_btn.setMaximumWidth(30)
        select_all_btn.setToolTip("Tout sélectionner")
        select_all_btn.clicked.connect(self._select_all_groups)
        groups_header.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("✗")
        deselect_all_btn.setMaximumWidth(30)
        deselect_all_btn.setToolTip("Tout désélectionner")
        deselect_all_btn.clicked.connect(self._deselect_all_groups)
        groups_header.addWidget(deselect_all_btn)
        
        groups_header.addStretch()
        
        self.groups_count_label = QLabel("0")
        self.groups_count_label.setStyleSheet("color: #7F8C8D; font-size: 8pt;")
        groups_header.addWidget(self.groups_count_label)
        
        layout.addLayout(groups_header)
        
        self.groups_list = QListWidget()
        self.groups_list.setFixedHeight(100)
        self.groups_list.itemChanged.connect(self._update_groups_count)
        layout.addWidget(self.groups_list)
        
        # Message (sans GroupBox)
        msg_header = QHBoxLayout()
        msg_label = QLabel("🔹 Message:")
        msg_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        msg_header.addWidget(msg_label)
        
        msg_header.addStretch()
        
        self.file_label = QLabel("📎 Aucun")
        self.file_label.setStyleSheet("color: #7F8C8D; font-size: 8pt;")
        msg_header.addWidget(self.file_label)
        
        select_file_btn = QPushButton("📎")
        select_file_btn.setMaximumWidth(28)
        select_file_btn.setToolTip("Joindre")
        select_file_btn.clicked.connect(self._select_file)
        msg_header.addWidget(select_file_btn)
        
        clear_file_btn = QPushButton("✗")
        clear_file_btn.setMaximumWidth(24)
        clear_file_btn.setToolTip("Supprimer")
        clear_file_btn.clicked.connect(self._clear_file)
        msg_header.addWidget(clear_file_btn)
        
        self.char_count_label = QLabel("0")
        self.char_count_label.setStyleSheet("color: #7F8C8D; font-size: 8pt;")
        msg_header.addWidget(self.char_count_label)
        
        layout.addLayout(msg_header)
        
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Votre message...")
        self.message_edit.setFixedHeight(80)
        self.message_edit.textChanged.connect(self._update_char_count)
        layout.addWidget(self.message_edit)
        
        # Planification (sans GroupBox)
        sched_header = QHBoxLayout()
        
        sched_label = QLabel("🔹 Envoi:")
        sched_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        sched_header.addWidget(sched_label)
        
        self.datetime_edit = QDateTimeEdit()
        self.datetime_edit.setCalendarPopup(True)
        self.datetime_edit.setDateTime(QDateTime.currentDateTime().addSecs(3600))
        
        # Permettre les heures passées mais pas les dates passées
        today = QDateTime.currentDateTime()
        today.setTime(QTime(0, 0, 0))
        self.datetime_edit.setMinimumDateTime(today)
        
        # Connecter les signaux
        self.datetime_edit.dateTimeChanged.connect(self._validate_datetime)
        self.datetime_edit.dateTimeChanged.connect(self._update_button_text)
        
        sched_header.addWidget(self.datetime_edit)
        
        # Boutons rapides
        now_btn = QPushButton("🚀")
        now_btn.setMaximumWidth(28)
        now_btn.setToolTip("Maintenant")
        now_btn.clicked.connect(self._set_now)
        sched_header.addWidget(now_btn)
        
        in_1h_btn = QPushButton("+1h")
        in_1h_btn.setMaximumWidth(38)
        in_1h_btn.clicked.connect(lambda: self._set_time_offset(1))
        sched_header.addWidget(in_1h_btn)
        
        in_3h_btn = QPushButton("+3h")
        in_3h_btn.setMaximumWidth(38)
        in_3h_btn.clicked.connect(lambda: self._set_time_offset(3))
        sched_header.addWidget(in_3h_btn)
        
        multi_btn = QPushButton("📅📅")
        multi_btn.setMaximumWidth(45)
        multi_btn.setToolTip("Planification multi-jours")
        multi_btn.clicked.connect(self._open_multi_schedule)
        sched_header.addWidget(multi_btn)
        
        layout.addLayout(sched_header)
        
        # Message d'erreur
        self.error_label = QLabel()
        self.error_label.setProperty("class", "error")
        self.error_label.setWordWrap(True)
        self.error_label.hide()
        layout.addWidget(self.error_label)
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Effacer")
        clear_btn.setMaximumWidth(90)
        clear_btn.clicked.connect(self._clear_form)
        actions_layout.addWidget(clear_btn)
        
        actions_layout.addStretch()
        
        self.schedule_btn = QPushButton("📅 Planifier")
        self.schedule_btn.setMinimumWidth(120)
        self.schedule_btn.clicked.connect(self._schedule_message)
        actions_layout.addWidget(self.schedule_btn)
        
        layout.addLayout(actions_layout)
        
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
        
        # Ne recharger que si le compte a vraiment changé
        if self._current_account == session_id:
            return
        
        # Ne pas recharger si on est déjà en train de charger
        if self._loading_groups:
            return
        
        # Charger les groupes
        self._loading_groups = True
        self._current_account = session_id
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
                
                # Réactiver le chargement
                self._loading_groups = False
            
            # Utiliser QTimer pour éviter les conflits asyncio
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, lambda: asyncio.create_task(load_dialogs()))
    
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
    
    def _reload_groups(self):
        """Recharge les groupes du compte sélectionné"""
        if not self.account_combo.isEnabled():
            return
        
        current_data = self.account_combo.currentData()
        if not current_data:
            return
        
        # Recharger les groupes (le compte reste connecté)
        async def reload():
            try:
                # Vider la liste actuelle
                self.groups_list.clear()
                
                # Recharger les groupes
                await self._load_groups_for_account(current_data)
                
                QMessageBox.information(
                    self,
                    "Succès",
                    "Groupes rechargés avec succès !",
                    QMessageBox.StandardButton.Ok
                )
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Erreur lors du rechargement: {e}",
                    QMessageBox.StandardButton.Ok
                )
        
        # Utiliser QTimer pour éviter les conflits asyncio
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(0, lambda: asyncio.create_task(reload()))
    
    async def _load_groups_for_account(self, session_id: str):
        """Charge les groupes pour un compte spécifique"""
        try:
            account = self.telegram_manager.accounts.get(session_id)
            if not account or not account.is_connected:
                return
            
            # Récupérer les dialogues
            dialogs = await account.get_dialogs()
            
            if not dialogs:
                item = QListWidgetItem("Aucun groupe trouvé")
                item.setFlags(Qt.ItemFlag.NoItemFlags)
                self.groups_list.addItem(item)
                return
            
            # Ajouter chaque groupe à la liste
            for dialog in dialogs:
                # Construire le texte avec le statut
                item_text = f"{dialog['title']} ({dialog['type']})"
                if dialog['username']:
                    item_text += f" @{dialog['username']}"
                if dialog['participants_count'] > 0:
                    item_text += f" - {dialog['participants_count']} membres"
                
                # Ajouter le statut
                if dialog['is_admin']:
                    item_text += " [ADMIN]"
                elif not dialog['can_send']:
                    item_text += " [Lecture seule]"
                else:
                    item_text += " [Membre]"
                
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, dialog['id'])
                item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                item.setCheckState(Qt.CheckState.Unchecked)
                
                # Marquer visuellement selon le statut
                if dialog['is_admin']:
                    item.setForeground(Qt.GlobalColor.blue)  # Admin en bleu
                elif not dialog['can_send']:
                    item.setForeground(Qt.GlobalColor.gray)  # Lecture seule en gris
                else:
                    item.setForeground(Qt.GlobalColor.black)  # Membre normal en noir
                
                self.groups_list.addItem(item)
            
            self._update_groups_count()
            
        except Exception as e:
            self.logger.error(f"Erreur chargement groupes: {e}")
            item = QListWidgetItem(f"Erreur: {e}")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.groups_list.addItem(item)
    
    def _update_groups_count(self):
        """Met à jour le compteur de groupes"""
        count = sum(
            1 for i in range(self.groups_list.count())
            if self.groups_list.item(i).checkState() == Qt.CheckState.Checked
        )
        self.groups_count_label.setText(f"{count} sélectionné(s)")
    
    def _update_char_count(self):
        """Met à jour le compteur de caractères"""
        text = self.message_edit.toPlainText()
        count = len(text)
        self.char_count_label.setText(f"{count} car.")
    
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
        self.file_label.setText("📎 Aucun")
    
    def _set_time_offset(self, hours: int):
        """Définit l'heure à +X heures"""
        new_time = QDateTime.currentDateTime().addSecs(hours * 3600)
        self.datetime_edit.setDateTime(new_time)
    
    def _set_tomorrow_9am(self):
        """Définit l'heure à demain 9h"""
        tomorrow = QDateTime.currentDateTime().addDays(1)
        tomorrow.setTime(tomorrow.time().fromString("09:00:00", "hh:mm:ss"))
        self.datetime_edit.setDateTime(tomorrow)
    
    def _set_now(self):
        """Définit l'heure à maintenant (envoi immédiat)"""
        now = QDateTime.currentDateTime()
        self.datetime_edit.setDateTime(now)
    
    def _validate_datetime(self, datetime: QDateTime):
        """Valide la date/heure sélectionnée"""
        now = QDateTime.currentDateTime()
        today = QDateTime.currentDateTime()
        today.setTime(QTime(0, 0, 0))  # Minuit d'aujourd'hui
        
        # Si la date est dans le passé (avant minuit d'aujourd'hui)
        if datetime < today:
            # Corriger automatiquement à aujourd'hui à la même heure
            corrected = QDateTime.currentDateTime()
            corrected.setTime(datetime.time())
            self.datetime_edit.setDateTime(corrected)
            
            # Afficher un message informatif
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.information(
                self,
                "Date corrigée",
                "La date ne peut pas être dans le passé.\n"
                "L'heure a été conservée pour aujourd'hui.",
                QMessageBox.StandardButton.Ok
            )
    
    def _update_button_text(self, datetime: QDateTime):
        """Met à jour le texte du bouton selon l'heure sélectionnée"""
        now = QDateTime.currentDateTime()
        
        if datetime <= now:
            self.schedule_btn.setText("🚀 Envoyer")
        else:
            self.schedule_btn.setText("📅 Planifier")
    
    def _open_multi_schedule(self):
        """Ouvre le dialog de planification multi-jours"""
        dialog = MultiScheduleDialog(self)
        
        if dialog.exec() == dialog.DialogCode.Accepted:
            datetimes = dialog.get_scheduled_datetimes()
            
            if not datetimes:
                return
            
            # Utiliser ces dates pour planifier
            self._schedule_multi_messages(datetimes)
    
    def _schedule_multi_messages(self, datetimes: list):
        """Planifie des messages sur plusieurs dates/heures"""
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
        
        message_text = self.message_edit.toPlainText().strip()
        if not message_text:
            self._show_error("Veuillez rédiger un message")
            return
        
        session_id = self.account_combo.currentData()
        file_path = self.selected_file if self.selected_file else None
        
        # Récupérer le nom du compte
        account = self.telegram_manager.accounts.get(session_id)
        account_name = account.account_name if account else "Inconnu"
        
        # Planifier tous les envois
        success_count = 0
        
        for schedule_time in datetimes:
            # Créer une tâche par date/heure avec tous les groupes
            try:
                # Récupérer les infos complètes des groupes
                groups_info = []
                for group_id in selected_groups:
                    # Chercher le nom du groupe dans la liste
                    for i in range(self.groups_list.count()):
                        item = self.groups_list.item(i)
                        if item.data(Qt.ItemDataRole.UserRole) == group_id:
                            group_name = item.text().split(" (")[0]  # Extraire le nom
                            groups_info.append({
                                "id": group_id,
                                "name": group_name
                            })
                            break
                
                task_id = self.scheduler.create_task(
                    session_id=session_id,
                    account_name=account_name,
                    groups=groups_info,
                    message=message_text,
                    schedule_time=schedule_time,
                    file_path=file_path
                )
                success_count += 1
            except Exception as e:
                self.logger.error(f"Erreur lors de la création de la tâche: {e}")
        
        # Message de succès
        total_messages = success_count * len(selected_groups)
        QMessageBox.information(
            self,
            "Succès",
            f"✅ {success_count} tâche(s) planifiée(s) avec succès !\n\n"
            f"📅 {len(datetimes)} date(s)/heure(s)\n"
            f"👥 {len(selected_groups)} groupe(s)\n"
            f"📨 {total_messages} message(s) au total\n\n"
            f"Consultez le tableau de bord pour suivre les envois.",
            QMessageBox.StandardButton.Ok
        )
        
        # Effacer le formulaire
        self._clear_form()
    
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
        
        message_text = self.message_edit.toPlainText().strip()
        if not message_text:
            self._show_error("Veuillez rédiger un message")
            return
        
        schedule_time = self.datetime_edit.dateTime().toPyDateTime()
        is_immediate = schedule_time <= datetime.now()
        
        # Si c'est un envoi immédiat, ajuster le temps à maintenant
        if is_immediate:
            schedule_time = datetime.now()
        
        # Confirmer
        if is_immediate:
            title = "Confirmer l'envoi immédiat"
            confirmation_text = f"Envoyer ce message immédiatement dans {len(selected_groups)} groupe(s) ?\n\n"
            confirmation_text += f"Le message sera envoyé maintenant."
        else:
            title = "Confirmer la planification"
            confirmation_text = f"Planifier ce message dans {len(selected_groups)} groupe(s) ?\n\n"
            confirmation_text += f"Heure d'envoi : {schedule_time.strftime('%d/%m/%Y à %H:%M')}\n\n"
            confirmation_text += f"Le message apparaîtra comme planifié dans votre Telegram."
        
        reply = QMessageBox.question(
            self,
            title,
            confirmation_text,
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
                message_text,
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

