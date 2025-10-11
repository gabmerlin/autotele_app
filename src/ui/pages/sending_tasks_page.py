"""
Page de gestion des envois en cours.
"""
from typing import Optional
from nicegui import ui

from services.sending_tasks_manager import sending_tasks_manager, SendingTask
from ui.components.dialogs import ConfirmDialog
from utils.logger import get_logger
from utils.notification_manager import notify

logger = get_logger()


class SendingTasksPage:
    """Page de gestion des envois en cours."""
    
    def __init__(self):
        """Initialise la page."""
        self.tasks_container: Optional[ui.column] = None
        self.refresh_timer: Optional[ui.timer] = None
    
    def render(self) -> None:
        """Rend la page."""
        with ui.column().classes('w-full gap-6 p-8'):
            # En-tête
            with ui.row().classes('items-center gap-3 mb-2'):
                ui.label('📤').classes('text-4xl').style('color: var(--primary);')
                ui.label('Envois en cours').classes('text-3xl font-bold').style(
                    'color: var(--text-primary);'
                )
            
            ui.label('Gérez vos envois de messages en arrière-plan').classes('text-sm').style(
                'color: var(--text-secondary);'
            )
            ui.separator().style('background: var(--border); height: 1px; border: none; margin: 16px 0;')
            
            # Boutons d'action
            with ui.row().classes('w-full gap-3 mb-4'):
                ui.button(
                    '↻ Rafraîchir',
                    on_click=self.refresh_tasks
                ).props('outline').style('color: var(--accent);')
                
                def cleanup_finished():
                    finished_tasks = [
                        task for task in sending_tasks_manager.get_all_tasks()
                        if task.status in ['terminé', 'annulé']
                    ]
                    for task in finished_tasks:
                        sending_tasks_manager.remove_task(task.task_id)
                    notify(f'✓ {len(finished_tasks)} tâche(s) terminée(s) supprimée(s)', type='positive')
                    self.refresh_tasks()
                
                ui.button(
                    '🗑️ Nettoyer terminés',
                    on_click=cleanup_finished
                ).props('outline').style('color: var(--secondary);')
            
            # Container pour les tâches
            self.tasks_container = ui.column().classes('w-full gap-4')
            
            # Charger les tâches
            self.refresh_tasks()
            
            # Auto-refresh toutes les 2 secondes
            self.refresh_timer = ui.timer(2.0, self.refresh_tasks)
    
    def refresh_tasks(self) -> None:
        """Actualise l'affichage des tâches."""
        if not self.tasks_container:
            return
        
        self.tasks_container.clear()
        
        with self.tasks_container:
            tasks = sending_tasks_manager.get_all_tasks()
            
            if not tasks:
                # Aucune tâche
                with ui.card().classes('w-full p-8 card-modern text-center'):
                    ui.label('📭').classes('text-5xl mb-3').style('color: var(--secondary); opacity: 0.3;')
                    ui.label('Aucun envoi en cours').classes('text-xl font-bold mb-2').style(
                        'color: var(--text-secondary);'
                    )
                    ui.label('Les envois que vous lancez apparaîtront ici.').classes('text-sm').style(
                        'color: var(--text-secondary); opacity: 0.7;'
                    )
            else:
                # Séparer les tâches en cours et terminées
                active_tasks = [t for t in tasks if t.is_running]
                finished_tasks = [t for t in tasks if not t.is_running]
                
                # Tâches en cours
                if active_tasks:
                    ui.label(f'🔄 En cours ({len(active_tasks)})').classes(
                        'text-lg font-bold mb-2'
                    ).style('color: var(--primary);')
                    
                    for task in active_tasks:
                        self._render_task_card(task, is_active=True)
                
                # Tâches terminées
                if finished_tasks:
                    ui.label(f'✓ Terminées ({len(finished_tasks)})').classes(
                        'text-lg font-bold mb-2 mt-6'
                    ).style('color: var(--success);')
                    
                    for task in finished_tasks:
                        self._render_task_card(task, is_active=False)
    
    def _render_task_card(self, task: SendingTask, is_active: bool) -> None:
        """Rend une carte de tâche."""
        # Couleur selon le statut
        if task.status == "en_cours":
            border_color = "var(--primary)"
            bg_color = "rgba(30, 58, 138, 0.05)"
            status_icon = "🔄"
            status_text = "En cours"
            status_color = "var(--primary)"
        elif task.status == "terminé":
            border_color = "var(--success)"
            bg_color = "rgba(16, 185, 129, 0.05)"
            status_icon = "✅"
            status_text = "Terminé"
            status_color = "var(--success)"
        else:  # annulé
            border_color = "var(--danger)"
            bg_color = "rgba(239, 68, 68, 0.05)"
            status_icon = "❌"
            status_text = "Annulé"
            status_color = "var(--danger)"
        
        with ui.card().classes('w-full p-5 card-modern').style(
            f'border-left: 4px solid {border_color}; background: {bg_color};'
        ):
            # En-tête
            with ui.row().classes('w-full items-center gap-3 mb-3'):
                ui.label(status_icon).classes('text-2xl')
                with ui.column().classes('flex-1 gap-1'):
                    ui.label(task.account_name).classes('text-lg font-bold').style(
                        'color: var(--text-primary);'
                    )
                    ui.label(f'ID: {task.task_id}').classes('text-xs').style(
                        'color: var(--text-secondary);'
                    )
                
                ui.label(status_text).classes('px-3 py-1 rounded font-semibold text-sm').style(
                    f'background: {bg_color}; color: {status_color}; border: 1px solid {border_color};'
                )
            
            # Statistiques
            with ui.row().classes('w-full gap-6 mb-3'):
                with ui.column().classes('gap-1'):
                    ui.label('Groupes').classes('text-xs').style('color: var(--text-secondary);')
                    ui.label(str(task.group_count)).classes('text-lg font-bold').style(
                        'color: var(--text-primary);'
                    )
                
                with ui.column().classes('gap-1'):
                    ui.label('Dates').classes('text-xs').style('color: var(--text-secondary);')
                    ui.label(str(task.date_count)).classes('text-lg font-bold').style(
                        'color: var(--text-primary);'
                    )
                
                with ui.column().classes('gap-1'):
                    ui.label('Messages').classes('text-xs').style('color: var(--text-secondary);')
                    ui.label(f'{task.sent}/{task.total_messages}').classes('text-lg font-bold').style(
                        'color: var(--success);'
                    )
                
                if len(task.failed_groups) > 0:
                    with ui.column().classes('gap-1'):
                        ui.label('Groupes exclus').classes('text-xs').style('color: var(--text-secondary);')
                        ui.label(str(len(task.failed_groups))).classes('text-lg font-bold').style(
                            'color: var(--warning);'
                        )
                        ui.label('(envoi programmé désactivé)').classes('text-xs').style(
                            'color: var(--text-secondary); font-style: italic;'
                        )
            
            # ⏰ Indicateur d'attente FloodWait
            if is_active and task.is_waiting and task.waiting_until:
                wait_until_str = task.waiting_until.strftime('%H:%M:%S')
                with ui.row().classes('w-full items-center gap-3 mb-3 p-3 rounded').style(
                    'background: rgba(251, 191, 36, 0.1); border: 1px solid var(--warning);'
                ):
                    ui.label('⏰').classes('text-2xl')
                    with ui.column().classes('gap-1'):
                        ui.label('Respect des limites Telegram').classes('text-sm font-bold').style(
                            'color: var(--warning);'
                        )
                        ui.label(f'Reprise automatique à {wait_until_str}').classes('text-xs').style(
                            'color: var(--text-secondary);'
                        )
                    ui.spinner(size='sm', color='warning')
            
            # Barre de progression
            if is_active:
                with ui.row().classes('w-full items-center gap-3 mb-3'):
                    ui.linear_progress(value=task.progress_percent / 100).classes('flex-1')
                    ui.label(f'{task.progress_percent:.1f}%').classes('font-bold').style(
                        'color: var(--primary);'
                    )
            
            # Actions
            with ui.row().classes('w-full gap-3'):
                # Heure de début
                started_str = task.started_at.strftime('%H:%M:%S')
                ui.label(f'⏱ Début: {started_str}').classes('text-sm').style(
                    'color: var(--text-secondary);'
                )
                
                # Heure de fin si terminé
                if task.finished_at:
                    finished_str = task.finished_at.strftime('%H:%M:%S')
                    duration = (task.finished_at - task.started_at).total_seconds()
                    ui.label(f'✓ Fin: {finished_str} ({int(duration)}s)').classes('text-sm').style(
                        'color: var(--text-secondary);'
                    )
                
                ui.space()
                
                # Bouton annuler si en cours
                if is_active:
                    def make_cancel(task_id: str):
                        def cancel():
                            async def on_confirm():
                                if sending_tasks_manager.cancel_task(task_id):
                                    notify('✓ Envoi annulé', type='warning')
                                    self.refresh_tasks()
                                else:
                                    notify('❌ Impossible d\'annuler', type='negative')
                            
                            confirm = ConfirmDialog(
                                title='⚠️ Annuler l\'envoi ?',
                                message='Les messages déjà envoyés resteront programmés.',
                                on_confirm=on_confirm,
                                confirm_text='Annuler l\'envoi',
                                is_danger=True
                            )
                            confirm.show()
                        return cancel
                    
                    ui.button(
                        '✕ Annuler',
                        on_click=make_cancel(task.task_id)
                    ).props('flat dense').style('color: var(--danger);')
                else:
                    # Bouton supprimer si terminé
                    def make_delete(task_id: str):
                        def delete():
                            sending_tasks_manager.remove_task(task_id)
                            notify('✓ Tâche supprimée', type='info')
                            self.refresh_tasks()
                        return delete
                    
                    ui.button(
                        '🗑️ Supprimer',
                        on_click=make_delete(task.task_id)
                    ).props('flat dense').style('color: var(--secondary);')

