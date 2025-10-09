"""
Page de création de nouveaux messages programmés
"""
import asyncio
from datetime import datetime, timedelta
from nicegui import ui
from utils.logger import get_logger

logger = get_logger()


class NewMessagePage:
    """Page de création de nouveaux messages"""
    
    def __init__(self, telegram_manager):
        self.telegram_manager = telegram_manager
        self.state = {
            'current_step': 1,
            'selected_account': None,
            'selected_groups': [],
            'all_groups': [],
            'filtered_groups': [],
            'message': '',
            'file_path': None,
            'selected_dates': [],
            'filter_text': ''
        }
        self.steps_container = None
        self.groups_container = None
        self.counter_label = None
    
    def render(self):
        """Rendu de la page"""
        with ui.column().classes('w-full h-full gap-6 p-8').style('overflow: hidden;'):
            # En-tête moderne
            with ui.row().classes('items-center gap-3 mb-2'):
                ui.label('✎').classes('text-4xl').style('color: var(--primary);')
                ui.label('Nouveau Message').classes('text-3xl font-bold').style('color: var(--text-primary);')
            ui.label('Créez et programmez vos messages Telegram').classes('text-sm').style('color: var(--text-secondary);')
            ui.separator().style('background: var(--border); height: 1px; border: none; margin: 16px 0;')
            
            # Container pour les étapes
            self.steps_container = ui.column().classes('w-full flex-1').style('overflow: visible;')
            
            # Rendu initial
            self.render_steps()
    
    def render_steps(self):
        """Rendu de l'interface par étapes"""
        self.steps_container.clear()
        with self.steps_container:
            # Indicateur d'étapes moderne
            with ui.card().classes('w-full p-4 mb-4 card-modern'):
                with ui.row().classes('w-full items-center justify-around'):
                    for i in range(1, 5):
                        if i == self.state['current_step']:
                            step_class = 'font-bold text-base'
                            step_style = 'background: var(--primary); color: white; box-shadow: 0 4px 12px rgba(30, 58, 138, 0.3);'
                        elif i < self.state['current_step']:
                            step_class = 'font-semibold text-sm'
                            step_style = 'background: var(--success); color: white;'
                        else:
                            step_class = 'text-sm'
                            step_style = 'background: #e2e8f0; color: var(--text-secondary);'
                        
                        with ui.column().classes('items-center gap-2'):
                            ui.label(f'{i}').classes(f'w-10 h-10 rounded-full flex items-center justify-center {step_class}').style(step_style)
                            step_labels = ['Compte', 'Groupes', 'Message', 'Dates']
                            ui.label(step_labels[i-1]).classes('text-xs font-medium').style('color: var(--text-secondary);')
            
            # Contenu de l'étape actuelle
            if self.state['current_step'] == 1:
                self.render_step_1()
            elif self.state['current_step'] == 2:
                self.render_step_2()
            elif self.state['current_step'] == 3:
                self.render_step_3()
            elif self.state['current_step'] == 4:
                self.render_step_4()
    
    def render_step_1(self):
        """Étape 1 : Sélection du compte"""
        with ui.card().classes('w-full p-6 card-modern'):
            ui.label('① Sélectionnez le compte').classes('text-2xl font-bold mb-4').style('color: var(--text-primary);')
            
            accounts = self.telegram_manager.list_accounts()
            connected_accounts = [acc for acc in accounts if acc.get('is_connected', False)]
            
            if not connected_accounts:
                with ui.card().classes('p-4').style('background: #fee2e2; border-left: 3px solid var(--danger);'):
                    ui.label('✕ Aucun compte connecté').classes('font-bold').style('color: #991b1b;')
                    ui.label('Veuillez connecter un compte depuis la page "Comptes"').classes('text-sm').style('color: #991b1b;')
            else:
                for account in connected_accounts:
                    session_id = account['session_id']
                    is_selected = self.state['selected_account'] == session_id
                    
                    # Style selon sélection moderne
                    if is_selected:
                        card_class = 'w-full p-4 cursor-pointer border-2 mb-3 card-modern'
                        card_style = 'border-color: var(--primary); background: rgba(30, 58, 138, 0.05);'
                        icon = '●'
                        icon_style = 'color: var(--primary);'
                        name_style = 'font-bold'
                        name_color = 'var(--primary)'
                    else:
                        card_class = 'w-full p-4 cursor-pointer mb-3 card-modern'
                        card_style = ''
                        icon = '○'
                        icon_style = 'color: var(--text-secondary);'
                        name_style = 'font-semibold'
                        name_color = 'var(--text-primary)'
                    
                    def make_select_handler(sid, name):
                        async def select_account():
                            self.state['selected_account'] = sid
                            ui.notify(f'Compte sélectionné: {name}', type='info')
                            self.render_steps()  # Re-render pour mettre à jour les styles
                        return select_account
                    
                    with ui.card().classes(card_class).style(card_style).on('click', make_select_handler(session_id, account['account_name'])):
                        with ui.row().classes('w-full items-center gap-3'):
                            ui.label(icon).classes('text-2xl').style(icon_style)
                            
                            with ui.column().classes('flex-1 gap-1'):
                                ui.label(f"{account['account_name']}").classes(f'text-lg {name_style}').style(f'color: {name_color};')
                                ui.label(f"{account['phone']}").classes('text-sm').style('color: var(--text-secondary);')
                            
                            ui.html('<span class="status-badge status-online"></span>', sanitize=False)
                
                # Bouton suivant
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    async def next_step():
                        if not self.state['selected_account']:
                            ui.notify('Veuillez sélectionner un compte', type='warning')
                            return
                        
                        # Charger les groupes
                        ui.notify('Chargement des groupes...', type='info')
                        account = self.telegram_manager.get_account(self.state['selected_account'])
                        if account:
                            self.state['all_groups'] = await account.get_dialogs()
                            self.state['filtered_groups'] = self.state['all_groups'].copy()
                            self.state['selected_groups'] = []
                            # Notification AVANT de changer le contexte UI
                            ui.notify(f'{len(self.state["all_groups"])} groupe(s) chargé(s)', type='positive')
                            self.state['current_step'] = 2
                            self.render_steps()
                    
                    ui.button('→ Suivant', on_click=next_step).classes('btn-primary').props('size=md')
    
    def render_step_2(self):
        """Étape 2 : Sélection des groupes"""
        with ui.card().classes('w-full p-6 overflow-visible card-modern'):
            ui.label('② Sélectionnez les groupes').classes('text-2xl font-bold mb-4').style('color: var(--text-primary);')
            
            # Barre de recherche et boutons
            with ui.row().classes('w-full gap-3 mb-4'):
                ui.input('Rechercher un groupe...', 
                        on_change=self.filter_groups).classes('flex-1').props('outlined dense').style('border-radius: 8px;')
                
                with ui.row().classes('gap-2'):
                    ui.button('✓ Tout', on_click=self.select_all).props('outline dense size=sm').style('''
                        color: var(--success); 
                        border-color: var(--success); 
                        font-weight: 600;
                        transition: all 0.2s ease;
                    ''').on('mouseover', lambda: None).on('mouseleave', lambda: None)
                    
                    ui.button('○ Rien', on_click=self.deselect_all).props('outline dense size=sm').style('''
                        color: var(--secondary); 
                        border-color: var(--secondary); 
                        font-weight: 600;
                        transition: all 0.2s ease;
                    ''')
            
            # Compteur de sélection moderne
            self.counter_label = ui.label().classes('text-sm font-semibold mb-3 px-3 py-2 rounded-lg').style('background: rgba(30, 58, 138, 0.1); color: var(--primary); border-left: 3px solid var(--primary);')
            self.update_counter()
            
            # Liste des groupes avec scroll moderne
            self.groups_container = ui.column().classes('w-full gap-2').style('''
                max-height: 350px; 
                overflow-y: auto; 
                overflow-x: hidden;
                padding-right: 8px;
            ''')
            
            # Ajouter du CSS pour le scroll moderne
            ui.add_head_html('''
                <style>
                    .groups-container::-webkit-scrollbar {
                        width: 6px;
                    }
                    .groups-container::-webkit-scrollbar-track {
                        background: #f1f5f9;
                        border-radius: 3px;
                    }
                    .groups-container::-webkit-scrollbar-thumb {
                        background: var(--secondary);
                        border-radius: 3px;
                    }
                    .groups-container::-webkit-scrollbar-thumb:hover {
                        background: var(--primary);
                    }
                </style>
            ''')
            
            self.groups_container.classes('groups-container')
            self.update_groups_list()
            
            # Boutons navigation
            with ui.row().classes('w-full justify-between mt-4'):
                ui.button('← Retour', on_click=self.go_back).props('flat size=md').style('color: var(--secondary);')
                
                async def next_step():
                    if not self.state['selected_groups']:
                        ui.notify('Veuillez sélectionner au moins un groupe', type='warning')
                        return
                    
                    # Charger le message prédéfini du compte si disponible
                    session_manager = self.telegram_manager.session_manager
                    settings = session_manager.get_account_settings(self.state['selected_account'])
                    if settings and settings.get('default_message'):
                        self.state['message'] = settings['default_message']
                    
                    self.state['current_step'] = 3
                    self.render_steps()
                
                ui.button('→ Suivant', on_click=next_step).classes('btn-primary').props('size=md')
    
    def filter_groups(self, e):
        """Filtre les groupes selon la recherche"""
        search_text = e.value.lower()
        if search_text:
            self.state['filtered_groups'] = [
                g for g in self.state['all_groups']
                if search_text in g['title'].lower()
            ]
        else:
            self.state['filtered_groups'] = self.state['all_groups'].copy()
        
        self.update_groups_list()
        self.update_counter()
    
    def select_all(self):
        """Sélectionne tous les groupes filtrés"""
        for group in self.state['filtered_groups']:
            if group['id'] not in self.state['selected_groups']:
                self.state['selected_groups'].append(group['id'])
        
        self.update_groups_list()
        self.update_counter()
    
    def deselect_all(self):
        """Désélectionne tous les groupes filtrés"""
        filtered_ids = [g['id'] for g in self.state['filtered_groups']]
        self.state['selected_groups'] = [
            gid for gid in self.state['selected_groups']
            if gid not in filtered_ids
        ]
        
        self.update_groups_list()
        self.update_counter()
    
    def toggle_group(self, group_id):
        """Toggle la sélection d'un groupe"""
        if group_id in self.state['selected_groups']:
            self.state['selected_groups'].remove(group_id)
        else:
            self.state['selected_groups'].append(group_id)
        
        self.update_groups_list()
        self.update_counter()
    
    def update_groups_list(self):
        """Met à jour uniquement la liste des groupes"""
        if not self.groups_container:
            return
        
        self.groups_container.clear()
        with self.groups_container:
            for group in self.state['filtered_groups']:
                is_selected = group['id'] in self.state['selected_groups']
                
                def make_toggle_handler(gid):
                    def handler():
                        self.toggle_group(gid)
                    return handler
                
                # Style moderne selon sélection
                if is_selected:
                    card_style = 'background: rgba(16, 185, 129, 0.05); border: 2px solid var(--success);'
                    icon = '●'
                    icon_style = 'color: var(--success);'
                    title_style = 'color: var(--success); font-weight: 600;'
                else:
                    card_style = 'background: white; border: 1px solid var(--border);'
                    icon = '○'
                    icon_style = 'color: var(--text-secondary);'
                    title_style = 'color: var(--text-primary);'
                
                with ui.card().classes('w-full p-4 cursor-pointer card-modern').style(f'{card_style} transition: all 0.2s ease;').on('click', make_toggle_handler(group['id'])):
                    with ui.row().classes('w-full items-center gap-3'):
                        ui.label(icon).classes('text-xl').style(icon_style)
                        
                        with ui.column().classes('flex-1 gap-1'):
                            ui.label(group['title']).classes('text-sm font-medium').style(title_style)
                            
                            # Indicateur de type de groupe (optionnel)
                            if 'channel' in group.get('type', '').lower():
                                ui.label('Canal').classes('text-xs').style('color: var(--accent); background: rgba(14, 165, 233, 0.1); padding: 2px 6px; border-radius: 4px;')
                            elif 'supergroup' in group.get('type', '').lower():
                                ui.label('Supergroupe').classes('text-xs').style('color: var(--primary); background: rgba(30, 58, 138, 0.1); padding: 2px 6px; border-radius: 4px;')
                        
                        # Indicateur visuel de sélection
                        if is_selected:
                            ui.label('✓').classes('text-sm font-bold').style('color: var(--success);')
    
    def update_counter(self):
        """Met à jour le compteur de sélection"""
        if self.counter_label:
            total = len(self.state['filtered_groups'])
            selected = len([g for g in self.state['filtered_groups'] if g['id'] in self.state['selected_groups']])
            
            if selected == 0:
                counter_style = 'background: rgba(239, 68, 68, 0.1); color: var(--danger); border-left: 3px solid var(--danger);'
                counter_text = f'○ Aucun groupe sélectionné ({total} disponibles)'
            elif selected == total:
                counter_style = 'background: rgba(16, 185, 129, 0.1); color: var(--success); border-left: 3px solid var(--success);'
                counter_text = f'✓ Tous les groupes sélectionnés ({selected}/{total})'
            else:
                counter_style = 'background: rgba(30, 58, 138, 0.1); color: var(--primary); border-left: 3px solid var(--primary);'
                counter_text = f'● {selected} groupe(s) sélectionné(s) sur {total}'
            
            self.counter_label.set_text(counter_text)
            self.counter_label.style(counter_style)
    
    def go_back(self):
        """Retour à l'étape précédente"""
        if self.state['current_step'] > 1:
            self.state['current_step'] -= 1
            self.render_steps()
    
    def render_step_3(self):
        """Étape 3 : Composition du message"""
        with ui.card().classes('w-full p-6 card-modern'):
            ui.label('③ Composez votre message').classes('text-2xl font-bold mb-4').style('color: var(--text-primary);')
            
            # Zone de texte pour le message
            ui.textarea('Message', value=self.state['message'], 
                       on_change=lambda e: self.state.update({'message': e.value})
            ).classes('w-full').props('outlined rows=6')
            
            # Compteur de caractères moderne
            with ui.row().classes('w-full justify-between items-center mb-4'):
                ui.label(f"Caractères: {len(self.state['message'])}").classes('text-sm').style('color: var(--text-secondary);')
                if len(self.state['message']) > 0:
                    ui.label(f"{len(self.state['message'])}/4096").classes('text-xs').style('color: var(--primary); background: rgba(30, 58, 138, 0.1); padding: 2px 8px; border-radius: 4px;')
            
            # Upload de fichier moderne
            with ui.card().classes('w-full p-4').style('background: var(--bg-secondary); border: 2px dashed var(--border); border-radius: 8px;'):
                with ui.column().classes('w-full items-center gap-3'):
                    ui.label('📎 Ajouter un fichier').classes('font-semibold').style('color: var(--text-primary);')
                    ui.label('Glissez-déposez un fichier ou cliquez pour sélectionner').classes('text-sm').style('color: var(--text-secondary);')
                    
                    async def handle_upload(e):
                        if e.name:
                            self.state['file_path'] = e.name
                            ui.notify(f'Fichier ajouté: {e.name}', type='positive')
                            # Re-render pour mettre à jour l'affichage
                            self.render_steps()
                    
                    upload_widget = ui.upload(on_upload=handle_upload, auto_upload=True).props('outlined dense')
                    
                    if self.state['file_path']:
                        with ui.row().classes('w-full items-center gap-2 mt-2'):
                            ui.label('✓').classes('text-green-600')
                            ui.label(f"{self.state['file_path']}").classes('text-sm font-medium').style('color: var(--success);')
                            
                            def remove_file():
                                self.state['file_path'] = None
                                self.render_steps()
                            
                            ui.button('✕', on_click=remove_file).props('flat dense').style('color: var(--danger);')
            
            # Boutons navigation
            with ui.row().classes('w-full justify-between mt-4'):
                ui.button('← Retour', on_click=self.go_back).props('flat size=md').style('color: var(--secondary);')
                
                async def next_step():
                    if not self.state['message'].strip():
                        ui.notify('Veuillez entrer un message', type='warning')
                        return
                    
                    # Charger les horaires prédéfinis du compte si disponibles
                    account = self.telegram_manager.get_account(self.state['selected_account'])
                    if account and hasattr(account, 'settings'):
                        predefined_times = account.settings.get('scheduled_times', [])
                        # Convertir en dates pour les prochains jours
                        # (implémentation simplifiée)
                    
                    self.state['current_step'] = 4
                    self.render_steps()
                
                ui.button('→ Suivant', on_click=next_step).classes('btn-primary').props('size=md')
    
    def render_step_4(self):
        """Étape 4 : Sélection des dates et heures - Layout plein écran optimisé"""
        with ui.column().classes('w-full gap-4').style('height: calc(100vh - 200px); overflow: hidden;'):
            
            # En-tête compact
            ui.label('④ Programmez les dates et heures').classes('text-2xl font-bold mb-2').style('color: var(--text-primary);')
            
            # Layout principal : 2 colonnes pour utiliser toute la largeur
            with ui.row().classes('flex-1 gap-6').style('overflow-y: auto;'):
                
                # COLONNE GAUCHE : Horaires + Calendrier (60% de la largeur)
                with ui.column().classes('flex-1 gap-4').style('flex: 3;'):
                    
                    # SECTION 1: Horaires (en haut, compact)
                    with ui.card().classes('p-4 card-modern').style('background: rgba(30, 58, 138, 0.05); border-left: 3px solid var(--primary);'):
                        with ui.row().classes('w-full items-center gap-4'):
                            ui.label('🕐 Horaires à utiliser').classes('font-bold').style('color: var(--primary);')
                            
                            # Charger les horaires
                            session_manager = self.telegram_manager.session_manager
                            settings = session_manager.get_account_settings(self.state['selected_account'])
                            predefined_times = settings.get('default_schedules', [])
                            
                            if not hasattr(self, 'temp_times'):
                                self.temp_times = []
                            
                            all_times = sorted(set(predefined_times + self.temp_times))
                            self.selected_times = []
                            
                            # Horaires existants en ligne
                            with ui.row().classes('gap-2 flex-wrap flex-1'):
                                for i, time in enumerate(all_times):
                                    with ui.row().classes('items-center gap-1'):
                                        checkbox = ui.checkbox(time, value=True).classes('text-sm')
                                        self.selected_times.append(checkbox)
                                        
                                        is_saved = time in predefined_times
                                        if is_saved:
                                            def make_delete_saved_handler(time_to_delete):
                                                def delete_time():
                                                    predefined_times.remove(time_to_delete)
                                                    session_manager.update_account_settings(
                                                        self.state['selected_account'],
                                                        default_schedules=predefined_times
                                                    )
                                                    ui.notify('Horaire supprimé', type='info')
                                                    self.render_steps()
                                                return delete_time
                                            ui.button('✕', on_click=make_delete_saved_handler(time)).props('flat dense').style('color: var(--danger);')
                                        else:
                                            def make_delete_temp_handler(time_to_delete):
                                                def delete_time():
                                                    self.temp_times.remove(time_to_delete)
                                                    ui.notify('Horaire supprimé', type='info')
                                                    self.render_steps()
                                                return delete_time
                                            ui.button('⏳', on_click=make_delete_temp_handler(time)).props('flat dense').style('color: var(--warning);')
                            
                            # Ajouter un horaire
                            with ui.row().classes('gap-2'):
                                time_input = ui.input(placeholder='HH:MM').props('dense outlined').style('width: 80px;')
                                
                                def add_time():
                                    time_str = time_input.value.strip()
                                    if time_str:
                                        try:
                                            h, m = map(int, time_str.split(':'))
                                            if 0 <= h <= 23 and 0 <= m <= 59:
                                                formatted = f"{h:02d}:{m:02d}"
                                                if formatted not in all_times:
                                                    self.temp_times.append(formatted)
                                                    self.temp_times.sort()
                                                    time_input.value = ''
                                                    ui.notify('Horaire ajouté', type='positive')
                                                    self.render_steps()
                                                else:
                                                    ui.notify('Déjà existant', type='warning')
                                            else:
                                                ui.notify('Format invalide', type='warning')
                                        except:
                                            ui.notify('Format invalide (HH:MM)', type='warning')
                                
                                ui.button('＋', on_click=add_time).props('outline dense').style('color: var(--accent);')
                    
                    # SECTION 2: Calendrier (pleine largeur de la colonne)
                    with ui.card().classes('p-4 card-modern'):
                        ui.label('📅 Calendrier').classes('font-bold mb-3').style('color: var(--text-primary);')
                        self.create_calendar()
                
                # COLONNE DROITE : Résumé et Actions (40% de la largeur)
                with ui.column().classes('gap-4').style('flex: 2; min-width: 350px;'):
                    
                    # Compteur de dates
                    with ui.card().classes('p-4 card-modern').style('background: rgba(16, 185, 129, 0.05); border-left: 3px solid var(--success);'):
                        ui.label(f'📋 {len(self.state["selected_dates"])} date(s) programmée(s)').classes('font-bold').style('color: var(--success);')
                    
                    # Actions rapides
                    with ui.card().classes('p-4 card-modern'):
                        ui.label('Actions rapides').classes('font-semibold mb-3').style('color: var(--text-primary);')
                        
                        with ui.column().classes('gap-2'):
                            ui.button('📅 Ajouter 7 jours', on_click=self.add_week).props('outline').style('color: var(--accent);').classes('w-full')
                            ui.button('📅 Ajouter 30 jours', on_click=self.add_month).props('outline').style('color: var(--primary);').classes('w-full')
                            ui.button('🗑️ Effacer toutes les dates', on_click=self.clear_all_dates).props('outline').style('color: var(--danger);').classes('w-full')
                    
                    # Liste des dates sélectionnées
                    with ui.card().classes('p-4 card-modern flex-1').style('min-height: 300px;'):
                        ui.label('Dates sélectionnées').classes('font-semibold mb-3').style('color: var(--text-primary);')
                        
                        if self.state['selected_dates']:
                            with ui.column().classes('gap-2').style('max-height: 400px; overflow-y: auto;'):
                                for i, dt in enumerate(sorted(self.state['selected_dates'])):
                                    with ui.card().classes('p-3').style('background: var(--bg-secondary); border: 1px solid var(--border);'):
                                        with ui.row().classes('w-full items-center gap-3'):
                                            with ui.column().classes('flex-1 gap-1'):
                                                ui.label(dt.strftime('%d/%m/%Y')).classes('font-semibold').style('color: var(--text-primary);')
                                                ui.label(dt.strftime('%H:%M')).classes('text-sm').style('color: var(--text-secondary);')
                                            
                                            def make_remove_handler(idx):
                                                def handler():
                                                    self.state['selected_dates'].pop(idx)
                                                    self.render_steps()
                                                return handler
                                            
                                            ui.button('✕', on_click=make_remove_handler(i)).props('flat dense').style('color: var(--danger);')
                        else:
                            ui.label('Aucune date sélectionnée').classes('text-center').style('color: var(--text-secondary); padding: 40px;')
                            ui.label('Sélectionnez des dates dans le calendrier à gauche').classes('text-sm text-center').style('color: var(--text-secondary);')
            
            # Boutons de navigation fixes
            with ui.card().classes('w-full p-4 card-modern').style('border-top: 1px solid var(--border); background: white;'):
                with ui.row().classes('w-full justify-between'):
                    ui.button('← Retour', on_click=self.go_back).props('flat size=md').style('color: var(--secondary);')
                    ui.button('✓ Envoyer', on_click=self.send_scheduled_messages).classes('btn-primary').props('size=lg').style('background: var(--success);')
    
    def create_calendar(self):
        """Crée un calendrier pour sélectionner les dates"""
        # Initialiser les dates sélectionnées si pas déjà fait
        if not hasattr(self, 'calendar_dates'):
            self.calendar_dates = set()
        
        # Initialiser le mois actuel
        if not hasattr(self, 'current_calendar_month'):
            self.current_calendar_month = datetime.now().date().replace(day=1)
        
        current_month = self.current_calendar_month
        
        # Nom des mois
        month_names = ['Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
                      'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre']
        
        # En-tête du calendrier avec flèches
        with ui.row().classes('w-full justify-between items-center mb-3'):
            def prev_month():
                if self.current_calendar_month.month == 1:
                    self.current_calendar_month = self.current_calendar_month.replace(
                        year=self.current_calendar_month.year - 1, month=12
                    )
                else:
                    self.current_calendar_month = self.current_calendar_month.replace(
                        month=self.current_calendar_month.month - 1
                    )
                self.render_steps()
            
            def next_month():
                if self.current_calendar_month.month == 12:
                    self.current_calendar_month = self.current_calendar_month.replace(
                        year=self.current_calendar_month.year + 1, month=1
                    )
                else:
                    self.current_calendar_month = self.current_calendar_month.replace(
                        month=self.current_calendar_month.month + 1
                    )
                self.render_steps()
            
            ui.button('◀', on_click=prev_month).props('flat dense')
            ui.label(f'{month_names[current_month.month-1]} {current_month.year}').classes('text-lg font-bold')
            ui.button('▶', on_click=next_month).props('flat dense')
        
        # Jours de la semaine
        with ui.row().classes('w-full gap-1 mb-2'):
            days = ['Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam', 'Dim']
            for day in days:
                ui.label(day).classes('w-12 text-center font-bold text-gray-600')
        
        # Grille du calendrier
        with ui.column().classes('w-full'):
            # Calculer le premier jour du mois et le nombre de jours
            first_day = current_month.weekday()
            days_in_month = (current_month.replace(month=current_month.month % 12 + 1, day=1) - 
                           timedelta(days=1)).day
            
            # Créer les lignes de semaines
            current_date = 1
            while current_date <= days_in_month:
                with ui.row().classes('w-full gap-1 mb-1'):
                    # Ajouter les jours vides du début
                    for i in range(7):
                        if current_date == 1 and i < first_day:
                            ui.label('').classes('w-12 h-12')  # Jour vide
                        elif current_date <= days_in_month:
                            day_date = current_month.replace(day=current_date)
                            self.create_calendar_day(day_date)
                            current_date += 1
                        else:
                            ui.label('').classes('w-12 h-12')  # Jour vide
    
    def create_calendar_day(self, day_date):
        """Crée un jour dans le calendrier"""
        today = datetime.now().date()
        
        # Déterminer le style et si cliquable
        if day_date <= today:
            # Date passée ou aujourd'hui - grisée
            color = 'grey'
            is_clickable = False
        elif day_date in self.calendar_dates:
            # Date sélectionnée - bleu
            color = 'blue'
            is_clickable = True
        else:
            # Date normale - blanc
            color = None
            is_clickable = True
        
        def make_click_handler(date):
            def toggle_date():
                if not is_clickable:
                    return
                
                if date in self.calendar_dates:
                    # Désélectionner : retirer la date ET supprimer toutes les dates/heures associées
                    self.calendar_dates.remove(date)
                    # Supprimer toutes les dates/heures de ce jour
                    self.state['selected_dates'] = [
                        dt for dt in self.state['selected_dates']
                        if dt.date() != date
                    ]
                else:
                    # Sélectionner : ajouter la date
                    self.calendar_dates.add(date)
                    # Appliquer les horaires sélectionnés à cette date
                    self.apply_times_to_date(date)
                
                # Re-render pour mettre à jour l'affichage
                self.render_steps()
            return toggle_date
        
        # Créer le bouton avec la bonne couleur
        btn = ui.button(str(day_date.day), on_click=make_click_handler(day_date))
        btn.classes('w-12 h-12')
        
        if color:
            btn.props(f'color={color}')
        else:
            btn.props('outline')
        
        if not is_clickable:
            btn.props('disable')
    
    def apply_times_to_date(self, date):
        """Applique les horaires sélectionnés à une date"""
        if not hasattr(self, 'selected_times'):
            return
        
        # Récupérer tous les horaires (prédéfinis + temporaires)
        session_manager = self.telegram_manager.session_manager
        settings = session_manager.get_account_settings(self.state['selected_account'])
        predefined_times = settings.get('default_schedules', [])
        
        if not hasattr(self, 'temp_times'):
            self.temp_times = []
        
        all_times = sorted(set(predefined_times + self.temp_times))
        
        # Pour chaque horaire sélectionné, créer une date/heure
        for i, checkbox in enumerate(self.selected_times):
            if i < len(all_times) and checkbox.value:
                time_str = all_times[i]
                hour, minute = map(int, time_str.split(':'))
                
                dt = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
                
                # Ajouter seulement si pas déjà présent
                if dt not in self.state['selected_dates']:
                    self.state['selected_dates'].append(dt)
    
    def clear_all_dates(self):
        """Vide toutes les dates sélectionnées"""
        self.state['selected_dates'] = []
        if hasattr(self, 'calendar_dates'):
            self.calendar_dates.clear()
        ui.notify('Toutes les dates ont été supprimées', type='info')
        self.render_steps()
    
    def add_week(self):
        """Ajoute une semaine de dates avec les horaires sélectionnés"""
        now = datetime.now()
        
        # Récupérer les horaires prédéfinis du compte
        session_manager = self.telegram_manager.session_manager
        settings = session_manager.get_account_settings(self.state['selected_account'])
        predefined_times = settings.get('default_schedules', [])
        
        if not predefined_times:
            # Fallback : 9h si pas d'horaires prédéfinis
            predefined_times = ['09:00']
        
        # Ajouter une semaine (7 jours)
        for day in range(1, 8):
            date = (now + timedelta(days=day)).date()
            
            # Ajouter chaque horaire prédéfini
            for time_str in predefined_times:
                hour, minute = map(int, time_str.split(':'))
                dt = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
                
                if dt not in self.state['selected_dates']:
                    self.state['selected_dates'].append(dt)
        
        ui.notify(f'Une semaine ajoutée ({len(predefined_times)} horaire(s) par jour)', type='positive')
        self.render_steps()
    
    def add_month(self):
        """Ajoute un mois de dates avec les horaires sélectionnés"""
        now = datetime.now()
        
        # Récupérer les horaires prédéfinis du compte
        session_manager = self.telegram_manager.session_manager
        settings = session_manager.get_account_settings(self.state['selected_account'])
        predefined_times = settings.get('default_schedules', [])
        
        if not predefined_times:
            # Fallback : 9h si pas d'horaires prédéfinis
            predefined_times = ['09:00']
        
        # Ajouter un mois (30 jours)
        for day in range(1, 31):
            date = (now + timedelta(days=day)).date()
            
            # Ajouter chaque horaire prédéfini
            for time_str in predefined_times:
                hour, minute = map(int, time_str.split(':'))
                dt = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
                
                if dt not in self.state['selected_dates']:
                    self.state['selected_dates'].append(dt)
        
        ui.notify(f'Un mois ajouté ({len(predefined_times)} horaire(s) par jour)', type='positive')
        self.render_steps()
    
    async def send_scheduled_messages(self):
        """Envoie les messages programmés"""
        if not self.state['selected_dates']:
            ui.notify('Veuillez ajouter au moins une date', type='warning')
            return
        
        # Variable pour gérer l'annulation
        cancelled = {'value': False}
        
        # Dialog de progression (persistant, ne se ferme pas en cliquant à l'extérieur)
        dialog = ui.dialog().props('persistent')
        
        with dialog, ui.card().classes('w-[500px] p-6 card-modern'):
            # Titre
            ui.label('⏱ Envoi des messages programmés').classes('text-xl font-bold mb-4 text-center').style('color: var(--text-primary);')
            
            # CSS pour stabiliser la barre et cacher les chiffres par défaut de Quasar
            ui.add_head_html('''
                <style>
                    .q-linear-progress {
                        height: 28px !important;
                        border-radius: 6px !important;
                    }
                    /* Cacher TOUS les chiffres générés par Quasar */
                    .q-linear-progress__track::after,
                    .q-linear-progress__model::after,
                    .q-linear-progress::after,
                    .q-linear-progress::before {
                        content: '' !important;
                        display: none !important;
                        visibility: hidden !important;
                    }
                    /* Masquer le texte de la barre de progression */
                    .q-linear-progress .q-linear-progress__text {
                        display: none !important;
                    }
                    /* Masquer tous les éléments texte dans la barre */
                    .q-linear-progress span {
                        display: none !important;
                    }
                </style>
            ''')
            
            # Conteneur pour superposer le pourcentage sur la barre
            with ui.element('div').classes('w-full mb-4').style('position: relative;'):
                # Barre de progression (en bleu vif) - show-value=false pour masquer la valeur par défaut
                progress = ui.linear_progress(0).props('show-value=false color=blue size=28px rounded').classes('w-full')
                
                # Pourcentage superposé AU CENTRE de la barre
                progress_percent = ui.label('0%').classes('text-base font-bold').style(
                    'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); '
                    'color: white; text-shadow: 0 0 4px rgba(0,0,0,0.8); z-index: 100; pointer-events: none;'
                )
            
            # Statut détaillé
            status_label = ui.label('Préparation...').classes('text-sm text-gray-700 mb-2 text-center')
            
            # Message d'erreur (groupes)
            error_label = ui.label('').classes('text-sm text-orange-600 font-medium mb-4 text-center')
            
            # Bouton d'annulation
            def cancel_send():
                cancelled['value'] = True
                ui.notify('❌ Annulation en cours...', type='warning')
            
            ui.button('❌ Annuler l\'envoi', on_click=cancel_send).props('color=red outline').classes('w-full')
        
        dialog.open()
        
        async def update_ui():
            """Force le rafraîchissement de l'UI"""
            await asyncio.sleep(0.05)  # Petit délai pour laisser l'UI se rafraîchir
        
        try:
            account = self.telegram_manager.get_account(self.state['selected_account'])
            if not account:
                ui.notify('Compte introuvable', type='negative')
                return
            
            total_groups = len(self.state['selected_groups'])
            total_dates = len(self.state['selected_dates'])
            total = total_groups * total_dates
            sent = 0
            skipped = 0  # Messages skippés (groupes en erreur)
            failed_groups = set()  # Groupes qui ont échoué (on les skip)
            
            # Calcul estimation (25 req/sec optimisé)
            num_groups = len(self.state['selected_groups'])
            num_dates = len(self.state['selected_dates'])
            
            if num_groups >= 25:
                # Si 25+ groupes : on peut faire 25 msg/sec (1 par groupe)
                estimated_time = int(total / 25) + 1
            else:
                # Si moins de 25 groupes : 1 sec par round de groupes
                estimated_time = num_dates + 1
            
            status_label.set_text(f'Envoi: 0/{total} (~{estimated_time}s)')
            
            # STRATÉGIE OPTIMALE : Créneau par créneau
            # Pour chaque créneau (date+heure), on l'envoie à tous les groupes
            # On vérifie qu'1 sec s'est écoulée depuis le dernier msg à ce groupe
            # Permet d'envoyer jusqu'à 25 req/sec en alternant les groupes
            
            # Dictionnaire pour tracker le dernier envoi par groupe
            last_send_time = {}  # {group_id: timestamp}
            last_global_send = 0  # Timestamp du dernier envoi global (tous groupes confondus)
            
            for date_idx, dt in enumerate(self.state['selected_dates'], 1):
                # Vérifier si annulé
                if cancelled['value']:
                    status_label.set_text('❌ Envoi annulé par l\'utilisateur')
                    error_label.set_text(f'{sent} envoyés, {len(failed_groups)} groupe(s) en erreur')
                    ui.notify(f'⚠️ Annulé : {sent} messages envoyés', type='warning')
                    await asyncio.sleep(2)
                    break
                
                # Mise à jour au début de chaque créneau
                status_label.set_text(f'📅 Créneau {date_idx}/{total_dates} - Envoi: {sent}/{total - skipped}')
                await update_ui()
                
                # Envoyer ce créneau à tous les groupes
                for group_idx, group_id in enumerate(self.state['selected_groups'], 1):
                    # Vérifier si annulé
                    if cancelled['value']:
                        break
                    
                    # Skip les groupes qui ont déjà échoué
                    if group_id in failed_groups:
                        skipped += 1
                        percent = int((sent + skipped) / total * 100)
                        progress.set_value((sent + skipped) / total)
                        progress_percent.set_text(f'{percent}%')
                        await update_ui()
                        continue
                    
                    try:
                        # PROTECTION 1 : Rate limit par chat (1 msg/sec/chat) - PRIORITAIRE
                        # Vérifier AVANT tout envoi que 1 seconde s'est écoulée depuis le dernier message à CE groupe
                        if group_id in last_send_time:
                            elapsed_chat = asyncio.get_event_loop().time() - last_send_time[group_id]
                            if elapsed_chat < 1.0:
                                wait_chat = 1.0 - elapsed_chat
                                # Attendre le temps nécessaire
                                while wait_chat > 0:
                                    chunk = min(0.1, wait_chat)
                                    await asyncio.sleep(chunk)
                                    await update_ui()
                                    wait_chat -= chunk
                        
                        # PROTECTION 2 : Rate limit global (25 req/sec = 0.04s entre chaque envoi)
                        if last_global_send > 0:
                            elapsed_global = asyncio.get_event_loop().time() - last_global_send
                            if elapsed_global < 0.04:
                                wait_global = 0.04 - elapsed_global
                                await asyncio.sleep(wait_global)
                                await update_ui()
                        
                        # Envoyer le message programmé
                        await account.client.send_message(
                            group_id,
                            self.state['message'],
                            schedule=dt
                        )
                        sent += 1
                        
                        # Enregistrer l'heure d'envoi pour ce groupe ET globalement
                        current_time = asyncio.get_event_loop().time()
                        last_send_time[group_id] = current_time
                        last_global_send = current_time
                        
                        # Mettre à jour la progression avec pourcentage
                        percent = int((sent + skipped) / total * 100)
                        progress.set_value((sent + skipped) / total)
                        progress_percent.set_text(f'{percent}%')
                        status_label.set_text(f'📅 Créneau {date_idx}/{total_dates} - Groupe {group_idx}/{total_groups} - {sent}/{total - skipped}')
                        
                        # Toujours afficher le nombre de groupes en erreur s'il y en a
                        if failed_groups:
                            error_label.set_text(f'⚠️ {len(failed_groups)} groupe(s) ne permettent pas les messages programmés')
                        else:
                            error_label.set_text('')
                        
                        # Forcer le rafraîchissement de l'UI
                        await update_ui()
                        
                    except Exception as e:
                        error_msg = str(e)
                        
                        # Vérifier si c'est une erreur de permission/topic
                        if any(x in error_msg.lower() for x in ["can't write", "topic_closed", "chat_write_forbidden"]):
                            # Ajouter ce groupe à la liste des exclus
                            failed_groups.add(group_id)
                            skipped += 1
                            logger.error(f'Groupe {group_id} exclu: {error_msg}')
                            error_label.set_text(f'⚠️ {len(failed_groups)} groupe(s) ne permettent pas les messages programmés')
                            # Mettre à jour la progression
                            percent = int((sent + skipped) / total * 100)
                            progress.set_value((sent + skipped) / total)
                            progress_percent.set_text(f'{percent}%')
                            await update_ui()
                            continue  # Passer au groupe suivant pour ce créneau
                        
                        # Si c'est une erreur de flood, attendre plus longtemps
                        if 'wait' in error_msg.lower() and 'seconds' in error_msg.lower():
                            import re
                            wait_match = re.search(r'(\d+)\s*seconds', error_msg)
                            if wait_match:
                                wait_time = int(wait_match.group(1)) + 5
                                error_label.set_text(f'⏳ Flood limit atteint, attente de {wait_time}s...')
                                # Attendre par intervalles d'1 seconde pour mettre à jour le compte à rebours
                                for remaining in range(wait_time, 0, -1):
                                    error_label.set_text(f'⏳ Flood limit - attente {remaining}s...')
                                    await asyncio.sleep(1)
                                    await update_ui()
                                
                                # Réessayer
                                try:
                                    await account.client.send_message(
                                        group_id,
                                        self.state['message'],
                                        schedule=dt
                                    )
                                    sent += 1
                                    current_time = asyncio.get_event_loop().time()
                                    last_send_time[group_id] = current_time
                                    last_global_send = current_time
                                    # Ne pas effacer le message d'erreur s'il y a des groupes en échec
                                    if not failed_groups:
                                        error_label.set_text('')
                                    percent = int((sent + skipped) / total * 100)
                                    progress.set_value((sent + skipped) / total)
                                    progress_percent.set_text(f'{percent}%')
                                    await update_ui()
                                except Exception as e2:
                                    logger.error(f'Erreur après attente: {e2}')
                                    # Si ça échoue encore, marquer comme groupe en erreur
                                    failed_groups.add(group_id)
                                    skipped += 1
                                    percent = int((sent + skipped) / total * 100)
                                    progress.set_value((sent + skipped) / total)
                                    progress_percent.set_text(f'{percent}%')
                                    await update_ui()
                        else:
                            logger.error(f'Erreur envoi message: {e}')
                        
                        # Mise à jour après erreur générique
                        percent = int((sent + skipped) / total * 100)
                        progress.set_value((sent + skipped) / total)
                        progress_percent.set_text(f'{percent}%')
                        status_label.set_text(f'📅 Créneau {date_idx}/{total_dates} - Groupe {group_idx}/{total_groups} - {sent}/{total - skipped}')
                        await update_ui()
                
            if not cancelled['value']:
                # Forcer la barre à 100% à la fin
                progress.set_value(1.0)
                progress_percent.set_text('100%')
                status_label.set_text('✅ Terminé!')
                if failed_groups:
                    error_label.set_text(f'{sent} envoyés, {len(failed_groups)} groupe(s) ne permettent pas les messages programmés')
                    ui.notify(f'✅ {sent} messages envoyés ({len(failed_groups)} groupe(s) ignoré(s))', type='positive')
                else:
                    error_label.set_text(f'{sent} messages envoyés avec succès!')
                    ui.notify(f'✅ {sent} messages programmés envoyés!', type='positive')
                await update_ui()
                
            # Réinitialiser
            await asyncio.sleep(2)
            dialog.close()
            self.state['current_step'] = 1
            self.state['selected_account'] = None
            self.state['selected_groups'] = []
            self.state['message'] = ''
            self.state['file_path'] = None
            self.state['selected_dates'] = []
            # Réinitialiser les horaires temporaires
            if hasattr(self, 'temp_times'):
                self.temp_times = []
            self.render_steps()
            
        except Exception as e:
            logger.error(f'Erreur: {e}')
            ui.notify(f'Erreur: {str(e)}', type='negative')
            dialog.close()
