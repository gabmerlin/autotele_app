"""
Widget du tableau de bord
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from core.scheduler import MessageScheduler
from core.telegram_manager import TelegramManager
from ui.styles import FONT_FAMILY, get_success_color, get_warning_color, get_error_color


class DashboardWidget(QWidget):
    """Widget du tableau de bord"""
    
    def __init__(self, scheduler: MessageScheduler, telegram_manager: TelegramManager):
        super().__init__()
        
        self.scheduler = scheduler
        self.telegram_manager = telegram_manager
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        
        # Titre et statistiques
        header_layout = QHBoxLayout()
        
        title = QLabel("Tableau de Bord")
        title.setProperty("class", "subtitle")
        title.setFont(QFont(FONT_FAMILY, 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Statistiques
        self.stats_label = QLabel()
        self.stats_label.setProperty("class", "hint")
        header_layout.addWidget(self.stats_label)
        
        layout.addLayout(header_layout)
        
        # Filtres et actions
        actions_layout = QHBoxLayout()
        
        refresh_btn = QPushButton("🔄 Rafraîchir")
        refresh_btn.setProperty("class", "secondary")
        refresh_btn.clicked.connect(self.refresh)
        actions_layout.addWidget(refresh_btn)
        
        export_btn = QPushButton("💾 Exporter l'historique")
        export_btn.setProperty("class", "secondary")
        export_btn.clicked.connect(self._export_history)
        actions_layout.addWidget(export_btn)
        
        actions_layout.addStretch()
        
        cleanup_btn = QPushButton("🗑️ Nettoyer l'historique")
        cleanup_btn.setProperty("class", "secondary")
        cleanup_btn.clicked.connect(self._cleanup_history)
        actions_layout.addWidget(cleanup_btn)
        
        layout.addLayout(actions_layout)
        
        # Tableau des tâches
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([
            "Statut", "Compte", "Groupes", "Message", "Heure planifiée", "Actions"
        ])
        
        # Configuration du tableau
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.tasks_table.verticalHeader().setVisible(False)
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.tasks_table)
        
        # Charger les tâches
        self.refresh()
    
    def refresh(self):
        """Rafraîchit le tableau de bord"""
        # Mettre à jour les statistiques
        stats = self.scheduler.get_statistics()
        self.stats_label.setText(
            f"Total : {stats['total']} | "
            f"En attente : {stats['pending']} | "
            f"En cours : {stats['processing']} | "
            f"Terminées : {stats['completed']} | "
            f"Échouées : {stats['failed']}"
        )
        
        # Charger les tâches
        tasks = self.scheduler.list_tasks()
        
        self.tasks_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # Statut avec couleur
            status_item = QTableWidgetItem(self._get_status_text(task.status))
            status_item.setForeground(self._get_status_color(task.status))
            self.tasks_table.setItem(row, 0, status_item)
            
            # Compte
            account_item = QTableWidgetItem(task.account_name)
            self.tasks_table.setItem(row, 1, account_item)
            
            # Nombre de groupes
            groups_item = QTableWidgetItem(f"{len(task.groups)} groupe(s)")
            self.tasks_table.setItem(row, 2, groups_item)
            
            # Message (aperçu)
            message_preview = task.message[:50] + "..." if len(task.message) > 50 else task.message
            message_item = QTableWidgetItem(message_preview)
            message_item.setToolTip(task.message)
            self.tasks_table.setItem(row, 3, message_item)
            
            # Heure
            time_item = QTableWidgetItem(task.schedule_time.strftime("%d/%m/%Y %H:%M"))
            self.tasks_table.setItem(row, 4, time_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(5)
            
            # Bouton détails
            details_btn = QPushButton("ℹ️")
            details_btn.setMaximumWidth(40)
            details_btn.clicked.connect(lambda checked, t=task: self._show_task_details(t))
            actions_layout.addWidget(details_btn)
            
            # Bouton supprimer (seulement pour tâches pending)
            if task.status == "pending":
                delete_btn = QPushButton("🗑️")
                delete_btn.setProperty("class", "danger")
                delete_btn.setMaximumWidth(40)
                delete_btn.clicked.connect(lambda checked, tid=task.task_id: self._delete_task(tid))
                actions_layout.addWidget(delete_btn)
            
            actions_layout.addStretch()
            
            self.tasks_table.setCellWidget(row, 5, actions_widget)
        
        if len(tasks) == 0:
            self.tasks_table.setRowCount(1)
            empty_item = QTableWidgetItem("Aucune tâche planifiée")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_table.setItem(0, 0, empty_item)
            self.tasks_table.setSpan(0, 0, 1, 6)
    
    def _get_status_text(self, status: str) -> str:
        """Retourne le texte du statut"""
        status_map = {
            "pending": "⏳ En attente",
            "processing": "⚙️ En cours",
            "completed": "✅ Terminé",
            "failed": "❌ Échoué",
            "partial": "⚠️ Partiel"
        }
        return status_map.get(status, status)
    
    def _get_status_color(self, status: str):
        """Retourne la couleur du statut"""
        from PyQt6.QtGui import QColor
        
        color_map = {
            "pending": QColor("#ff9500"),
            "processing": QColor("#0071e3"),
            "completed": QColor(get_success_color()),
            "failed": QColor(get_error_color()),
            "partial": QColor(get_warning_color())
        }
        return color_map.get(status, QColor("#1d1d1f"))
    
    def _show_task_details(self, task):
        """Affiche les détails d'une tâche"""
        details = f"📋 Détails de la tâche\n\n"
        details += f"ID : {task.task_id}\n"
        details += f"Compte : {task.account_name}\n"
        details += f"Statut : {self._get_status_text(task.status)}\n"
        details += f"Créé le : {task.created_at.strftime('%d/%m/%Y %H:%M')}\n"
        details += f"Planifié pour : {task.schedule_time.strftime('%d/%m/%Y %H:%M')}\n"
        details += f"Nombre de groupes : {len(task.groups)}\n\n"
        
        details += f"📝 Message :\n{task.message}\n\n"
        
        if task.file_path:
            details += f"📎 Fichier joint : {task.file_path}\n\n"
        
        if task.results:
            details += "📊 Résultats par groupe :\n"
            for group_id, result in task.results.items():
                status_emoji = "✅" if result["success"] else "❌"
                details += f"{status_emoji} {result['group_title']}"
                if not result["success"]:
                    details += f" - {result['error']}"
                details += "\n"
        
        QMessageBox.information(
            self,
            "Détails de la tâche",
            details,
            QMessageBox.StandardButton.Ok
        )
    
    def _delete_task(self, task_id: str):
        """Supprime une tâche"""
        reply = QMessageBox.question(
            self,
            "Supprimer la tâche",
            "Êtes-vous sûr de vouloir supprimer cette tâche planifiée ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.scheduler.delete_task(task_id)
            self.refresh()
    
    def _export_history(self):
        """Exporte l'historique en CSV"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter l'historique",
            f"autotele_history_{datetime.now().strftime('%Y%m%d')}.csv",
            "Fichiers CSV (*.csv)"
        )
        
        if file_path:
            from utils.logger import get_logger
            logger = get_logger()
            logger.export_history_csv(file_path)
            
            QMessageBox.information(
                self,
                "Export réussi",
                f"L'historique a été exporté vers :\n{file_path}",
                QMessageBox.StandardButton.Ok
            )
    
    def _cleanup_history(self):
        """Nettoie l'historique ancien"""
        reply = QMessageBox.question(
            self,
            "Nettoyer l'historique",
            "Supprimer les tâches terminées de plus de 30 jours ?\n\n"
            "Cette action est irréversible.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.scheduler.cleanup_old_tasks(30)
            self.refresh()
            
            QMessageBox.information(
                self,
                "Nettoyage terminé",
                "L'historique a été nettoyé.",
                QMessageBox.StandardButton.Ok
            )


from datetime import datetime

