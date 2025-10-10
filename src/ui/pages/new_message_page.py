"""
Page de création de nouveaux messages programmés.
"""
import asyncio
import os
from datetime import datetime, timedelta, date
from pathlib import Path
from typing import List, Dict, Set, Optional
from nicegui import ui

from core.telegram.manager import TelegramManager
from core.session_manager import SessionManager
from services.message_service import MessageService
from services.dialog_service import DialogService
from ui.components.calendar import CalendarWidget
from utils.logger import get_logger
from utils.constants import (
    ICON_MESSAGE, ICON_CALENDAR, ICON_FILE, ICON_SUCCESS,
    MSG_NO_CONNECTED_ACCOUNT, MSG_SELECT_ACCOUNT, MSG_SELECT_GROUP,
    MSG_ENTER_MESSAGE, MSG_SELECT_DATE, FILE_ICONS
)
from utils.validators import validate_message

logger = get_logger()


class NewMessagePage:
    """Page de création de nouveaux messages."""
    
    def __init__(self, telegram_manager: TelegramManager):
        """
        Initialise la page.
        
        Args:
            telegram_manager: Gestionnaire de comptes Telegram
        """
        self.telegram_manager = telegram_manager
        self.session_manager = SessionManager()
        
        # État de l'application
        self.state = {
            'current_step': 1,
            'selected_account': None,
            'selected_groups': [],
            'all_groups': [],
            'filtered_groups': [],
            'message': '',
            'file_path': None,
            'selected_dates': [],
        }
        
        # Conteneurs UI
        self.steps_container: Optional[ui.column] = None
        self.groups_container: Optional[ui.column] = None
        self.counter_label: Optional[ui.label] = None
        self.calendar_widget: Optional[CalendarWidget] = None
        self.selected_times_checkboxes: List = []
        self.temp_times: List[str] = []
    
    def render(self) -> None:
        """Rend la page."""
        with ui.column().classes('w-full h-full gap-6 p-8').style('overflow: hidden;'):
            # En-tête
            with ui.row().classes('items-center gap-3 mb-2'):
                ui.label(ICON_MESSAGE).classes('text-4xl').style('color: var(--primary);')
                ui.label('Nouveau Message').classes('text-3xl font-bold').style(
                    'color: var(--text-primary);'
                )
            
            ui.label('Créez et programmez vos messages Telegram').classes('text-sm').style(
                'color: var(--text-secondary);'
            )
            ui.separator().style('background: var(--border); height: 1px; border: none; margin: 16px 0;')
            
            # Container pour les étapes
            self.steps_container = ui.column().classes('w-full flex-1').style('overflow: visible;')
            self.render_steps()
    
    def render_steps(self) -> None:
        """Rend l'interface par étapes."""
        self.steps_container.clear()
        
        with self.steps_container:
            # Indicateur d'étapes
            self._render_step_indicator()
            
            # Contenu de l'étape actuelle
            step = self.state['current_step']
            if step == 1:
                self._render_step_account()
            elif step == 2:
                self._render_step_groups()
            elif step == 3:
                self._render_step_message()
            elif step == 4:
                self._render_step_schedule()
    
    def _render_step_indicator(self) -> None:
        """Rend l'indicateur d'étapes."""
        step_labels = ['Compte', 'Groupes', 'Message', 'Dates']
        
        with ui.card().classes('w-full p-4 mb-4 card-modern'):
            with ui.row().classes('w-full items-center justify-around'):
                for i in range(1, 5):
                    current = self.state['current_step']
                    
                    if i == current:
                        style = 'background: var(--primary); color: white; box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);'
                        label_class = 'font-bold text-base'
                    elif i < current:
                        style = 'background: var(--success); color: white;'
                        label_class = 'font-semibold text-sm'
                    else:
                        style = 'background: #e2e8f0; color: var(--text-secondary);'
                        label_class = 'text-sm'
                    
                    with ui.column().classes('items-center gap-2'):
                        ui.label(f'{i}').classes(
                            f'w-10 h-10 rounded-full flex items-center justify-center {label_class}'
                        ).style(style)
                        ui.label(step_labels[i-1]).classes('text-xs font-medium').style(
                            'color: var(--text-secondary);'
                        )
    
    def _render_step_account(self) -> None:
        """Étape 1 : Sélection du compte."""
        with ui.card().classes('w-full p-6 card-modern'):
            ui.label('① Sélectionnez le compte').classes('text-2xl font-bold mb-4').style(
                'color: var(--text-primary);'
            )
            
            accounts = self.telegram_manager.list_accounts()
            connected = [acc for acc in accounts if acc.get('is_connected', False)]
            
            if not connected:
                with ui.card().classes('p-4').style(
                    'background: #fee2e2; border-left: 3px solid var(--danger);'
                ):
                    ui.label(f'✕ {MSG_NO_CONNECTED_ACCOUNT}').classes('font-bold').style(
                        'color: #991b1b;'
                    )
            else:
                with ui.column().classes('w-full gap-2 custom-scrollbar').style(
                    'max-height: 473px; overflow-y: auto; padding-right: 8px;'
                ):
                    for account in connected:
                        self._render_account_card(account)
                
                with ui.row().classes('w-full justify-end mt-4'):
                    async def next_step() -> None:
                        if not self.state['selected_account']:
                            ui.notify(MSG_SELECT_ACCOUNT, type='warning')
                            return
                        
                        # Charger les groupes
                        ui.notify('Chargement des groupes...', type='info')
                        account = self.telegram_manager.get_account(self.state['selected_account'])
                        
                        if account:
                            dialogs = await DialogService.get_dialogs(account)
                            self.state['all_groups'] = dialogs
                            self.state['filtered_groups'] = dialogs.copy()
                            self.state['selected_groups'] = []
                            ui.notify(f'{len(dialogs)} groupe(s) chargé(s)', type='positive')
                            self.state['current_step'] = 2
                            self.render_steps()
                    
                    ui.button('→ Suivant', on_click=next_step).classes('btn-primary')
    
    def _render_account_card(self, account: dict) -> None:
        """Rend une carte de compte sélectionnable."""
        session_id = account['session_id']
        is_selected = self.state['selected_account'] == session_id
        
        card_class = 'w-full p-3 cursor-pointer mb-2 card-modern'
        if is_selected:
            card_style = 'border: 2px solid var(--primary); background: rgba(30, 58, 138, 0.05);'
            icon, icon_color = '●', 'var(--primary)'
        else:
            card_style = 'border: 1px solid var(--border);'
            icon, icon_color = '○', 'var(--text-secondary)'
        
        def select_account() -> None:
            self.state['selected_account'] = session_id
            ui.notify(f'Compte sélectionné: {account["account_name"]}', type='info')
            self.render_steps()
        
        with ui.card().classes(card_class).style(card_style).on('click', select_account):
            with ui.row().classes('w-full items-center gap-3'):
                ui.label(icon).classes('text-lg').style(f'color: {icon_color};')
                with ui.column().classes('flex-1 gap-1'):
                    ui.label(account['account_name']).classes('text-base font-semibold').style(
                        f'color: {icon_color if is_selected else "var(--text-primary)"};'
                    )
                    ui.label(account['phone']).classes('text-xs').style('color: var(--text-secondary);')
                ui.html('<span class="status-badge status-online"></span>', sanitize=False)
    
    def _render_step_groups(self) -> None:
        """Étape 2 : Sélection des groupes."""
        with ui.card().classes('w-full p-6 card-modern'):
            ui.label('② Sélectionnez les groupes').classes('text-2xl font-bold mb-4').style(
                'color: var(--text-primary);'
            )
            
            # Barre de recherche
            with ui.row().classes('w-full gap-3 mb-4'):
                ui.input(
                    'Rechercher un groupe...',
                    on_change=self._on_search_change
                ).classes('flex-1').props('outlined dense')
                
                ui.button('✓ Tout', on_click=self._select_all_groups).props('outline dense size=sm').style(
                    'color: var(--success); border-color: var(--success);'
                )
                ui.button('○ Rien', on_click=self._deselect_all_groups).props('outline dense size=sm').style(
                    'color: var(--secondary); border-color: var(--secondary);'
                )
            
            # Compteur
            self.counter_label = ui.label().classes('text-sm font-semibold mb-3 px-3 py-2 rounded-lg')
            self._update_counter()
            
            # Liste des groupes
            self.groups_container = ui.column().classes('w-full gap-2 custom-scrollbar').style(
                'max-height: 333px; overflow-y: auto; padding-right: 8px;'
            )
            self._update_groups_list()
            
            # Navigation
            with ui.row().classes('w-full justify-between mt-4'):
                ui.button('← Retour', on_click=self._go_back).props('flat size=md').style(
                    'color: var(--secondary);'
                )
                
                async def next_step() -> None:
                    if not self.state['selected_groups']:
                        ui.notify(MSG_SELECT_GROUP, type='warning')
                        return
                    
                    # Charger le message prédéfini
                    settings = self.session_manager.get_account_settings(self.state['selected_account'])
                    if settings.get('default_message'):
                        self.state['message'] = settings['default_message']
                    
                    self.state['current_step'] = 3
                    self.render_steps()
                
                ui.button('→ Suivant', on_click=next_step).classes('btn-primary')
    
    def _render_step_message(self) -> None:
        """Étape 3 : Composition du message."""
        with ui.card().classes('w-full p-6 card-modern'):
            ui.label('③ Composez votre message').classes('text-2xl font-bold mb-4').style(
                'color: var(--text-primary);'
            )
            
            # Zone de texte
            ui.textarea(
                'Message',
                value=self.state['message'],
                on_change=lambda e: self.state.update({'message': e.value})
            ).classes('w-full').props('outlined rows=6')
            
            # Compteur de caractères
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label(f"Caractères: {len(self.state['message'])}").classes('text-sm').style(
                    'color: var(--text-secondary);'
                )
            
            # Upload de fichier
            self._render_file_upload()
            
            # Navigation
            with ui.row().classes('w-full justify-between mt-4'):
                ui.button('← Retour', on_click=self._go_back).props('flat size=md').style(
                    'color: var(--secondary);'
                )
                
                async def next_step() -> None:
                    is_valid, error_msg = validate_message(self.state['message'])
                    if not is_valid:
                        ui.notify(error_msg, type='warning')
                        return
                    
                    self.state['current_step'] = 4
                    self.render_steps()
                
                ui.button('→ Suivant', on_click=next_step).classes('btn-primary')
    
    def _render_file_upload(self) -> None:
        """Rend la zone d'upload de fichier."""
        with ui.card().classes('w-full p-4').style(
            'background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 12px;'
        ):
            ui.label(f'{ICON_FILE} Joindre un fichier (optionnel)').classes('font-semibold mb-4')
            
            if not self.state['file_path']:
                # Zone d'upload
                file_input = ui.upload(
                    on_upload=self._handle_file_upload,
                    auto_upload=True
                ).classes('w-full')
            else:
                # Fichier sélectionné
                self._render_selected_file()
    
    def _handle_file_upload(self, e) -> None:
        """Gère l'upload d'un fichier."""
        try:
            # Créer le dossier temp
            temp_dir = Path(__file__).parent.parent.parent.parent / 'temp'
            temp_dir.mkdir(exist_ok=True)
            
            # Sauvegarder le fichier
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_name = e.name
            file_path = temp_dir / f"{timestamp}_{file_name}"
            
            with open(file_path, 'wb') as f:
                f.write(e.content.read())
            
            self.state['file_path'] = str(file_path)
            
            file_size = file_path.stat().st_size
            size_text = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
            ui.notify(f'{ICON_SUCCESS} Fichier ajouté: {file_name} ({size_text})', type='positive')
            
            self.render_steps()
            
        except Exception as ex:
            logger.error(f'Erreur upload: {ex}')
            ui.notify(f'❌ Erreur: {str(ex)}', type='negative')
    
    def _render_selected_file(self) -> None:
        """Affiche le fichier sélectionné."""
        if not self.state['file_path']:
            return
        
        file_path = Path(self.state['file_path'])
        if not file_path.exists():
            self.state['file_path'] = None
            self.render_steps()
            return
        
        file_name = file_path.name
        file_size = file_path.stat().st_size
        size_text = f"{file_size / 1024:.1f} KB" if file_size < 1024*1024 else f"{file_size / (1024*1024):.1f} MB"
        
        # Icône
        ext = file_path.suffix.lower()
        icon = FILE_ICONS.get(ext, FILE_ICONS['default'])
        
        with ui.card().classes('w-full p-3').style(
            'background: rgba(16, 185, 129, 0.1); border: 2px solid var(--success);'
        ):
            with ui.row().classes('w-full items-center gap-3'):
                ui.label(icon).classes('text-2xl')
                with ui.column().classes('flex-1'):
                    ui.label('Fichier joint').classes('text-xs font-semibold').style('color: var(--success);')
                    ui.label(file_name).classes('text-sm font-medium')
                    ui.label(size_text).classes('text-xs').style('color: var(--text-secondary);')
                
                def remove_file() -> None:
                    try:
                        if self.state['file_path']:
                            Path(self.state['file_path']).unlink(missing_ok=True)
                    except:
                        pass
                    self.state['file_path'] = None
                    ui.notify('Fichier supprimé', type='info')
                    self.render_steps()
                
                ui.button('✕', on_click=remove_file).props('outline dense size=sm').style(
                    'color: var(--danger);'
                )
    
    def _render_step_schedule(self) -> None:
        """Étape 4 : Programmation des dates."""
        with ui.card().classes('w-full p-6 card-modern'):
            ui.label('④ Programmez les dates et heures').classes('text-2xl font-bold mb-4')
            
            with ui.row().classes('w-full gap-4').style('max-height: 483px; overflow: hidden;'):
                # Colonne 1: Calendrier
                with ui.column().classes('gap-3').style('flex: 1; max-height: 483px; overflow-y: auto;'):
                    with ui.card().classes('p-3 card-modern'):
                        ui.label(f'{ICON_CALENDAR} Calendrier').classes('font-bold mb-2 text-sm')
                        
                        # Calendrier widget
                        selected_dates_set: Set[date] = set()
                        
                        def on_date_change(dates: Set[date]) -> None:
                            nonlocal selected_dates_set
                            selected_dates_set = dates
                            self._apply_times_to_dates(dates)
                        
                        self.calendar_widget = CalendarWidget(
                            on_date_change=on_date_change,
                            selected_dates=selected_dates_set
                        )
                        self.calendar_widget.render()
                    
                    # Actions rapides
                    with ui.card().classes('p-3 card-modern'):
                        ui.label('Actions rapides').classes('font-semibold mb-2 text-sm')
                        with ui.row().classes('w-full gap-2'):
                            ui.button('📅 Semaine', on_click=self._add_week).props('outline dense').style('flex: 1;')
                            ui.button('📅 Mois', on_click=self._add_month).props('outline dense').style('flex: 1;')
                            ui.button('🗑️ Effacer', on_click=self._clear_dates).props('outline dense').style('flex: 1;')
                
                # Colonne 2: Horaires
                with ui.column().classes('gap-3').style('flex: 1; max-height: 483px; overflow-y: auto;'):
                    self._render_time_selection()
                
                # Colonne 3: Dates sélectionnées
                with ui.column().classes('gap-3').style('flex: 1; max-height: 483px; overflow-y: auto;'):
                    self._render_selected_dates()
            
            # Navigation
            with ui.row().classes('w-full justify-between mt-4'):
                ui.button('← Précédent', on_click=self._go_back).props('flat size=md')
                ui.button('✓ Envoyer', on_click=self._send_messages).classes('btn-primary').style(
                    'background: var(--success);'
                )
    
    def _render_time_selection(self) -> None:
        """Rend la sélection d'horaires."""
        # À implémenter selon vos besoins
        pass
    
    def _render_selected_dates(self) -> None:
        """Rend la liste des dates sélectionnées."""
        # À implémenter selon vos besoins
        pass
    
    # Méthodes utilitaires
    
    def _on_search_change(self, e) -> None:
        """Filtre les groupes."""
        search_text = e.value
        self.state['filtered_groups'] = DialogService.filter_dialogs(
            self.state['all_groups'],
            search_text
        )
        self._update_groups_list()
        self._update_counter()
    
    def _select_all_groups(self) -> None:
        """Sélectionne tous les groupes filtrés."""
        for group in self.state['filtered_groups']:
            if group['id'] not in self.state['selected_groups']:
                self.state['selected_groups'].append(group['id'])
        self._update_groups_list()
        self._update_counter()
    
    def _deselect_all_groups(self) -> None:
        """Désélectionne tous les groupes filtrés."""
        filtered_ids = [g['id'] for g in self.state['filtered_groups']]
        self.state['selected_groups'] = [
            gid for gid in self.state['selected_groups']
            if gid not in filtered_ids
        ]
        self._update_groups_list()
        self._update_counter()
    
    def _update_groups_list(self) -> None:
        """Met à jour la liste des groupes."""
        if not self.groups_container:
            return
        
        self.groups_container.clear()
        
        with self.groups_container:
            for group in self.state['filtered_groups']:
                is_selected = group['id'] in self.state['selected_groups']
                
                def make_toggle(gid: int):
                    def toggle() -> None:
                        if gid in self.state['selected_groups']:
                            self.state['selected_groups'].remove(gid)
                        else:
                            self.state['selected_groups'].append(gid)
                        self._update_groups_list()
                        self._update_counter()
                    return toggle
                
                style = 'background: rgba(16, 185, 129, 0.05); border: 2px solid var(--success);' if is_selected else ''
                
                with ui.card().classes('w-full p-4 cursor-pointer card-modern').style(style).on(
                    'click', make_toggle(group['id'])
                ):
                    with ui.row().classes('w-full items-center gap-3'):
                        icon = '●' if is_selected else '○'
                        ui.label(icon).classes('text-xl')
                        ui.label(group['title']).classes('text-sm font-medium flex-1')
                        if is_selected:
                            ui.label('✓').classes('text-sm font-bold').style('color: var(--success);')
    
    def _update_counter(self) -> None:
        """Met à jour le compteur de sélection."""
        if not self.counter_label:
            return
        
        total = len(self.state['filtered_groups'])
        selected = DialogService.count_selected(
            self.state['filtered_groups'],
            self.state['selected_groups']
        )
        
        if selected == 0:
            style = 'background: rgba(239, 68, 68, 0.1); color: var(--danger);'
            text = f'○ Aucun groupe sélectionné ({total} disponibles)'
        elif selected == total:
            style = 'background: rgba(16, 185, 129, 0.1); color: var(--success);'
            text = f'✓ Tous les groupes sélectionnés ({selected}/{total})'
        else:
            style = 'background: rgba(30, 58, 138, 0.1); color: var(--primary);'
            text = f'● {selected} groupe(s) sélectionné(s) sur {total}'
        
        self.counter_label.set_text(text)
        self.counter_label.style(style)
    
    def _go_back(self) -> None:
        """Retourne à l'étape précédente."""
        if self.state['current_step'] > 1:
            self.state['current_step'] -= 1
            self.render_steps()
    
    def _apply_times_to_dates(self, dates: Set[date]) -> None:
        """Applique les horaires aux dates sélectionnées."""
        # À implémenter selon vos besoins
        pass
    
    def _add_week(self) -> None:
        """Ajoute une semaine de dates."""
        if self.calendar_widget:
            self.calendar_widget.add_week()
    
    def _add_month(self) -> None:
        """Ajoute un mois de dates."""
        if self.calendar_widget:
            self.calendar_widget.add_month()
    
    def _clear_dates(self) -> None:
        """Efface toutes les dates."""
        if self.calendar_widget:
            self.calendar_widget.clear_dates()
        self.state['selected_dates'] = []
        ui.notify('Toutes les dates supprimées', type='info')
        self.render_steps()
    
    async def _send_messages(self) -> None:
        """Envoie les messages programmés."""
        if not self.state['selected_dates']:
            ui.notify(MSG_SELECT_DATE, type='warning')
            return
        
        # À implémenter: utiliser MessageService.send_scheduled_messages
        ui.notify('Envoi en cours...', type='info')
        
        # Réinitialiser après envoi
        self.state['current_step'] = 1
        self.state['selected_account'] = None
        self.state['selected_groups'] = []
        self.state['message'] = ''
        self.state['file_path'] = None
        self.state['selected_dates'] = []
        self.render_steps()

