"""
Dialog pour planifier des messages sur plusieurs jours avec plusieurs horaires
"""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCalendarWidget, QTimeEdit, QListWidget, QListWidgetItem,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt, QDate, QTime, QDateTime
from PyQt6.QtGui import QFont, QTextCharFormat, QColor
from datetime import datetime, timedelta


class MultiScheduleDialog(QDialog):
    """Dialog pour sélectionner plusieurs jours et horaires"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_dates = set()  # Set de QDate
        self.selected_times = []  # Liste de QTime
        self.scheduled_datetimes = []  # Liste finale de datetime
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        self.setWindowTitle("📅 Planification Multi-Jours")
        self.setModal(True)
        self.resize(700, 550)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Titre
        title = QLabel("📅 Planifier sur Plusieurs Jours")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #4A90E2;")
        layout.addWidget(title)
        
        # Instructions
        info = QLabel("1️⃣ Cliquez sur les dates dans le calendrier\n2️⃣ Ajoutez des horaires\n3️⃣ Validez pour planifier tous les envois")
        info.setStyleSheet("color: #7F8C8D; font-size: 9pt; padding: 8px; background: #F5F7FA; border-radius: 6px;")
        layout.addWidget(info)
        
        # Layout horizontal pour calendrier + infos
        main_content = QHBoxLayout()
        
        # === CALENDRIER ===
        cal_group = QGroupBox("📆 Sélectionner les Dates")
        cal_layout = QVBoxLayout(cal_group)
        
        self.calendar = QCalendarWidget()
        self.calendar.setMinimumDate(QDate.currentDate())
        self.calendar.setGridVisible(True)
        self.calendar.clicked.connect(self._toggle_date)
        cal_layout.addWidget(self.calendar)
        
        # Boutons rapides calendrier
        cal_btns = QHBoxLayout()
        
        today_btn = QPushButton("Aujourd'hui")
        today_btn.setMaximumWidth(100)
        today_btn.clicked.connect(lambda: self._add_date(QDate.currentDate()))
        cal_btns.addWidget(today_btn)
        
        tomorrow_btn = QPushButton("Demain")
        tomorrow_btn.setMaximumWidth(100)
        tomorrow_btn.clicked.connect(lambda: self._add_date(QDate.currentDate().addDays(1)))
        cal_btns.addWidget(tomorrow_btn)
        
        week_btn = QPushButton("7 Jours")
        week_btn.setMaximumWidth(100)
        week_btn.clicked.connect(self._add_week)
        cal_btns.addWidget(week_btn)
        
        cal_btns.addStretch()
        
        clear_dates_btn = QPushButton("🗑️ Effacer Dates")
        clear_dates_btn.setMaximumWidth(120)
        clear_dates_btn.clicked.connect(self._clear_dates)
        cal_btns.addWidget(clear_dates_btn)
        
        cal_layout.addLayout(cal_btns)
        
        main_content.addWidget(cal_group, 60)
        
        # === HORAIRES ===
        times_group = QGroupBox("🕐 Horaires d'Envoi")
        times_layout = QVBoxLayout(times_group)
        
        # Sélecteur d'heure
        time_selector = QHBoxLayout()
        
        time_label = QLabel("Heure:")
        time_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        time_selector.addWidget(time_label)
        
        self.time_edit = QTimeEdit()
        self.time_edit.setTime(QTime(9, 0))
        self.time_edit.setDisplayFormat("HH:mm")
        time_selector.addWidget(self.time_edit)
        
        add_time_btn = QPushButton("➕ Ajouter")
        add_time_btn.setMaximumWidth(90)
        add_time_btn.clicked.connect(self._add_time)
        time_selector.addWidget(add_time_btn)
        
        times_layout.addLayout(time_selector)
        
        # Boutons horaires prédéfinis
        preset_times = QHBoxLayout()
        
        morning_btn = QPushButton("9h")
        morning_btn.setMaximumWidth(50)
        morning_btn.clicked.connect(lambda: self._add_preset_time(9, 0))
        preset_times.addWidget(morning_btn)
        
        noon_btn = QPushButton("12h")
        noon_btn.setMaximumWidth(50)
        noon_btn.clicked.connect(lambda: self._add_preset_time(12, 0))
        preset_times.addWidget(noon_btn)
        
        afternoon_btn = QPushButton("15h")
        afternoon_btn.setMaximumWidth(50)
        afternoon_btn.clicked.connect(lambda: self._add_preset_time(15, 0))
        preset_times.addWidget(afternoon_btn)
        
        evening_btn = QPushButton("18h")
        evening_btn.setMaximumWidth(50)
        evening_btn.clicked.connect(lambda: self._add_preset_time(18, 0))
        preset_times.addWidget(evening_btn)
        
        preset_times.addStretch()
        
        times_layout.addLayout(preset_times)
        
        # Liste des horaires
        times_list_label = QLabel("Horaires sélectionnés:")
        times_list_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        times_layout.addWidget(times_list_label)
        
        self.times_list = QListWidget()
        self.times_list.setMaximumHeight(150)
        times_layout.addWidget(self.times_list)
        
        clear_times_btn = QPushButton("🗑️ Effacer Horaires")
        clear_times_btn.clicked.connect(self._clear_times)
        times_layout.addWidget(clear_times_btn)
        
        times_layout.addStretch()
        
        main_content.addWidget(times_group, 40)
        
        layout.addLayout(main_content)
        
        # === RÉSUMÉ ===
        summary_group = QGroupBox("📊 Résumé")
        summary_layout = QVBoxLayout(summary_group)
        
        self.summary_label = QLabel("0 date(s) × 0 horaire(s) = 0 envoi(s) planifié(s)")
        self.summary_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.summary_label.setStyleSheet("color: #4A90E2; padding: 8px;")
        self.summary_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        summary_layout.addWidget(self.summary_label)
        
        layout.addWidget(summary_group)
        
        # === BOUTONS D'ACTION ===
        actions = QHBoxLayout()
        
        cancel_btn = QPushButton("❌ Annuler")
        cancel_btn.setMinimumWidth(120)
        cancel_btn.clicked.connect(self.reject)
        actions.addWidget(cancel_btn)
        
        actions.addStretch()
        
        self.validate_btn = QPushButton("✅ Valider et Planifier")
        self.validate_btn.setMinimumWidth(180)
        self.validate_btn.clicked.connect(self._validate)
        self.validate_btn.setEnabled(False)
        actions.addWidget(self.validate_btn)
        
        layout.addLayout(actions)
        
        self._update_summary()
    
    def _toggle_date(self, date: QDate):
        """Ajoute ou retire une date"""
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
        """Ajoute les 7 prochains jours"""
        today = QDate.currentDate()
        for i in range(7):
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
        """Surligne une date dans le calendrier"""
        fmt = QTextCharFormat()
        fmt.setBackground(QColor("#4A90E2"))
        fmt.setForeground(QColor("white"))
        fmt.setFontWeight(QFont.Weight.Bold)
        self.calendar.setDateTextFormat(date, fmt)
    
    def _remove_highlight(self, date: QDate):
        """Retire le surlignage d'une date"""
        self.calendar.setDateTextFormat(date, QTextCharFormat())
    
    def _add_time(self):
        """Ajoute l'heure sélectionnée"""
        time = self.time_edit.time()
        if time not in self.selected_times:
            self.selected_times.append(time)
            self.selected_times.sort()
            self._refresh_times_list()
            self._update_summary()
    
    def _add_preset_time(self, hour: int, minute: int):
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
            item.setData(Qt.ItemDataRole.UserRole, time)
            self.times_list.addItem(item)
    
    def _update_summary(self):
        """Met à jour le résumé"""
        nb_dates = len(self.selected_dates)
        nb_times = len(self.selected_times)
        total = nb_dates * nb_times
        
        self.summary_label.setText(
            f"{nb_dates} date(s) × {nb_times} horaire(s) = {total} envoi(s) planifié(s)"
        )
        
        self.validate_btn.setEnabled(total > 0)
    
    def _validate(self):
        """Valide et génère tous les datetime"""
        if not self.selected_dates or not self.selected_times:
            QMessageBox.warning(
                self,
                "Attention",
                "Veuillez sélectionner au moins une date et un horaire.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Générer tous les datetime
        self.scheduled_datetimes.clear()
        
        for qdate in sorted(self.selected_dates):
            for qtime in self.selected_times:
                # Convertir en datetime Python
                dt = datetime(
                    qdate.year(),
                    qdate.month(),
                    qdate.day(),
                    qtime.hour(),
                    qtime.minute()
                )
                
                # Ignorer les dates passées
                if dt > datetime.now():
                    self.scheduled_datetimes.append(dt)
        
        if not self.scheduled_datetimes:
            QMessageBox.warning(
                self,
                "Attention",
                "Toutes les dates/heures sélectionnées sont dans le passé.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        # Confirmation
        msg = f"Voulez-vous planifier {len(self.scheduled_datetimes)} envoi(s) ?\n\n"
        msg += "Premiers envois:\n"
        for dt in self.scheduled_datetimes[:5]:
            msg += f"  • {dt.strftime('%d/%m/%Y à %H:%M')}\n"
        
        if len(self.scheduled_datetimes) > 5:
            msg += f"  ... et {len(self.scheduled_datetimes) - 5} autre(s)"
        
        reply = QMessageBox.question(
            self,
            "Confirmer",
            msg,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.accept()
    
    def get_scheduled_datetimes(self):
        """Retourne la liste des datetime planifiés"""
        return self.scheduled_datetimes

