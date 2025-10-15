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
from services.sending_tasks_manager import sending_tasks_manager
from ui.components.svg_icons import svg
from ui.components.calendar import CalendarWidget
from utils.logger import get_logger
from utils.constants import (
    ICON_MESSAGE, ICON_CALENDAR, ICON_FILE, ICON_SUCCESS,
    MSG_NO_CONNECTED_ACCOUNT, MSG_SELECT_ACCOUNT, MSG_SELECT_GROUP,
    MSG_ENTER_MESSAGE, MSG_SELECT_DATE, FILE_ICONS,
    MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
)
from utils.validators import validate_message
from utils.paths import get_temp_dir
from utils.notification_manager import notify
from ui.components.svg_icons import svg

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
            'files': [],  # Liste des fichiers [{name, path, size}]
            'selected_dates': [],
        }
        
        # Le système de notifications est maintenant global
        
        # Conteneurs UI
        self.steps_container: Optional[ui.column] = None
        self.groups_container: Optional[ui.column] = None
        self.counter_label: Optional[ui.label] = None
        
        # Cache pour la recherche de groupes
        self._last_groups_search = ""
    
        self.calendar_widget: Optional[CalendarWidget] = None
    
    def render(self) -> None:
        """Rend la page."""
        with ui.column().classes('w-full gap-6 p-8'):
            # En-tête
            with ui.row().classes('items-center gap-3 mb-2'):
                ui.html(svg('edit', 40, 'var(--primary)'))
                ui.label('Nouveau Message').classes('text-3xl font-bold').style(
                    'color: var(--text-primary);'
                )
            
            ui.label('Créez et programmez vos messages Telegram').classes('text-sm').style(
                'color: var(--text-secondary);'
            )
            ui.separator().style('background: var(--border); height: 1px; border: none; margin: 16px 0;')
            
            # Container pour les étapes
            self.steps_container = ui.column().classes('w-full')
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
                    ui.label(f'{MSG_NO_CONNECTED_ACCOUNT}').classes('font-bold').style(
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
                            notify(MSG_SELECT_ACCOUNT, type='warning')
                            return
                        
                        # Vérifier si le compte est occupé
                        if sending_tasks_manager.is_account_busy(self.state['selected_account']):
                            notify(
                                'Ce compte envoie déjà des messages. Attendez la fin de l\'envoi pour éviter le rate limit.',
                                type='warning'
                            )
                            return
                        
                        # Charger les groupes
                        notify('Chargement des groupes...', type='info')
                        account = self.telegram_manager.get_account(self.state['selected_account'])
                        
                        if account:
                            dialogs = await DialogService.get_dialogs(account)
                            self.state['all_groups'] = dialogs
                            self.state['filtered_groups'] = dialogs.copy()
                            self.state['selected_groups'] = []
                            notify(f'{len(dialogs)} groupe(s) chargé(s)', type='positive')
                            self.state['current_step'] = 2
                            self.render_steps()
                    
                    ui.button('→ Suivant', on_click=next_step).classes('btn-primary')
    
    def _render_account_card(self, account: dict) -> None:
        """Rend une carte de compte sélectionnable."""
        session_id = account['session_id']
        is_selected = self.state['selected_account'] == session_id
        is_busy = sending_tasks_manager.is_account_busy(session_id)
        
        card_class = 'w-full p-3 mb-2 card-modern'
        
        if is_busy:
            # Compte occupé - grisé et non cliquable
            card_class += ' cursor-not-allowed'
            card_style = 'border: 1px solid var(--border); background: rgba(128, 128, 128, 0.1); opacity: 0.6;'
            icon, icon_color = 'schedule', 'var(--warning)'
        elif is_selected:
            card_class += ' cursor-pointer'
            card_style = 'border: 2px solid var(--primary); background: rgba(30, 58, 138, 0.05);'
            icon, icon_color = 'radio_button_checked', 'var(--primary)'
        else:
            card_class += ' cursor-pointer'
            card_style = 'border: 1px solid var(--border);'
            icon, icon_color = 'radio_button_unchecked', 'var(--text-secondary)'
        
        def select_account() -> None:
            if is_busy:
                notify('Ce compte est occupé par un envoi en cours', type='warning')
                return
            self.state['selected_account'] = session_id
            
            # CORRECTION : Recharger les settings du compte sélectionné
            # Recharger l'index depuis le fichier pour avoir les dernières modifications
            self.session_manager.sessions_index = self.session_manager._load_index()
            settings = self.session_manager.get_account_settings(session_id)
            
            # Charger le message par défaut du compte
            if settings.get('default_message'):
                self.state['message'] = settings['default_message']
            else:
                self.state['message'] = ''
            
            notify(f'Compte sélectionné: {account["account_name"]}', type='info')
            self.render_steps()
        
        card = ui.card().classes(card_class).style(card_style)
        if not is_busy:
            card.on('click', select_account)
        
        with card:
            with ui.row().classes('w-full items-center gap-3'):
                ui.html(svg(icon, 24, icon_color))
                with ui.column().classes('flex-1 gap-1'):
                    ui.label(account['account_name']).classes('text-base font-semibold').style(
                        f'color: {icon_color if is_selected else "var(--text-primary)"};'
                    )
                    ui.label(account['phone']).classes('text-xs').style('color: var(--text-secondary);')
                
                if is_busy:
                    ui.label('Envoi en cours...').classes('text-xs font-semibold px-2 py-1 rounded').style(
                        'background: rgba(251, 191, 36, 0.2); color: var(--warning);'
                    )
                else:
                    ui.html('<span class="status-badge status-online"></span>')
    
    def _render_step_groups(self) -> None:
        """Étape 2 : Sélection des groupes."""
        with ui.card().classes('w-full p-6 card-modern'):
            ui.label('② Sélectionnez les groupes').classes('text-2xl font-bold mb-4').style(
                'color: var(--text-primary);'
            )
            
            # Barre de recherche
            with ui.row().classes('w-full gap-3 mb-4'):
                # Input HTML natif
                search_html = '''
                <input 
                    type="text"
                    id="search_groups_native"
                    placeholder="Rechercher un groupe..."
                    style="
                        width: 100%;
                        height: 48px;
                        background: #ffffff;
                        border: 2px solid #d1d5db;
                        border-radius: 8px;
                        font-size: 16px;
                        padding: 12px 16px;
                        box-sizing: border-box;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    "
                    oninput="window.searchGroups()"
                />
                '''
                ui.html(search_html).classes('flex-1')
                
                # CORRECTION : Créer fonction JavaScript avec debounce
                ui.run_javascript('''
                    let groupSearchTimeout;
                    window.searchGroups = function() {
                        clearTimeout(groupSearchTimeout);
                        groupSearchTimeout = setTimeout(() => {
                            emitEvent('group_search_changed', {});
                        }, 300);  // Debounce 300ms
                    };
                ''')
                
                # Handler Python pour l'événement
                async def on_group_search_event(e):
                    await self._on_search_change_native()
                
                ui.on('group_search_changed', on_group_search_event)
                
                with ui.button(on_click=self._select_all_groups).props('outline dense size=sm').style(
                    'color: var(--success); border-color: var(--success);'
                ):
                    ui.html(svg('check_circle', 18, '#059669'))
                    ui.label('Tout').classes('ml-1')
                with ui.button(on_click=self._deselect_all_groups).props('outline dense size=sm').style(
                    'color: var(--secondary); border-color: var(--secondary);'
                ):
                    ui.html(svg('remove_circle', 18, 'var(--secondary)'))
                    ui.label('Rien').classes('ml-1')
            
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
                        notify(MSG_SELECT_GROUP, type='warning')
                        return
                    
                    self.state['current_step'] = 3
                    self.render_steps()
                
                ui.button('→ Suivant', on_click=next_step).classes('btn-primary')
    
    def _render_step_message(self) -> None:
        """Étape 3 : Composition du message."""
        with ui.card().classes('w-full p-6 card-modern'):
            ui.label('③ Composez votre message').classes('text-2xl font-bold mb-4').style(
                'color: var(--text-primary);'
            )
            
            # CORRECTION : Charger le message prérempli avec les derniers paramètres
            if self.state['selected_account']:
                # Recharger l'index pour avoir les dernières modifications
                self.session_manager.sessions_index = self.session_manager._load_index()
                settings = self.session_manager.get_account_settings(self.state['selected_account'])
                if settings.get('default_message') and not self.state.get('message'):
                    self.state['message'] = settings['default_message']
            
            # Zone de texte - Textarea HTML natif (agrandie)
            message_value = self.state.get('message', '')
            message_html = f'''
            <textarea 
                id="message_textarea_native"
                placeholder="Message"
                rows="12"
                style="
                    width: 100%;
                    min-height: 300px;
                    background: #ffffff;
                    border: 2px solid #d1d5db;
                    border-radius: 8px;
                    font-size: 16px;
                    padding: 14px 16px;
                    resize: vertical;
                    box-sizing: border-box;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                "
            >{message_value}</textarea>
            '''
            ui.html(message_html).classes('w-full')
            # Mettre à jour le state périodiquement
            ui.timer(1.0, lambda: asyncio.create_task(self._update_message_state()), once=False)
            
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
                    # Récupérer le message actuel via JavaScript
                    try:
                        message = await ui.run_javascript('document.getElementById("message_textarea_native").value', timeout=1.0) or ""
                        self.state['message'] = str(message)
                    except Exception:
                        pass
                    
                    is_valid, error_msg = validate_message(self.state['message'])
                    if not is_valid:
                        notify(error_msg, type='warning')
                        return
                    
                    self.state['current_step'] = 4
                    self.render_steps()
                
                ui.button('→ Suivant', on_click=next_step).classes('btn-primary')
    
    def _render_file_upload(self) -> None:
        """Zone d'upload simple et propre."""
        with ui.card().classes('w-full p-4'):
            with ui.row().classes('items-center gap-2 mb-3'):
                ui.html(svg('attach_file', 22, 'var(--text-primary)'))
                ui.label('Images (optionnel)').classes('text-lg font-bold')
            
            # Upload simple
            def handle_upload(e):
                try:
                    file_name = e.name if hasattr(e, 'name') else 'fichier'
                    
                    if hasattr(e, 'content'):
                        content = e.content.read()
                        e.content.seek(0)
                        file_size = len(content)
                    else:
                        content = e.content_bytes if hasattr(e, 'content_bytes') else b''
                        file_size = len(content)
                    
                    if file_size > MAX_FILE_SIZE_BYTES:
                        notify(f'{file_name} trop volumineux (max {MAX_FILE_SIZE_MB} MB)', type='negative')
                        return
                    
                    # Sauvegarder
                    temp_dir = get_temp_dir()
                    
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    file_path = temp_dir / f"{timestamp}_{file_name}"
                    
                    with open(file_path, 'wb') as f:
                        f.write(content)
                    
                    # Ajouter à la liste
                    self.state['files'].append({
                        'name': file_name,
                        'path': str(file_path),
                        'size': file_size
                    })
                    
                    notify(f'{file_name} ajoutée', type='positive')
                    
                except Exception as ex:
                    logger.error(f'Erreur upload: {ex}')
                    notify(f'Erreur upload', type='negative')
            
            # Bouton d'upload avec label personnalisé
            ui.upload(
                on_upload=handle_upload,
                auto_upload=True,
                multiple=True
            ).props('accept="image/*" label="Ajouter des fichiers"').classes('w-full')
            
            ui.label(f'Max {MAX_FILE_SIZE_MB} MB par image').classes('text-xs text-gray-500 mt-2')
            
            # Affichage simple des fichiers
            if self.state['files']:
                ui.label(f'Images sélectionnées ({len(self.state["files"])})').classes('text-sm font-semibold mt-3 mb-2')
                for file_info in self.state['files']:
                    size_kb = file_info['size'] / 1024
                    with ui.row().classes('w-full items-center justify-between p-2 bg-gray-50 rounded mb-1'):
                        with ui.row().classes('items-center gap-2'):
                            ui.html(svg('image', 20, '#6b7280'))
                            ui.label(file_info['name']).classes('text-sm')
                            ui.label(f"{size_kb:.1f} KB").classes('text-xs text-gray-500')
                        ui.html(svg('check_circle', 20, '#10b981'))
            else:
                ui.label('Aucune image').classes('text-sm text-gray-500 mt-2')
    
    
    
    def _render_step_schedule(self) -> None:
        """Étape 4 : Programmation complète des dates et heures."""
        # Réinitialiser complètement les conteneurs à chaque rendu
        self.schedule_containers = {}
        
        with ui.card().classes('w-full p-6'):
            ui.label('④ Programmez les dates et heures').classes('text-2xl font-bold mb-6')
            
            # Layout en 3 colonnes
            with ui.row().classes('w-full gap-6'):
                
                # === COLONNE 1: CALENDRIER ===
                with ui.column().classes('flex-1 gap-4'):
                    with ui.card().classes('p-4'):
                        ui.label('📅 Sélection des dates').classes('text-lg font-bold mb-4')
                        
                        # Conteneur pour le calendrier
                        self.schedule_containers['calendar_container'] = ui.column().classes('gap-2')
                        self._render_calendar_to_container(self.schedule_containers['calendar_container'])
                        
                        # Raccourcis de sélection
                        ui.label('Raccourcis rapides:').classes('font-semibold mb-2 mt-4')
                        with ui.row().classes('gap-2 flex-wrap'):
                            ui.button('1 SEMAINE', on_click=lambda: self._select_date_range(7)).props('outline size=sm')
                            ui.button('2 SEMAINES', on_click=lambda: self._select_date_range(14)).props('outline size=sm')
                            ui.button('1 MOIS', on_click=lambda: self._select_date_range(30)).props('outline size=sm')
                            ui.button('EFFACER TOUT', on_click=self._clear_dates).props('outline size=sm').classes('text-red-500')
                
                # === COLONNE 2: HORAIRES ===
                with ui.column().classes('flex-1 gap-4'):
                    with ui.card().classes('p-4'):
                        with ui.row().classes('items-center gap-2 mb-4'):
                            ui.html(svg('access_time', 22, 'var(--text-primary)'))
                            ui.label('Gestion des horaires').classes('text-lg font-bold')
                        
                        # Horaires par défaut du compte
                        self._render_default_schedules()
                        
                        # Ajout d'horaires personnalisés
                        self._render_custom_schedule_input()
                        
                        # Section des horaires ajoutés manuellement
                        self.schedule_containers['manual_schedules_container'] = ui.column().classes('gap-2')
                        self._render_manual_schedules_to_container(self.schedule_containers['manual_schedules_container'])
                
                # === COLONNE 3: RÉSUMÉ (doublée en largeur et hauteur) ===
                with ui.column().classes('flex-2 gap-4').style('min-height: 600px;'):
                    with ui.card().classes('p-4'):
                        with ui.row().classes('items-center gap-2 mb-4'):
                            ui.html(svg('description', 22, 'var(--text-primary)'))
                            ui.label('Planning final').classes('text-lg font-bold')
                        
                        # Conteneur pour le planning final
                        self.schedule_containers['final_schedule_container'] = ui.column().classes('gap-2')
                        self._render_final_schedule_to_container(self.schedule_containers['final_schedule_container'])
            
            # Navigation
            with ui.row().classes('w-full justify-between mt-4'):
                ui.button('← Retour', on_click=self._go_back).props('flat size=md').style(
                    'color: var(--secondary);'
                )
                
                with ui.button(on_click=self._send_messages).classes('btn-primary'):
                    with ui.row().classes('items-center gap-2'):
                        ui.html(svg('send', 18, 'white'))
                        ui.label('Envoyer')
    
    def _render_calendar_to_container(self, container) -> None:
        """Rend le calendrier dans un conteneur spécifique."""
        # Initialiser les dates sélectionnées si nécessaire
        if 'selected_dates' not in self.state:
            self.state['selected_dates'] = []
        
        # Initialiser le mois affiché
        if 'displayed_month' not in self.state:
            self.state['displayed_month'] = date.today().month
        if 'displayed_year' not in self.state:
            self.state['displayed_year'] = date.today().year
        
        # Utiliser le conteneur passé en paramètre
        with container:
            # Header du calendrier avec navigation
            self._render_calendar_header()
            
            # Grille du calendrier
            self._render_calendar_grid()
            
            # Les dates sélectionnées ne sont plus affichées sous le calendrier
    
    def _render_calendar_header(self) -> None:
        """Rend l'en-tête du calendrier avec navigation."""
        import calendar
        
        month_name = calendar.month_name[self.state['displayed_month']]
        year = self.state['displayed_year']
        
        with ui.row().classes('items-center justify-between w-full mb-4'):
            # Bouton précédent
            ui.button('←', on_click=self._previous_month).props('dense round').classes('w-8 h-8')
            
            # Mois et année
            ui.label(f'{month_name} {year}').classes('text-lg font-bold')
            
            # Bouton suivant
            ui.button('→', on_click=self._next_month).props('dense round').classes('w-8 h-8')
    
    def _render_calendar_grid(self) -> None:
        """Rend la grille du calendrier."""
        import calendar
        
        # Obtenir le calendrier du mois
        cal = calendar.monthcalendar(self.state['displayed_year'], self.state['displayed_month'])
        
        # Jours de la semaine
        with ui.row().classes('w-full text-center text-sm font-semibold text-gray-600 mb-2'):
            for day in ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']:
                ui.label(day).classes('flex-1')
        
        # Grille des jours
        today = date.today()
        
        for week in cal:
            with ui.row().classes('gap-1 mb-1 w-full'):
                for day in week:
                    if day == 0:
                        # Jour vide - même taille que les autres cases
                        ui.label('').classes('w-10 h-10')
                    else:
                        day_date = date(self.state['displayed_year'], self.state['displayed_month'], day)
                        is_selected = day_date in self.state['selected_dates']
                        is_today = day_date == today
                        is_past = day_date <= today
                        
                        # Classes CSS selon l'état - taille fixe pour uniformité
                        classes = 'w-10 h-10 text-center rounded border-2'
                        if is_selected:
                            classes += ' bg-blue-500 text-white border-blue-600'
                        elif is_today:
                            classes += ' bg-yellow-100 text-yellow-800 border-yellow-300'
                        elif is_past:
                            classes += ' bg-gray-100 text-gray-400 border-gray-200 cursor-not-allowed'
                        else:
                            classes += ' bg-white hover:bg-gray-100 border-gray-200 cursor-pointer'
                        
                        # Bouton ou label selon si c'est sélectionnable
                        if is_past:
                            ui.label(str(day)).classes(classes)
                        else:
                            ui.button(
                                str(day),
                                on_click=lambda d=day_date: self._toggle_date(d)
                            ).props('flat').classes(classes)
    
    def _previous_month(self) -> None:
        """Va au mois précédent."""
        if self.state['displayed_month'] == 1:
            self.state['displayed_month'] = 12
            self.state['displayed_year'] -= 1
        else:
            self.state['displayed_month'] -= 1
        
        self._update_calendar_display()
    
    def _next_month(self) -> None:
        """Va au mois suivant."""
        if self.state['displayed_month'] == 12:
            self.state['displayed_month'] = 1
            self.state['displayed_year'] += 1
        else:
            self.state['displayed_month'] += 1
        
        self._update_calendar_display()
    
    def _render_calendar(self) -> None:
        """Rend le calendrier avec sélection multiple (méthode de compatibilité)."""
        # Cette méthode est gardée pour la compatibilité mais ne devrait plus être utilisée
        pass
    
    def _select_date_range(self, days: int) -> None:
        """Sélectionne une plage de dates en supprimant les précédentes."""
        today = date.today()
        # Commencer à partir de demain (aujourd'hui + 1 jour)
        new_dates = [today + timedelta(days=i) for i in range(1, days + 1)]
        
        # Supprimer toutes les dates existantes d'abord
        self.state['selected_dates'] = []
        
        # Ajouter les nouvelles dates
        self.state['selected_dates'] = new_dates
        self.state['selected_dates'].sort()
        
        notify(f'{days} jour(s) sélectionné(s) (à partir de demain)', type='positive')
        # Mettre à jour seulement les conteneurs nécessaires
        self._update_calendar_display()
        self._update_final_schedule_display()
    
    def _clear_dates(self) -> None:
        """Efface toutes les dates sélectionnées."""
        self.state['selected_dates'] = []
        notify('Dates effacées', type='info')
        # Mettre à jour seulement les conteneurs nécessaires
        self._update_calendar_display()
        self._update_final_schedule_display()
    
    def _remove_date(self, date_to_remove) -> None:
        """Supprime une date spécifique."""
        if date_to_remove in self.state['selected_dates']:
            self.state['selected_dates'].remove(date_to_remove)
            notify(f'Date {date_to_remove.strftime("%d/%m/%Y")} supprimée', type='info')
            # Mettre à jour seulement les conteneurs nécessaires
            self._update_calendar_display()
            self._update_final_schedule_display()
    
    def _toggle_date(self, day_date: date) -> None:
        """Bascule la sélection d'une date."""
        today = date.today()
        
        # Empêcher la sélection des jours passés et du jour actuel
        if day_date <= today:
            notify('Impossible de sélectionner une date passée ou le jour actuel', type='negative')
            return
        
        if day_date in self.state['selected_dates']:
            self.state['selected_dates'].remove(day_date)
            notify(f'Date {day_date.strftime("%d/%m/%Y")} désélectionnée', type='info')
        else:
            self.state['selected_dates'].append(day_date)
            self.state['selected_dates'].sort()
            notify(f'Date {day_date.strftime("%d/%m/%Y")} sélectionnée', type='positive')
        
        # Mettre à jour seulement les conteneurs nécessaires
        self._update_calendar_display()
        self._update_final_schedule_display()
    
    
    def _render_default_schedules(self) -> None:
        """Affiche les horaires par défaut du compte sélectionné."""
        session_id = self.state.get('selected_account', '')
        
        # Récupérer le vrai nom du compte depuis le session_id
        account_display_name = session_id  # Par défaut
        if session_id:
            account = self.telegram_manager.get_account(session_id)
            if account:
                account_display_name = account.account_name
        
        # Charger les vrais horaires par défaut du compte
        default_schedules = self._get_default_schedules_for_account(session_id)
        
        if default_schedules:
            ui.label(f'Horaires par défaut ({account_display_name}):').classes('font-semibold mb-3')
            with ui.column().classes('gap-2'):
                for schedule in default_schedules:
                    with ui.row().classes('items-center justify-between p-2 bg-green-50 rounded border border-green-200'):
                        with ui.row().classes('items-center gap-2'):
                            ui.label(schedule['time']).classes('font-mono text-lg')
                            ui.label(schedule['label']).classes('text-sm text-gray-600')
                        ui.html(svg('check_circle', 20, '#059669'))
            
            # Ajouter automatiquement les horaires par défaut
            if 'selected_schedules' not in self.state:
                self.state['selected_schedules'] = []
            # Marquer comme horaires par défaut et éviter les doublons
            for schedule in default_schedules:
                schedule_with_source = schedule.copy()
                schedule_with_source['source'] = 'default'
                if not any(s['time'] == schedule['time'] for s in self.state['selected_schedules']):
                    self.state['selected_schedules'].append(schedule_with_source)
        else:
            ui.label('Aucun horaire par défaut').classes('text-sm text-gray-500')
    
    def _get_default_schedules_for_account(self, account_name: str) -> list:
        """Récupère les horaires par défaut pour un compte donné."""
        if not account_name:
            return []
        
        try:
            # CORRECTION : Recharger l'index pour avoir les derniers horaires
            self.session_manager.sessions_index = self.session_manager._load_index()
            
            # Utiliser le système existant de SessionManager
            settings = self.session_manager.get_account_settings(account_name)
            default_schedules = settings.get('default_schedules', [])
            
            # Convertir le format existant vers le nouveau format si nécessaire
            if default_schedules:
                # Si c'est déjà au bon format (liste de dicts)
                if isinstance(default_schedules[0], dict):
                    return default_schedules
                # Si c'est au format string (liste de strings)
                elif isinstance(default_schedules[0], str):
                    return [{'time': schedule, 'label': schedule} for schedule in default_schedules]
            
            # Si pas d'horaires définis, utiliser des horaires par défaut
            return [
                {'time': '09:00', 'label': 'Matin'},
                {'time': '12:00', 'label': 'Midi'},
                {'time': '18:00', 'label': 'Soir'}
            ]
            
        except Exception as e:
            logger.error(f"Erreur récupération horaires par défaut pour {account_name}: {e}")
            # Retourner des horaires par défaut en cas d'erreur
            return [
                {'time': '09:00', 'label': 'Matin'},
                {'time': '12:00', 'label': 'Midi'},
                {'time': '18:00', 'label': 'Soir'}
            ]
    
    def _render_manual_schedules_to_container(self, container) -> None:
        """Affiche les horaires ajoutés manuellement dans un conteneur spécifique."""
        if 'selected_schedules' not in self.state:
            self.state['selected_schedules'] = []
        
        # Filtrer les horaires ajoutés manuellement
        manual_schedules = [s for s in self.state['selected_schedules'] if s.get('source') == 'manual']
        
        with container:
            if manual_schedules:
                ui.label('Horaires ajoutés:').classes('font-semibold mb-3 mt-4')
                with ui.column().classes('gap-2'):
                    for schedule in manual_schedules:
                        with ui.row().classes('items-center justify-between p-2 bg-blue-50 rounded border border-blue-200'):
                            with ui.row().classes('items-center gap-2'):
                                ui.label(schedule['time']).classes('font-mono text-lg')
                                ui.label(schedule['label']).classes('text-sm text-gray-600')
                            with ui.button(on_click=lambda s=schedule: self._remove_schedule(s)).props('dense round flat').style('color: #ef4444;'):
                                ui.html(svg('close', 18, '#ef4444'))
            else:
                ui.label('Aucun horaire ajouté manuellement').classes('text-sm text-gray-500 mt-4')
    
    def _render_manual_schedules(self) -> None:
        """Méthode de compatibilité."""
        pass
    
    def _render_custom_schedule_input(self) -> None:
        """Interface pour ajouter des horaires personnalisés."""
        ui.label('Ajouter un horaire:').classes('font-semibold mb-3 mt-4')
        
        # Conteneur principal pour l'interface d'ajout
        with ui.card().classes('p-4 bg-gray-50 border border-gray-200'):
            with ui.row().classes('items-center gap-4 w-full'):
                # Sélecteur d'heure avec input numérique
                with ui.column().classes('gap-1'):
                    ui.label('Heure').classes('text-sm font-medium text-gray-700')
                    hour_input = ui.number(
                        value=9,
                        min=0,
                        max=23,
                        step=1
                    ).classes('w-20 text-center').props('prefix=""')
                
                # Séparateur
                ui.label(':').classes('text-2xl font-bold text-gray-600 mt-6')
                
                # Sélecteur de minute avec input numérique
                with ui.column().classes('gap-1'):
                    ui.label('Minute').classes('text-sm font-medium text-gray-700')
                    minute_input = ui.number(
                        value=0,
                        min=0,
                        max=59,
                        step=15
                    ).classes('w-20 text-center').props('prefix=""')
                
                # Bouton d'ajout
                with ui.column().classes('gap-1'):
                    ui.label('').classes('text-sm')  # Espaceur pour alignement
                    ui.button(
                        'AJOUTER',
                        on_click=lambda: self._add_custom_schedule_from_inputs(
                            hour_input.value, minute_input.value
                        )
                    ).classes('px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600')
    
    def _render_selected_schedules_to_container(self, container) -> None:
        """Méthode obsolète - les horaires par défaut sont ajoutés automatiquement."""
        pass
    
    def _render_selected_schedules(self) -> None:
        """Affiche les horaires sélectionnés (méthode de compatibilité)."""
        # Cette méthode est gardée pour la compatibilité mais ne devrait plus être utilisée
        pass
    
    def _render_final_schedule_to_container(self, container) -> None:
        """Affiche le planning final dans un conteneur spécifique."""
        # Générer le planning final
        self._generate_final_schedule()
        
        with container:
            if self.state['final_schedule']:
                ui.label(f'Planning final ({len(self.state["final_schedule"])} publication(s)):').classes('font-semibold mb-3')
                with ui.column().classes('gap-2 max-h-96 overflow-y-auto'):
                    for i, item in enumerate(self.state['final_schedule']):
                        with ui.row().classes('items-center justify-between p-3 bg-gradient-to-r from-blue-50 to-blue-100 rounded-lg border border-blue-200'):
                            with ui.column().classes('gap-1 flex-1'):
                                # Convertir le jour en français
                                french_days = {
                                    'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
                                    'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
                                }
                                day_name = french_days.get(item['date'].strftime('%A'), item['date'].strftime('%A'))
                                ui.label(f'{day_name} {item["date"].strftime("%d/%m/%Y")}').classes('font-semibold text-sm')
                                ui.label(f'à {item["time"]}').classes('font-mono text-lg font-bold text-blue-600')
                            with ui.column().classes('items-center gap-1'):
                                ui.label(f'#{i+1}').classes('text-xs text-gray-500')
                                ui.html(svg('send', 24, 'var(--primary)'))
            else:
                ui.label('Sélectionnez des dates et horaires').classes('text-sm text-gray-500 italic')
                ui.label('pour voir le planning final').classes('text-xs text-gray-400')
    
    def _render_final_schedule(self) -> None:
        """Affiche le planning final avec toutes les combinaisons date/heure (méthode de compatibilité)."""
        # Cette méthode est gardée pour la compatibilité mais ne devrait plus être utilisée
        pass
    
    def _add_schedule(self, schedule) -> None:
        """Ajoute un horaire à la sélection."""
        if 'selected_schedules' not in self.state:
            self.state['selected_schedules'] = []
        
        # Éviter les doublons
        if not any(s['time'] == schedule['time'] for s in self.state['selected_schedules']):
            self.state['selected_schedules'].append(schedule)
            notify(f'{schedule["time"]} ajouté', type='positive')
            # Mettre à jour les conteneurs nécessaires
            self._update_manual_schedules_display()
            self._update_final_schedule_display()
    
    def _add_custom_schedule(self, time_str) -> None:
        """Ajoute un horaire personnalisé."""
        if not time_str:
            notify('Veuillez saisir une heure', type='negative')
            return
        
        custom_schedule = {'time': time_str, 'label': 'Personnalisé'}
        self._add_schedule(custom_schedule)
    
    def _add_custom_schedule_from_inputs(self, hour, minute) -> None:
        """Ajoute un horaire personnalisé depuis les inputs numériques."""
        if hour is None or minute is None:
            notify('Veuillez saisir une heure complète', type='negative')
            return
        
        # Convertir en entiers (les inputs ui.number retournent des float)
        try:
            hour = int(hour) if hour is not None else None
            minute = int(minute) if minute is not None else None
        except (ValueError, TypeError):
            notify('Valeurs invalides', type='negative')
            return
        
        if hour is None or minute is None:
            notify('Veuillez saisir une heure complète', type='negative')
            return
        
        # Valider les valeurs
        if hour < 0 or hour > 23:
            notify('Heure invalide (0-23)', type='negative')
            return
        
        if minute < 0 or minute > 59:
            notify('Minute invalide (0-59)', type='negative')
            return
        
        # Formater l'heure avec zéros devant
        time_str = f'{hour:02d}:{minute:02d}'
        custom_schedule = {'time': time_str, 'label': 'Personnalisé', 'source': 'manual'}
        self._add_schedule(custom_schedule)
    
    def _add_custom_schedule_from_selectors(self, hour: str, minute: str) -> None:
        """Ajoute un horaire personnalisé depuis les sélecteurs (méthode de compatibilité)."""
        # Cette méthode est gardée pour la compatibilité mais ne devrait plus être utilisée
        pass
    
    def _remove_schedule(self, schedule) -> None:
        """Supprime un horaire de la sélection."""
        if 'selected_schedules' in self.state and schedule in self.state['selected_schedules']:
            self.state['selected_schedules'].remove(schedule)
            notify(f'{schedule["time"]} supprimé', type='info')
            # Mettre à jour les conteneurs nécessaires
            self._update_manual_schedules_display()
            self._update_final_schedule_display()
    
    def _generate_final_schedule(self) -> None:
        """Génère le planning final en combinant dates et horaires."""
        dates = self.state.get('selected_dates', [])
        schedules = self.state.get('selected_schedules', [])
        
        final_schedule = []
        for date_obj in dates:
            for schedule in schedules:
                final_schedule.append({
                    'date': date_obj,
                    'time': schedule['time'],
                    'datetime': f"{date_obj} {schedule['time']}"
                })
        
        # Trier par date puis par heure
        final_schedule.sort(key=lambda x: (x['date'], x['time']))
        self.state['final_schedule'] = final_schedule
    
    def _update_calendar_display(self) -> None:
        """Met à jour l'affichage du calendrier."""
        # Re-rendre complètement l'étape 4 pour mettre à jour le calendrier
        self.render_steps()
    
    def _update_schedules_display(self) -> None:
        """Met à jour l'affichage des horaires sélectionnés."""
        # Les horaires par défaut sont ajoutés automatiquement, pas besoin de mise à jour
        pass
    
    def _update_manual_schedules_display(self) -> None:
        """Met à jour l'affichage des horaires ajoutés manuellement."""
        # Re-rendre complètement l'étape 4 pour mettre à jour les horaires manuels
        self.render_steps()
    
    def _update_final_schedule_display(self) -> None:
        """Met à jour l'affichage du planning final."""
        # Re-rendre complètement l'étape 4 pour mettre à jour le planning final
        self.render_steps()
    
    
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
    
    async def _on_search_change_native(self) -> None:
        """Filtre les groupes (version HTML native)."""
        try:
            search_text = await ui.run_javascript('document.getElementById("search_groups_native").value', timeout=0.5) or ""
            search_text = str(search_text)
        except Exception:
            search_text = ""
        
        # Ne filtrer que si la recherche a changé
        if search_text == self._last_groups_search:
            return
        
        self._last_groups_search = search_text
        
        self.state['filtered_groups'] = DialogService.filter_dialogs(
            self.state['all_groups'],
            search_text
        )
        self._update_groups_list()
        self._update_counter()
    
    async def _update_message_state(self) -> None:
        """Met à jour le message dans le state (version HTML native)."""
        try:
            message = await ui.run_javascript('document.getElementById("message_textarea_native").value', timeout=0.5) or ""
            self.state['message'] = str(message)
        except Exception:
            pass
    
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
                        icon = 'radio_button_checked' if is_selected else 'radio_button_unchecked'
                        ui.html(svg(icon, 22, 'var(--primary)' if is_selected else 'var(--text-secondary)'))
                        ui.label(group['title']).classes('text-sm font-medium flex-1')
                        if is_selected:
                            ui.html(svg('check', 18, '#059669'))
    
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
            text = f'Aucun groupe sélectionné ({total} disponibles)'
        elif selected == total:
            style = 'background: rgba(16, 185, 129, 0.1); color: var(--success);'
            text = f'Tous les groupes sélectionnés ({selected}/{total})'
        else:
            style = 'background: rgba(30, 58, 138, 0.1); color: var(--primary);'
            text = f'{selected} groupe(s) sélectionné(s) sur {total}'
        
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
    
    async def _send_messages(self) -> None:
        """Envoie les messages programmés."""
        if not self.state.get('final_schedule'):
            notify(MSG_SELECT_DATE, type='warning')
            return
        
        if not self.state['selected_groups']:
            notify(MSG_SELECT_GROUP, type='warning')
            return
        
        # Récupérer le compte
        account = self.telegram_manager.get_account(self.state['selected_account'])
        if not account or not account.is_connected:
            notify('Compte non connecté', type='negative')
            return
        
        # Préparer les dates avec horaires
        scheduled_datetimes = []
        for schedule_item in self.state['final_schedule']:
            date_obj = schedule_item['date']
            time_str = schedule_item['time']
            hour, minute = map(int, time_str.split(':'))
            scheduled_dt = datetime.combine(date_obj, datetime.min.time().replace(hour=hour, minute=minute))
            scheduled_datetimes.append(scheduled_dt)
        
        # Fichier à envoyer (premier fichier uniquement pour le moment)
        file_path = self.state['files'][0]['path'] if self.state['files'] else None
        
        # Créer une tâche dans le gestionnaire
        task = sending_tasks_manager.create_task(
            account_session_id=self.state['selected_account'],
            account_name=account.account_name,
            group_count=len(self.state['selected_groups']),
            date_count=len(self.state['selected_dates']),
            total_messages=len(self.state['selected_groups']) * len(scheduled_datetimes)
        )
        
        # Afficher dialogue de progression avec bouton Minimiser
        with ui.dialog() as progress_dialog, ui.card().classes('w-96 p-6'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.html(svg('send', 28, 'var(--primary)'))
                ui.label('Envoi en cours...').classes('text-xl font-bold')
            progress_label = ui.label('Préparation...').classes('mb-2')
            progress_bar = ui.linear_progress(value=0).classes('w-full mb-4')
            
            with ui.row().classes('w-full gap-3'):
                def minimize():
                    progress_dialog.close()
                    # Retour à l'étape 1
                    self.state['current_step'] = 1
                    self.state['selected_account'] = None
                    self.state['selected_groups'] = []
                    self.state['message'] = ''
                    self.state['files'] = []
                    self.state['selected_dates'] = []
                    self.state['selected_schedules'] = []
                    self.state['final_schedule'] = []
                    self.render_steps()
                    notify('Envoi en arrière-plan, consultez l\'onglet "Envois en cours"', type='info')
                
                with ui.button(on_click=minimize).props('outline').classes('flex-1'):
                    ui.html(svg('expand_more', 18))
                    ui.label('Minimiser').classes('ml-1')
                with ui.button(on_click=lambda: task.cancel()).props('flat').style('color: #ef4444;').classes('flex-1'):
                    ui.html(svg('close', 18, '#ef4444'))
                    ui.label('Annuler').classes('ml-1')
        
        progress_dialog.open()
        
        def on_progress(sent: int, total: int, skipped: int, failed_groups: Set[int]) -> None:
            """Met à jour la progression avec le total ajusté dynamiquement."""
            # Passer le total ajusté pour que l'interface reflète les exclusions
            task.update_progress(sent, skipped, failed_groups, total_adjusted=total)
            progress = sent / total if total > 0 else 0
            progress_bar.set_value(progress)
            progress_label.set_text(f'{sent}/{total} messages envoyés ({skipped} ignorés, {len(failed_groups)} groupes en erreur)')
        
        try:
            notify('Envoi en cours...', type='info')
            
            # Envoyer les messages
            sent, skipped, failed_groups = await MessageService.send_scheduled_messages(
                account=account,
                group_ids=self.state['selected_groups'],
                message=self.state['message'],
                dates=scheduled_datetimes,
                file_path=file_path,
                on_progress=on_progress,
                cancelled_flag=task.cancel_flag,
                task=task  # Passer la tâche pour l'affichage des attentes
            )
            
            # Marquer la tâche comme terminée
            task.complete()
            
            # Fermer le dialogue s'il est encore ouvert
            if progress_dialog.value:
                progress_dialog.close()
            
            if task.cancel_flag['value']:
                notify(f'Envoi annulé : {sent} messages envoyés', type='warning')
            elif failed_groups:
                notify(
                    f'{sent} messages envoyés, {skipped} ignorés, {len(failed_groups)} groupes en erreur',
                    type='warning'
                )
            else:
                notify(f'{sent} messages programmés avec succès !', type='positive')
            
            # Nettoyer le fichier temporaire si utilisé
            if file_path:
                MessageService.cleanup_temp_file(file_path)
            
            # Réinitialiser après envoi
            self.state['current_step'] = 1
            self.state['selected_account'] = None
            self.state['selected_groups'] = []
            self.state['message'] = ''
            self.state['files'] = []
            self.state['selected_dates'] = []
            self.state['selected_schedules'] = []
            self.state['final_schedule'] = []
            self.render_steps()
            
        except Exception as e:
            task.status = "annulé"
            if progress_dialog.value:
                progress_dialog.close()
            logger.error(f"Erreur envoi messages: {e}")
            notify(f'Erreur: {e}', type='negative')

