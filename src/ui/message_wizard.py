"""
Wizard étape par étape pour créer et planifier des messages
"""
import asyncio
from datetime import datetime
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QListWidget, QListWidgetItem, QStackedWidget,
    QFileDialog, QMessageBox, QProgressBar, QCalendarWidget, QTimeEdit,
    QCheckBox, QLineEdit
)
from ui.searchable_combobox import SearchableComboBox
from PyQt6.QtCore import Qt, QDate, QTime, QDateTime, QTimer
from PyQt6.QtGui import QFont, QTextCharFormat, QColor

from core.telegram_manager import TelegramManager
from core.scheduler import MessageScheduler
from utils.logger import get_logger


class MessageWizard(QWidget):
    """Assistant étape par étape pour planifier des messages"""
    
    def __init__(self, telegram_manager: TelegramManager, scheduler: MessageScheduler):
        super().__init__()
        
        self.telegram_manager = telegram_manager
        self.scheduler = scheduler
        self.logger = get_logger()
        
        # Données du wizard
        self.selected_account = None
        self.selected_groups = []
        self.message_text = ""
        self.selected_file = None
        self.selected_dates = set()
        self.selected_times = []
        self.current_step = 0
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header avec progression
        self._create_header(layout)
        
        # Zone des étapes (StackedWidget)
        self.steps_stack = QStackedWidget()
        layout.addWidget(self.steps_stack, 1)
        
        # Créer les 4 étapes
        self.steps_stack.addWidget(self._create_step1_account())
        self.steps_stack.addWidget(self._create_step2_groups())
        self.steps_stack.addWidget(self._create_step3_message())
        self.steps_stack.addWidget(self._create_step4_schedule())
        
        # Boutons de navigation
        self._create_navigation(layout)
        
        # Afficher l'étape 1
        self._update_step(0)
    
    def _create_header(self, layout):
        """Crée le header avec la progression"""
        header = QWidget()
        header.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #4A90E2,
                                            stop:1 #357ABD);
                border-radius: 8px;
                padding: 15px;
            }
        """)
        header_layout = QVBoxLayout(header)
        
        # Titre
        self.step_title = QLabel("Étape 1 : Sélectionner le Compte")
        self.step_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.step_title.setStyleSheet("color: white; background: transparent;")
        header_layout.addWidget(self.step_title)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 4)
        self.progress_bar.setValue(1)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Étape %v / %m")
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid white;
                border-radius: 5px;
                text-align: center;
                background: rgba(255, 255, 255, 0.3);
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: white;
                border-radius: 3px;
            }
        """)
        header_layout.addWidget(self.progress_bar)
        
        layout.addWidget(header)
    
    def _create_step1_account(self):
        """Étape 1 : Sélection du compte"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Instructions
        info = QLabel("👤 Choisissez le compte Telegram qui enverra les messages")
        info.setFont(QFont("Segoe UI", 10))
        info.setStyleSheet("color: #7F8C8D; padding: 10px; background: #F5F7FA; border-radius: 6px;")
        layout.addWidget(info)
        
        # Sélecteur de compte
        account_label = QLabel("Compte:")
        account_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(account_label)
        
        self.account_combo = SearchableComboBox()
        self.account_combo.setMinimumHeight(50)
        self.account_combo.setFont(QFont("Segoe UI", 14))
        layout.addWidget(self.account_combo)
        
        layout.addStretch()
        
        return widget
    
    def _create_step2_groups(self):
        """Étape 2 : Sélection des groupes"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Instructions
        info = QLabel("👥 Sélectionnez les groupes qui recevront le message")
        info.setFont(QFont("Segoe UI", 10))
        info.setStyleSheet("color: #7F8C8D; padding: 10px; background: #F5F7FA; border-radius: 6px;")
        layout.addWidget(info)
        
        # Filtre de recherche
        search_layout = QHBoxLayout()
        
        search_label = QLabel("🔍 Rechercher:")
        search_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        search_layout.addWidget(search_label)
        
        self.group_search = QLineEdit()
        self.group_search.setPlaceholderText("Filtrer par nom...")
        self.group_search.textChanged.connect(self._filter_groups)
        self.group_search.setStyleSheet("padding: 5px; font-size: 11pt;")
        search_layout.addWidget(self.group_search)
        
        layout.addLayout(search_layout)
        
        # Boutons d'action
        actions = QHBoxLayout()
        
        reload_btn = QPushButton("🔄 Recharger")
        reload_btn.clicked.connect(self._reload_groups)
        actions.addWidget(reload_btn)
        
        select_all_btn = QPushButton("✓ Tout sélectionner")
        select_all_btn.clicked.connect(self._select_all_groups)
        actions.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("✗ Tout désélectionner")
        deselect_all_btn.clicked.connect(self._deselect_all_groups)
        actions.addWidget(deselect_all_btn)
        
        actions.addStretch()
        
        self.groups_count_label = QLabel("0 sélectionné(s)")
        self.groups_count_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.groups_count_label.setStyleSheet("color: #4A90E2;")
        actions.addWidget(self.groups_count_label)
        
        layout.addLayout(actions)
        
        # Liste des groupes
        self.groups_list = QListWidget()
        self.groups_list.setMinimumHeight(300)
        self.groups_list.itemChanged.connect(self._update_groups_count)
        layout.addWidget(self.groups_list)
        
        return widget
    
    def _create_step3_message(self):
        """Étape 3 : Rédaction du message"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Instructions
        info = QLabel("📝 Rédigez votre message et ajoutez un fichier si nécessaire")
        info.setFont(QFont("Segoe UI", 10))
        info.setStyleSheet("color: #7F8C8D; padding: 10px; background: #F5F7FA; border-radius: 6px;")
        layout.addWidget(info)
        
        # Zone de message
        msg_label = QLabel("Message:")
        msg_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        layout.addWidget(msg_label)
        
        self.message_edit = QTextEdit()
        self.message_edit.setPlaceholderText("Écrivez votre message ici...")
        self.message_edit.setMinimumHeight(200)
        self.message_edit.textChanged.connect(self._update_char_count)
        layout.addWidget(self.message_edit)
        
        # Compteur + fichier
        bottom_row = QHBoxLayout()
        
        self.char_count_label = QLabel("0 caractère(s)")
        self.char_count_label.setStyleSheet("color: #7F8C8D;")
        bottom_row.addWidget(self.char_count_label)
        
        bottom_row.addStretch()
        
        self.file_label = QLabel("📎 Aucun fichier")
        self.file_label.setStyleSheet("color: #7F8C8D;")
        bottom_row.addWidget(self.file_label)
        
        select_file_btn = QPushButton("📎 Joindre un fichier")
        select_file_btn.clicked.connect(self._select_file)
        bottom_row.addWidget(select_file_btn)
        
        clear_file_btn = QPushButton("🗑️")
        clear_file_btn.setMaximumWidth(40)
        clear_file_btn.setToolTip("Supprimer le fichier")
        clear_file_btn.clicked.connect(self._clear_file)
        bottom_row.addWidget(clear_file_btn)
        
        layout.addLayout(bottom_row)
        
        return widget
    
    def _create_step4_schedule(self):
        """Étape 4 : Planification (dates + heures)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # Instructions
        info = QLabel("📅 Sélectionnez les dates et heures d'envoi")
        info.setFont(QFont("Segoe UI", 10))
        info.setStyleSheet("color: #7F8C8D; padding: 10px; background: #F5F7FA; border-radius: 6px;")
        layout.addWidget(info)
        
        # Layout horizontal pour calendrier + horaires
        content = QHBoxLayout()
        content.setSpacing(20)
        
        # === CALENDRIER ===
        cal_layout = QVBoxLayout()
        cal_layout.setSpacing(10)
        
        cal_label = QLabel("📆 Dates:")
        cal_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        cal_layout.addWidget(cal_label)
        
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self._toggle_date)
        cal_layout.addWidget(self.calendar)
        
        # Boutons rapides dates
        date_btns = QHBoxLayout()
        date_btns.setSpacing(10)
        
        week_btn = QPushButton("📅 1 Semaine")
        week_btn.setMaximumWidth(150)
        week_btn.clicked.connect(self._add_week)
        date_btns.addWidget(week_btn)
        
        month_btn = QPushButton("📅 1 Mois")
        month_btn.setMaximumWidth(120)
        month_btn.clicked.connect(self._add_month)
        date_btns.addWidget(month_btn)
        
        date_btns.addStretch()
        
        clear_dates_btn = QPushButton("🗑️ Effacer")
        clear_dates_btn.setMaximumWidth(100)
        clear_dates_btn.clicked.connect(self._clear_dates)
        date_btns.addWidget(clear_dates_btn)
        
        cal_layout.addLayout(date_btns)
        
        content.addLayout(cal_layout, 60)
        
        # === HORAIRES ===
        times_layout = QVBoxLayout()
        times_layout.setSpacing(10)
        
        times_label = QLabel("🕐 Horaires:")
        times_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        times_layout.addWidget(times_label)
        
        # Sélecteur d'heure
        time_selector = QVBoxLayout()
        time_selector.setSpacing(10)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))
        self.time_edit.setDisplayFormat("HH:mm")
        self.time_edit.setMinimumHeight(40)
        self.time_edit.setMaximumWidth(200)
        time_selector.addWidget(self.time_edit)
        
        add_time_btn = QPushButton("➕ Ajouter cette heure")
        add_time_btn.setMinimumHeight(40)
        add_time_btn.setMaximumWidth(200)
        add_time_btn.clicked.connect(self._add_time)
        time_selector.addWidget(add_time_btn)
        
        times_layout.addLayout(time_selector)
        
        # Liste des horaires
        self.times_list = QListWidget()
        self.times_list.setMaximumHeight(150)
        times_layout.addWidget(self.times_list)
        
        clear_times_btn = QPushButton("🗑️ Effacer les horaires")
        clear_times_btn.setMaximumWidth(200)
        clear_times_btn.clicked.connect(self._clear_times)
        times_layout.addWidget(clear_times_btn)
        
        times_layout.addStretch()
        
        content.addLayout(times_layout, 40)
        
        layout.addLayout(content)
        
        # Résumé
        self.summary_label = QLabel("0 date(s) × 0 horaire(s) = 0 envoi(s)")
        self.summary_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self.summary_label.setStyleSheet("color: #4A90E2; padding: 10px; background: #E3F2FD; border-radius: 6px;")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.summary_label)
        
        return widget
    
    def _create_navigation(self, layout):
        """Crée les boutons de navigation"""
        nav = QHBoxLayout()
        
        self.prev_btn = QPushButton("⬅️ Précédent")
        self.prev_btn.setMinimumHeight(40)
        self.prev_btn.clicked.connect(self._previous_step)
        nav.addWidget(self.prev_btn)
        
        nav.addStretch()
        
        self.next_btn = QPushButton("Suivant ➡️")
        self.next_btn.setMinimumHeight(40)
        self.next_btn.clicked.connect(self._next_step)
        nav.addWidget(self.next_btn)
        
        self.finish_btn = QPushButton("✅ Planifier les Envois")
        self.finish_btn.setMinimumHeight(40)
        self.finish_btn.setVisible(False)
        self.finish_btn.clicked.connect(self._finish)
        nav.addWidget(self.finish_btn)
        
        layout.addLayout(nav)
    
    def _update_step(self, step):
        """Met à jour l'affichage de l'étape"""
        self.current_step = step
        self.steps_stack.setCurrentIndex(step)
        self.progress_bar.setValue(step + 1)
        
        # Titres
        titles = [
            "Étape 1 : Sélectionner le Compte",
            "Étape 2 : Sélectionner les Groupes",
            "Étape 3 : Rédiger le Message",
            "Étape 4 : Planifier les Envois"
        ]
        self.step_title.setText(titles[step])
        
        # Boutons
        self.prev_btn.setEnabled(step > 0)
        self.next_btn.setVisible(step < 3)
        self.finish_btn.setVisible(step == 3)
        
        # Charger les données selon l'étape
        if step == 0:
            self.refresh_accounts()
        elif step == 1:
            self._load_groups()
    
    def _previous_step(self):
        """Étape précédente"""
        if self.current_step > 0:
            self._update_step(self.current_step - 1)
    
    def _next_step(self):
        """Étape suivante"""
        # Validation avant de passer à l'étape suivante
        if self.current_step == 0:
            if self.account_combo.currentIndex() < 0:
                QMessageBox.warning(self, "Attention", "Veuillez sélectionner un compte")
                return
            self.selected_account = self.account_combo.currentData()
        
        elif self.current_step == 1:
            selected = []
            for i in range(self.groups_list.count()):
                item = self.groups_list.item(i)
                if item.checkState() == Qt.CheckState.Checked:
                    selected.append(item.data(Qt.ItemDataRole.UserRole))
            
            if not selected:
                QMessageBox.warning(self, "Attention", "Veuillez sélectionner au moins un groupe")
                return
            self.selected_groups = selected
        
        elif self.current_step == 2:
            self.message_text = self.message_edit.toPlainText().strip()
            if not self.message_text:
                QMessageBox.warning(self, "Attention", "Veuillez rédiger un message")
                return
        
        if self.current_step < 3:
            self._update_step(self.current_step + 1)
    
    def _finish(self):
        """Finaliser et planifier"""
        if not self.selected_dates or not self.selected_times:
            QMessageBox.warning(
                self,
                "Attention",
                "Veuillez sélectionner au moins une date et un horaire"
            )
            return
        
        # Générer tous les datetime
        datetimes = []
        now = datetime.now()
        
        for qdate in sorted(self.selected_dates):
            for qtime in self.selected_times:
                dt = datetime(
                    qdate.year(),
                    qdate.month(),
                    qdate.day(),
                    qtime.hour(),
                    qtime.minute()
                )
                
                # Si c'est dans le passé
                if dt < now:
                    # Si c'est aujourd'hui, programmer pour maintenant (envoi immédiat)
                    if qdate == QDate.currentDate():
                        datetimes.append(now)
                    # Sinon, ignorer (date complètement passée)
                else:
                    # Future : programmer normalement
                    datetimes.append(dt)
        
        if not datetimes:
            QMessageBox.warning(
                self,
                "Attention",
                "Toutes les dates/heures sélectionnées sont dans le passé.\n"
                "Veuillez sélectionner des dates/heures futures."
            )
            return
        
        # Planifier
        self._schedule_all(datetimes)
    
    def _schedule_all(self, datetimes):
        """Planifie tous les envois - OPTIMISÉ : Une seule tâche pour toutes les dates"""
        account = self.telegram_manager.accounts.get(self.selected_account)
        account_name = account.account_name if account else "Inconnu"
        
        try:
            # VÉRIFICATION ANTI-RATE-LIMIT (optimisé pour 27 req/sec)
            total_messages = len(self.selected_groups) * len(datetimes)
            max_messages = 500  # Limite augmentée
            
            if total_messages > max_messages:
                QMessageBox.warning(
                    self,
                    "⚠️ Trop de messages",
                    f"⚠️ Limite atteinte !\n\n"
                    f"Total de messages : {total_messages}\n"
                    f"Maximum par tâche : {max_messages}\n\n"
                    f"Actuellement :\n"
                    f"• {len(self.selected_groups)} groupes\n"
                    f"• {len(datetimes)} dates/heures\n\n"
                    f"💡 Divise en plusieurs tâches ou réduis le nombre de groupes/dates."
                )
                return
            
            # Construire groups_info depuis selected_groups
            groups_info = []
            for group_data in self.selected_groups:
                groups_info.append({
                    "id": group_data['id'],
                    "name": group_data['title']
                })
            
            # Créer UNE SEULE tâche avec toutes les dates/heures
            task_id = self.scheduler.create_task(
                session_id=self.selected_account,
                account_name=account_name,
                groups=groups_info,
                message=self.message_text,
                schedule_times=datetimes,  # Passer TOUTES les dates en une fois
                file_path=self.selected_file
            )
            
            success = task_id is not None
            total_messages = len(self.selected_groups) * len(datetimes) if success else 0
            
            if success:
                QMessageBox.information(
                    self,
                    "Messages planifiés",
                    f"✅ Tâche créée avec succès !\n\n"
                    f"📅 {len(datetimes)} date(s)/heure(s)\n"
                    f"👥 {len(self.selected_groups)} groupe(s)\n"
                    f"📨 {total_messages} message(s) au total\n\n"
                    f"⚡ Chaque groupe recevra toutes les dates en un seul passage !"
                )
            else:
                QMessageBox.warning(
                    self,
                    "Erreur",
                    "❌ Échec de la création de la tâche"
                )
        
        except Exception as e:
            self.logger.error(f"Erreur planification: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            QMessageBox.warning(
                self,
                "Erreur",
                f"❌ Erreur lors de la planification: {str(e)}"
            )
        
        # Réinitialiser le wizard
        self._reset_wizard()
    
    def _reset_wizard(self):
        """Réinitialise le wizard"""
        self.selected_account = None
        self.selected_groups = []
        self.message_text = ""
        self.selected_file = None
        self.selected_dates.clear()
        self.selected_times = []
        
        self.message_edit.clear()
        self.file_label.setText("📎 Aucun fichier")
        self._clear_dates()
        self._clear_times()
        
        self._update_step(0)
    
    # === MÉTHODES UTILITAIRES ===
    
    def refresh_accounts(self):
        """Rafraîchit la liste des comptes"""
        self.account_combo.clear()
        accounts = self.telegram_manager.list_accounts()
        
        for account in accounts:
            if account["is_connected"]:
                text = f"{account['account_name']} ({account['phone']})"
                self.account_combo.addItem(text, account["session_id"])
    
    def _load_groups(self):
        """Charge les groupes du compte sélectionné (optimisé)"""
        async def load():
            # Afficher le loading
            self.groups_list.clear()
            loading_item = QListWidgetItem("🔄 Chargement des groupes...")
            loading_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.groups_list.addItem(loading_item)
            
            account = self.telegram_manager.accounts.get(self.selected_account)
            if not account or not account.is_connected:
                self.groups_list.clear()
                error_item = QListWidgetItem("❌ Compte non connecté")
                error_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.groups_list.addItem(error_item)
                return
            
            try:
                dialogs = await account.get_dialogs()
                
                # Vider et remplir avec progression
                self.groups_list.clear()
                
                # Traitement ULTRA RAPIDE par lots plus gros
                batch_size = 25  # Lots plus gros pour plus de vitesse
                for i in range(0, len(dialogs), batch_size):
                    batch = dialogs[i:i+batch_size]
                    
                    for dialog in batch:
                        item_text = f"{dialog['title']} ({dialog['type']})"
                        if dialog['is_admin']:
                            item_text += " [ADMIN]"
                        
                        item = QListWidgetItem(item_text)
                        # Stocker un dict avec id et title
                        item.setData(Qt.ItemDataRole.UserRole, {
                            'id': dialog['id'],
                            'title': dialog['title']
                        })
                        item.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
                        item.setCheckState(Qt.CheckState.Unchecked)
                        
                        if dialog['is_admin']:
                            item.setForeground(QColor("#4A90E2"))
                        
                        self.groups_list.addItem(item)
                    
                    # Micro-pause ultra courte pour la vitesse
                    await asyncio.sleep(0.005)
                
                self._update_groups_count()
                
            except Exception as e:
                self.groups_list.clear()
                error_item = QListWidgetItem(f"❌ Erreur: {str(e)[:50]}")
                error_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.groups_list.addItem(error_item)
        
        QTimer.singleShot(0, lambda: asyncio.create_task(load()))
    
    def _reload_groups(self):
        """Recharge les groupes"""
        self._load_groups()
    
    def _select_all_groups(self):
        """Sélectionne tous les groupes visibles (non filtrés)"""
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable and not item.isHidden():
                item.setCheckState(Qt.CheckState.Checked)
    
    def _deselect_all_groups(self):
        """Désélectionne tous les groupes visibles (non filtrés)"""
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable and not item.isHidden():
                item.setCheckState(Qt.CheckState.Unchecked)
    
    def _update_groups_count(self):
        """Met à jour le compteur de groupes"""
        count = sum(
            1 for i in range(self.groups_list.count())
            if self.groups_list.item(i).checkState() == Qt.CheckState.Checked
        )
        self.groups_count_label.setText(f"{count} sélectionné(s)")
    
    def _filter_groups(self):
        """Filtre les groupes par nom"""
        search_text = self.group_search.text().lower()
        
        for i in range(self.groups_list.count()):
            item = self.groups_list.item(i)
            item_text = item.text().lower()
            
            # Afficher/masquer selon la recherche
            if search_text in item_text:
                item.setHidden(False)
            else:
                item.setHidden(True)
    
    def _update_char_count(self):
        """Met à jour le compteur de caractères"""
        count = len(self.message_edit.toPlainText())
        self.char_count_label.setText(f"{count} caractère(s)")
    
    def _select_file(self):
        """Sélectionne un fichier"""
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
        """Supprime le fichier"""
        self.selected_file = None
        self.file_label.setText("📎 Aucun fichier")
    
    def _toggle_date(self, date: QDate):
        """Ajoute/retire une date"""
        if date in self.selected_dates:
            self.selected_dates.remove(date)
            self._remove_highlight(date)
        else:
            self.selected_dates.add(date)
            self._add_highlight(date)
        self._update_summary()
    
    def _add_date(self, date: QDate):
        """Ajoute une date"""
        if date not in self.selected_dates:
            self.selected_dates.add(date)
            self._add_highlight(date)
            self._update_summary()
    
    def _add_week(self):
        """Ajoute 7 jours"""
        today = QDate.currentDate()
        for i in range(7):
            date = today.addDays(i)
            if date not in self.selected_dates:
                self.selected_dates.add(date)
                self._add_highlight(date)
        self._update_summary()
    
    def _add_month(self):
        """Ajoute 30 jours"""
        today = QDate.currentDate()
        for i in range(30):
            date = today.addDays(i)
            if date not in self.selected_dates:
                self.selected_dates.add(date)
                self._add_highlight(date)
        self._update_summary()
    
    def _clear_dates(self):
        """Efface toutes les dates"""
        for date in list(self.selected_dates):
            self._remove_highlight(date)
        self.selected_dates.clear()
        self._update_summary()
    
    def _add_highlight(self, date: QDate):
        """Surligne une date"""
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#4A90E2"))
        fmt.setForeground(QColor("white"))
        fmt.setFontWeight(QFont.Weight.Bold)
        self.calendar.setDateTextFormat(date, fmt)
    
    def _remove_highlight(self, date: QDate):
        """Retire le surlignage"""
        self.calendar.setDateTextFormat(date, QTextCharFormat())
    
    def _add_time(self):
        """Ajoute l'heure sélectionnée"""
        time = self.time_edit.time()
        if time not in self.selected_times:
            self.selected_times.append(time)
            self.selected_times.sort()
            self._refresh_times_list()
            self._update_summary()
    
    def _add_preset_time(self, hour, minute):
        """Ajoute une heure prédéfinie"""
        time = QTime(hour, minute)
        if time not in self.selected_times:
            self.selected_times.append(time)
            self.selected_times.sort()
            self._refresh_times_list()
            self._update_summary()
    
    def _clear_times(self):
        """Efface tous les horaires"""
        self.selected_times.clear()
        self.times_list.clear()
        self._update_summary()
    
    def _refresh_times_list(self):
        """Rafraîchit la liste des horaires"""
        self.times_list.clear()
        for time in self.selected_times:
            item = QListWidgetItem(f"🕐 {time.toString('HH:mm')}")
            self.times_list.addItem(item)
    
    def _update_summary(self):
        """Met à jour le résumé"""
        nb_dates = len(self.selected_dates)
        nb_times = len(self.selected_times)
        total = nb_dates * nb_times
        
        self.summary_label.setText(
            f"{nb_dates} date(s) × {nb_times} horaire(s) = {total} envoi(s)"
        )

