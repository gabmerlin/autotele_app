"""
Widget pour afficher les tâches en cours et en attente
"""
import asyncio
from datetime import datetime
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class ActiveTasksWidget(QWidget):
    """Widget pour voir les tâches en cours et en attente"""
    
    def __init__(self, telegram_manager, scheduler):
        super().__init__()
        self.telegram_manager = telegram_manager
        self.scheduler = scheduler
        self.init_ui()
        
        # Timer pour actualiser automatiquement (plus fréquent)
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_tasks)
        self.refresh_timer.start(1000)  # Actualiser toutes les 1 seconde pour fluidité maximale
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # En-tête
        header_layout = QHBoxLayout()
        
        title = QLabel("📤 Envois en cours")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Bouton actualiser
        refresh_btn = QPushButton("🔄 Actualiser")
        refresh_btn.clicked.connect(self.refresh_tasks)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Table des tâches
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(6)
        self.tasks_table.setHorizontalHeaderLabels([
            "📅 Programmé pour", "👤 Compte", "👥 Groupes", "📝 Message", "📊 Statut", "Actions"
        ])
        
        # Configuration des colonnes
        header = self.tasks_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Compte
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Groupes
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)          # Message
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Statut
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # Actions
        
        self.tasks_table.setAlternatingRowColors(True)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tasks_table.setMinimumHeight(400)
        
        layout.addWidget(self.tasks_table)
        
        # Boutons d'action
        buttons_layout = QHBoxLayout()
        
        cancel_selected_btn = QPushButton("❌ Annuler sélection")
        cancel_selected_btn.clicked.connect(self._cancel_selected)
        buttons_layout.addWidget(cancel_selected_btn)
        
        cancel_all_btn = QPushButton("❌ Annuler tout")
        cancel_all_btn.clicked.connect(self._cancel_all)
        buttons_layout.addWidget(cancel_all_btn)
        
        buttons_layout.addStretch()
        
        # Statistiques
        self.stats_label = QLabel("📊 Statistiques : 0 tâches en cours")
        self.stats_label.setStyleSheet("color: #666; font-size: 12pt;")
        buttons_layout.addWidget(self.stats_label)
        
        layout.addLayout(buttons_layout)
        
        # Charger les tâches initiales
        self.refresh_tasks()
    
    def refresh_tasks(self):
        """Actualise la liste des tâches"""
        try:
            # Récupérer les tâches du scheduler
            all_tasks = list(self.scheduler.tasks.values())
            
            # Filtrer les tâches en cours et en attente
            active_tasks = []
            for task in all_tasks:
                if task.status in ["pending", "running", "processing"]:
                    active_tasks.append(task)
            
            # Trier par date de programmation (avec gestion d'erreur)
            def get_first_time(task):
                try:
                    if hasattr(task, 'schedule_times') and task.schedule_times:
                        return task.schedule_times[0]
                    return datetime.now()
                except Exception:
                    return datetime.now()
            
            active_tasks.sort(key=get_first_time)
            
            # Afficher les tâches
            self._display_tasks(active_tasks)
            
            # Mettre à jour les statistiques
            pending_count = len([t for t in active_tasks if t.status == "pending"])
            running_count = len([t for t in active_tasks if t.status in ["running", "processing"]])
            
            self.stats_label.setText(
                f"📊 Statistiques : {pending_count} en attente, {running_count} en cours"
            )
            
        except Exception as e:
            print(f"❌ Erreur refresh_tasks: {e}")
            import traceback
            traceback.print_exc()
            self.tasks_table.setRowCount(1)
            error_item = QTableWidgetItem(f"❌ Erreur: {str(e)[:50]}")
            error_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_table.setItem(0, 0, error_item)
            self.tasks_table.setSpan(0, 0, 1, 6)
    
    def _display_tasks(self, tasks):
        """Affiche les tâches dans la table"""
        # Ne pas clear() pour garder les en-têtes
        self.tasks_table.setRowCount(0)
        
        # Réinitialiser les en-têtes
        self.tasks_table.setHorizontalHeaderLabels([
            "📅 Programmé pour", "👤 Compte", "👥 Groupes", "📝 Message", "📊 Statut", "Actions"
        ])
        
        if not tasks:
            self.tasks_table.setRowCount(1)
            empty_item = QTableWidgetItem("✅ Aucune tâche en cours")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tasks_table.setItem(0, 0, empty_item)
            self.tasks_table.setSpan(0, 0, 1, 6)
            return
        
        self.tasks_table.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            try:
                # Date/Heure programmée (afficher le nombre de dates)
                try:
                    if hasattr(task, 'schedule_times') and task.schedule_times and len(task.schedule_times) > 1:
                        date_str = f"{len(task.schedule_times)} dates"
                        tooltip = "\n".join([st.strftime("%d/%m/%Y %H:%M") for st in task.schedule_times[:10]])  # Max 10 pour le tooltip
                        if len(task.schedule_times) > 10:
                            tooltip += f"\n... et {len(task.schedule_times) - 10} autres"
                    elif hasattr(task, 'schedule_times') and task.schedule_times:
                        schedule_time = task.schedule_times[0]
                        date_str = schedule_time.strftime("%d/%m/%Y %H:%M")
                        tooltip = date_str
                    else:
                        date_str = "Non défini"
                        tooltip = date_str
                except Exception as e:
                    print(f"⚠️ Erreur date row {row}: {e}")
                    date_str = "Erreur"
                    tooltip = str(e)
                
                date_item = QTableWidgetItem(date_str)
                date_item.setToolTip(tooltip)
                self.tasks_table.setItem(row, 0, date_item)
                
                # Compte
                account_item = QTableWidgetItem(task.account_name)
                self.tasks_table.setItem(row, 1, account_item)
                
                # Groupes (plusieurs groupes par tâche)
                try:
                    if task.groups and len(task.groups) > 0:
                        if len(task.groups) == 1:
                            groups_text = task.groups[0].get("name", task.groups[0].get("title", "Inconnu"))
                        else:
                            groups_text = f"{len(task.groups)} groupes"
                        
                        tooltip = ", ".join([g.get("name", g.get("title", "Inconnu")) for g in task.groups])
                    else:
                        groups_text = "Aucun groupe"
                        tooltip = groups_text
                except Exception:
                    groups_text = "Erreur"
                    tooltip = groups_text
                
                groups_item = QTableWidgetItem(groups_text)
                groups_item.setToolTip(tooltip)
                self.tasks_table.setItem(row, 2, groups_item)
                
                # Message
                message_text = task.message[:80] + "..." if len(task.message) > 80 else task.message
                message_item = QTableWidgetItem(message_text)
                message_item.setToolTip(task.message)
                self.tasks_table.setItem(row, 3, message_item)
                
                # Statut
                status_item = QTableWidgetItem()
                if task.status == "pending":
                    status_item.setText("⏳ En attente")
                    status_item.setBackground(QColor(255, 255, 200))  # Jaune clair
                elif task.status in ["running", "processing"]:
                    status_item.setText("🚀 En cours")
                    status_item.setBackground(QColor(200, 255, 200))  # Vert clair
                else:
                    status_item.setText("❓ Inconnu")
                    status_item.setBackground(QColor(255, 200, 200))  # Rouge clair
                
                status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tasks_table.setItem(row, 4, status_item)
                
                # Actions
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(5, 2, 5, 2)
                actions_layout.setSpacing(5)
                
                cancel_btn = QPushButton("❌")
                cancel_btn.setMaximumWidth(40)
                cancel_btn.setToolTip("Annuler cette tâche")
                cancel_btn.clicked.connect(lambda checked, t=task: self._cancel_task(t))
                actions_layout.addWidget(cancel_btn)
                
                self.tasks_table.setCellWidget(row, 5, actions_widget)
                
            except Exception as e:
                print(f"❌ Erreur affichage ligne {row}: {e}")
                import traceback
                traceback.print_exc()
                # Afficher une ligne d'erreur
                error_item = QTableWidgetItem(f"❌ Erreur ligne {row}")
                self.tasks_table.setItem(row, 0, error_item)
        
        # Forcer la mise à jour
        self.tasks_table.update()
        self.tasks_table.repaint()
    
    def _cancel_task(self, task):
        """Annule une tâche spécifique"""
        # Afficher les dates
        if hasattr(task, 'schedule_times') and len(task.schedule_times) > 1:
            dates_str = f"{len(task.schedule_times)} dates"
        else:
            first_time = task.schedule_times[0] if hasattr(task, 'schedule_times') else datetime.now()
            dates_str = first_time.strftime('%d/%m/%Y %H:%M:%S')
        
        reply = QMessageBox.question(
            self,
            "Confirmer l'annulation",
            f"Annuler cette tâche ?\n\n"
            f"Compte: {task.account_name}\n"
            f"Groupes: {len(task.groups)}\n"
            f"Programmé pour: {dates_str}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Annuler la tâche via le scheduler
                self.scheduler.cancel_task(task.task_id)
                print(f"✅ Tâche {task.task_id[:8]} annulée")
                
                # Actualiser l'affichage
                self.refresh_tasks()
                
            except Exception as e:
                print(f"❌ Erreur annulation: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible d'annuler la tâche :\n{e}"
                )
    
    def _cancel_selected(self):
        """Annule les tâches sélectionnées"""
        selected_rows = set(item.row() for item in self.tasks_table.selectedItems())
        
        if not selected_rows:
            QMessageBox.warning(self, "Attention", "Aucune tâche sélectionnée")
            return
        
        # Récupérer les tâches actives
        all_tasks = list(self.scheduler.tasks.values())
        active_tasks = [task for task in all_tasks if task.status in ["pending", "running", "processing"]]
        
        # Trier avec gestion d'erreur
        def get_first_time(task):
            try:
                if hasattr(task, 'schedule_times') and task.schedule_times:
                    return task.schedule_times[0]
                return datetime.now()
            except Exception:
                return datetime.now()
        
        active_tasks.sort(key=get_first_time)
        
        selected_tasks = [active_tasks[row] for row in selected_rows if row < len(active_tasks)]
        
        if not selected_tasks:
            QMessageBox.warning(self, "Attention", "Aucune tâche valide sélectionnée")
            return
        
        reply = QMessageBox.question(
            self,
            "Confirmer l'annulation",
            f"Annuler {len(selected_tasks)} tâche(s) sélectionnée(s) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                for task in selected_tasks:
                    self.scheduler.cancel_task(task.task_id)
                    print(f"✅ Tâche {task.task_id[:8]} annulée")
                
                self.refresh_tasks()
                
                QMessageBox.information(
                    self,
                    "Succès",
                    f"✅ {len(selected_tasks)} tâche(s) annulée(s)"
                )
            except Exception as e:
                print(f"❌ Erreur annulation multiple: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'annulation :\n{e}")
    
    def _cancel_all(self):
        """Annule toutes les tâches en cours"""
        all_tasks = list(self.scheduler.tasks.values())
        active_tasks = [task for task in all_tasks if task.status in ["pending", "running", "processing"]]
        
        if not active_tasks:
            QMessageBox.warning(self, "Attention", "Aucune tâche à annuler")
            return
        
        reply = QMessageBox.question(
            self,
            "⚠️ CONFIRMER",
            f"⚠️ ATTENTION\n\n"
            f"Annuler TOUTES les {len(active_tasks)} tâche(s) en cours ?\n\n"
            f"Cette action est irréversible !",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                cancelled_count = 0
                for task in active_tasks:
                    try:
                        self.scheduler.cancel_task(task.task_id)
                        print(f"✅ Tâche {task.task_id[:8]} annulée")
                        cancelled_count += 1
                    except Exception as e:
                        print(f"❌ Erreur annulation tâche {task.task_id[:8]}: {e}")
                
                self.refresh_tasks()
                
                QMessageBox.information(
                    self,
                    "Succès",
                    f"✅ {cancelled_count}/{len(active_tasks)} tâche(s) annulée(s)"
                )
            except Exception as e:
                print(f"❌ Erreur annulation globale: {e}")
                import traceback
                traceback.print_exc()
                QMessageBox.critical(self, "Erreur", f"Erreur lors de l'annulation :\n{e}")
