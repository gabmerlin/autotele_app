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
        with ui.column().classes('w-full h-full gap-4 p-6').style('overflow: hidden;'):
            ui.label('✉️ Nouveau Messages').classes('text-3xl font-bold')
            ui.separator()
            
            # Container pour les étapes
            self.steps_container = ui.column().classes('w-full flex-1').style('overflow: visible;')
            
            # Rendu initial
            self.render_steps()
    
    def render_steps(self):
        """Rendu de l'interface par étapes"""
        self.steps_container.clear()
        with self.steps_container:
            # Indicateur d'étapes (compact)
            with ui.card().classes('w-full p-2 mb-3'):
                with ui.row().classes('w-full items-center justify-around'):
                    for i in range(1, 5):
                        step_class = 'bg-blue-500 text-white' if i == self.state['current_step'] else 'bg-gray-300 text-gray-600'
                        if i < self.state['current_step']:
                            step_class = 'bg-green-500 text-white'
                        
                        with ui.column().classes('items-center gap-0'):
                            ui.label(f'{i}').classes(f'w-7 h-7 rounded-full flex items-center justify-center {step_class} font-bold text-sm')
                            step_labels = ['Compte', 'Groupes', 'Message', 'Dates']
                            ui.label(step_labels[i-1]).classes('text-xs')
            
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
        with ui.card().classes('w-full p-6'):
            ui.label('1️⃣ Sélectionnez le compte').classes('text-2xl font-bold mb-4')
            
            accounts = self.telegram_manager.list_accounts()
            connected_accounts = [acc for acc in accounts if acc.get('is_connected', False)]
            
            if not connected_accounts:
                with ui.card().classes('bg-red-50 p-4'):
                    ui.label('❌ Aucun compte connecté').classes('text-red-700 font-bold')
                    ui.label('Veuillez connecter un compte depuis la page "Compte Telegram"').classes('text-red-600')
            else:
                for account in connected_accounts:
                    session_id = account['session_id']
                    is_selected = self.state['selected_account'] == session_id
                    
                    # Style selon sélection (compact)
                    if is_selected:
                        card_class = 'w-full p-2 cursor-pointer border-2 border-green-500 bg-green-50 mb-2'
                        icon = '🎯'
                        name_style = 'text-base font-bold text-green-700'
                        phone_style = 'text-xs text-green-600'
                    else:
                        card_class = 'w-full p-2 cursor-pointer border border-gray-200 hover:border-gray-300 bg-white mb-2'
                        icon = '⚪'
                        name_style = 'text-base font-bold'
                        phone_style = 'text-xs text-gray-600'
                    
                    def make_select_handler(sid, name):
                        async def select_account():
                            self.state['selected_account'] = sid
                            ui.notify(f'Compte sélectionné: {name}', type='info')
                            self.render_steps()  # Re-render pour mettre à jour les styles
                        return select_account
                    
                    with ui.card().classes(card_class).on('click', make_select_handler(session_id, account['account_name'])):
                        with ui.row().classes('w-full items-center gap-2'):
                            ui.label(icon).classes('text-lg')
                            
                            with ui.column().classes('flex-1'):
                                ui.label(f"{account['account_name']}").classes(name_style)
                                ui.label(f"{account['phone']}").classes(phone_style)
                            
                            ui.label('🟢').classes('text-sm')
                
                # Bouton suivant
                with ui.row().classes('w-full justify-end gap-2 mt-3'):
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
                            self.state['current_step'] = 2
                            self.render_steps()
                            ui.notify(f'{len(self.state["all_groups"])} groupe(s) chargé(s)', type='positive')
                    
                    ui.button('Suivant ➡️', on_click=next_step).props('color=primary size=md')
    
    def render_step_2(self):
        """Étape 2 : Sélection des groupes"""
        with ui.card().classes('w-full p-6 overflow-visible'):
            ui.label('2️⃣ Sélectionnez les groupes').classes('text-2xl font-bold mb-4')
            
            # Barre de recherche et boutons
            with ui.row().classes('w-full gap-2 mb-4'):
                ui.input('Rechercher un groupe...', 
                        on_change=self.filter_groups).classes('flex-1').props('outlined')
                
                ui.button('✅ Tout', on_click=self.select_all).props('flat dense color=green size=sm')
                ui.button('⬜ Rien', on_click=self.deselect_all).props('flat dense color=red size=sm')
            
            # Compteur de sélection (compact)
            self.counter_label = ui.label().classes('text-sm font-bold mb-2')
            self.update_counter()
            
            # Liste des groupes (hauteur réduite pour voir le bouton suivant)
            self.groups_container = ui.column().classes('w-full gap-1').style('max-height: 350px; overflow-y: auto; overflow-x: hidden;')
            self.update_groups_list()
            
            # Boutons navigation
            with ui.row().classes('w-full justify-between mt-3'):
                ui.button('⬅️ Retour', on_click=self.go_back).props('flat size=md')
                
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
                
                ui.button('Suivant ➡️', on_click=next_step).props('color=primary size=md')
    
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
                
                card_class = 'w-full p-2 cursor-pointer border mb-1'
                if is_selected:
                    card_class += ' border-green-500 bg-green-50'
                else:
                    card_class += ' border-gray-200 hover:border-gray-300 bg-white'
                
                def make_toggle_handler(gid):
                    def handler():
                        self.toggle_group(gid)
                    return handler
                
                with ui.card().classes(card_class).on('click', make_toggle_handler(group['id'])):
                    with ui.row().classes('w-full items-center gap-2'):
                        ui.label('✅' if is_selected else '⬜').classes('text-base')
                        ui.label(group['title']).classes('flex-1 text-sm')
    
    def update_counter(self):
        """Met à jour le compteur de sélection"""
        if self.counter_label:
            total = len(self.state['filtered_groups'])
            selected = len([g for g in self.state['filtered_groups'] if g['id'] in self.state['selected_groups']])
            self.counter_label.set_text(f'Sélectionnés: {selected} / {total}')
    
    def go_back(self):
        """Retour à l'étape précédente"""
        if self.state['current_step'] > 1:
            self.state['current_step'] -= 1
            self.render_steps()
    
    def render_step_3(self):
        """Étape 3 : Composition du message"""
        with ui.card().classes('w-full p-6'):
            ui.label('3️⃣ Composez votre message').classes('text-2xl font-bold mb-4')
            
            # Zone de texte pour le message
            ui.textarea('Message', value=self.state['message'], 
                       on_change=lambda e: self.state.update({'message': e.value})
            ).classes('w-full').props('outlined rows=8')
            
            ui.label(f"Caractères: {len(self.state['message'])}").classes('text-sm text-gray-600 mb-4')
            
            # Upload de fichier
            with ui.row().classes('w-full items-center gap-2 mb-4'):
                ui.label('📎 Fichier (optionnel):').classes('font-medium')
                
                async def handle_upload(e):
                    if e.name:
                        self.state['file_path'] = e.name
                        ui.notify(f'Fichier sélectionné: {e.name}', type='positive')
                
                ui.upload(on_upload=handle_upload, auto_upload=True).props('outlined')
                
                if self.state['file_path']:
                    ui.label(f"✅ {self.state['file_path']}").classes('text-green-600 font-medium')
            
            # Boutons navigation
            with ui.row().classes('w-full justify-between mt-3'):
                ui.button('⬅️ Retour', on_click=self.go_back).props('flat size=md')
                
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
                
                ui.button('Suivant ➡️', on_click=next_step).props('color=primary size=md')
    
    def render_step_4(self):
        """Étape 4 : Sélection des dates et heures"""
        with ui.card().classes('w-full p-4'):
            ui.label('4️⃣ Programmez les dates et heures').classes('text-2xl font-bold mb-3')
            
            # Charger les horaires prédéfinis du compte
            session_manager = self.telegram_manager.session_manager
            settings = session_manager.get_account_settings(self.state['selected_account'])
            predefined_times = settings.get('default_schedules', [])
            
            # Horaires temporaires (pour cette session uniquement)
            if not hasattr(self, 'temp_times'):
                self.temp_times = []
            
            # Combiner les horaires prédéfinis et temporaires
            all_times = sorted(set(predefined_times + self.temp_times))
            
            # Section horaires (compact)
            with ui.row().classes('w-full gap-4 mb-3'):
                # Colonne gauche : Horaires
                with ui.card().classes('flex-1 p-3 bg-blue-50'):
                    ui.label('🕐 Horaires à utiliser').classes('font-bold mb-2')
                    
                    # Liste des horaires avec gestion
                    self.horaires_container = ui.column().classes('w-full gap-1')
                    self.selected_times = []
                    
                    with self.horaires_container:
                        if all_times:
                            for i, time in enumerate(all_times):
                                with ui.row().classes('w-full items-center gap-1'):
                                    checkbox = ui.checkbox(time, value=True).classes('text-sm')
                                    self.selected_times.append(checkbox)
                                    
                                    # Vérifier si c'est un horaire sauvegardé ou temporaire
                                    is_saved = time in predefined_times
                                    is_temp = time in self.temp_times
                                    
                                    if is_saved:
                                        # Horaire sauvegardé dans les paramètres : bouton rouge
                                        def make_delete_saved_handler(time_to_delete):
                                            def delete_time():
                                                predefined_times.remove(time_to_delete)
                                                session_manager.update_account_settings(
                                                    self.state['selected_account'],
                                                    default_schedules=predefined_times
                                                )
                                                self.render_steps()
                                                ui.notify('Horaire supprimé des paramètres', type='info')
                                            return delete_time
                                        ui.button('🗑️', on_click=make_delete_saved_handler(time)).props('flat dense size=xs color=red')
                                    elif is_temp:
                                        # Horaire temporaire : bouton orange
                                        def make_delete_temp_handler(time_to_delete):
                                            def delete_time():
                                                self.temp_times.remove(time_to_delete)
                                                self.render_steps()
                                                ui.notify('Horaire temporaire supprimé', type='info')
                                            return delete_time
                                        ui.button('⏳', on_click=make_delete_temp_handler(time)).props('flat dense size=xs color=orange')
                        else:
                            ui.label('Aucun horaire').classes('text-xs text-gray-500')
                    
                    # Ajouter un horaire
                    with ui.row().classes('w-full gap-1 mt-2'):
                        time_input = ui.input(placeholder='HH:MM').classes('flex-1').props('dense')
                        
                        def add_time():
                            time_str = time_input.value.strip()
                            if time_str:
                                try:
                                    h, m = map(int, time_str.split(':'))
                                    if 0 <= h <= 23 and 0 <= m <= 59:
                                        formatted = f"{h:02d}:{m:02d}"
                                        # Vérifier si déjà existant (sauvegardé ou temporaire)
                                        if formatted not in all_times:
                                            # Ajouter comme horaire TEMPORAIRE
                                            self.temp_times.append(formatted)
                                            self.temp_times.sort()
                                            time_input.value = ''
                                            self.render_steps()
                                            ui.notify('⏳ Horaire temporaire ajouté', type='positive')
                                        else:
                                            ui.notify('Déjà existant', type='warning')
                                    else:
                                        ui.notify('Format invalide', type='warning')
                                except:
                                    ui.notify('Format invalide (HH:MM)', type='warning')
                        
                        ui.button('➕ Temp', on_click=add_time).props('dense flat color=orange').classes('text-xs')
                
                # Colonne droite : Boutons rapides + Compteur
                with ui.column().classes('gap-2'):
                    with ui.card().classes('p-2 bg-green-50'):
                        ui.label(f'📋 {len(self.state["selected_dates"])} dates').classes('font-bold text-sm text-center')
                    
                    ui.button('7J', on_click=self.add_week).props('dense color=blue').classes('w-full')
                    ui.button('30J', on_click=self.add_month).props('dense color=purple').classes('w-full')
                    ui.button('🗑️', on_click=self.clear_all_dates).props('dense flat color=red').classes('w-full')
            
            # Layout : Calendrier à gauche + Liste à droite
            with ui.row().classes('w-full gap-3 mb-3'):
                # Calendrier à gauche
                with ui.card().classes('p-3'):
                    ui.label('📅 Calendrier').classes('font-bold mb-2')
                    self.create_calendar()
                
                # Liste des dates à droite
                with ui.card().classes('flex-1 p-3 bg-gray-50'):
                    ui.label(f'📋 {len(self.state["selected_dates"])} date(s) programmée(s)').classes('font-bold mb-2')
                    
                    if self.state['selected_dates']:
                        with ui.column().classes('w-full gap-1 max-h-96 overflow-auto'):
                            for i, dt in enumerate(sorted(self.state['selected_dates'])):
                                with ui.row().classes('w-full items-center gap-2 p-1 hover:bg-gray-100'):
                                    ui.label(dt.strftime('%d/%m/%Y %H:%M')).classes('flex-1 text-sm')
                                    
                                    def make_remove_handler(idx):
                                        def handler():
                                            self.state['selected_dates'].pop(idx)
                                            self.render_steps()
                                        return handler
                                    
                                    ui.button('🗑️', on_click=make_remove_handler(i)).props('flat dense size=sm color=red')
                    else:
                        ui.label('Sélectionnez des dates dans le calendrier').classes('text-gray-500 text-sm italic')
            
            # Boutons navigation
            with ui.row().classes('w-full justify-between mt-3'):
                ui.button('⬅️ Retour', on_click=self.go_back).props('flat size=md')
                ui.button('🚀 Envoyer', on_click=self.send_scheduled_messages).props('color=positive size=md')
    
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
        self.render_steps()
        ui.notify('Toutes les dates ont été supprimées', type='info')
    
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
        
        self.render_steps()
        ui.notify(f'Une semaine ajoutée ({len(predefined_times)} horaire(s) par jour)', type='positive')
    
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
        
        self.render_steps()
        ui.notify(f'Un mois ajouté ({len(predefined_times)} horaire(s) par jour)', type='positive')
    
    async def send_scheduled_messages(self):
        """Envoie les messages programmés"""
        if not self.state['selected_dates']:
            ui.notify('Veuillez ajouter au moins une date', type='warning')
            return
        
        # Variable pour gérer l'annulation
        cancelled = {'value': False}
        
        # Dialog de progression (persistant, ne se ferme pas en cliquant à l'extérieur)
        dialog = ui.dialog().props('persistent')
        
        with dialog, ui.card().classes('w-[500px] p-6'):
            # Titre
            ui.label('📤 Envoi des messages programmés').classes('text-xl font-bold mb-4 text-center')
            
            # CSS pour stabiliser la barre et cacher les chiffres par défaut de Quasar
            ui.add_head_html('''
                <style>
                    .q-linear-progress {
                        height: 28px !important;
                        border-radius: 6px !important;
                    }
                    /* Cacher UNIQUEMENT les chiffres générés par Quasar */
                    .q-linear-progress__track::after,
                    .q-linear-progress__model::after {
                        content: '' !important;
                        display: none !important;
                    }
                </style>
            ''')
            
            # Conteneur pour superposer le pourcentage sur la barre
            with ui.element('div').classes('w-full mb-4').style('position: relative;'):
                # Barre de progression (en bleu vif) - instant=true pour désactiver l'affichage de la valeur
                progress = ui.linear_progress(0).props('instant color=blue size=28px rounded').classes('w-full')
                
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
