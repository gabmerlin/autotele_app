"""
Page de gestion des comptes Telegram.
"""
from typing import Optional
from nicegui import ui

from core.telegram.manager import TelegramManager
from core.session_manager import SessionManager
from ui.components.dialogs import VerificationDialog, ConfirmDialog
from utils.logger import get_logger
from utils.notification_manager import notify
from utils.constants import ICON_ACCOUNT, ICON_SUCCESS, MSG_NO_ACCOUNT
from utils.validators import validate_time_format, format_time
from ui.components.svg_icons import svg

logger = get_logger()


class AccountsPage:
    """Page de gestion des comptes Telegram."""
    
    def __init__(self, telegram_manager: TelegramManager, app):
        """
        Initialise la page des comptes.
        
        Args:
            telegram_manager: Gestionnaire de comptes Telegram
            app: Instance de l'application principale
        """
        self.telegram_manager = telegram_manager
        self.app = app
        self.session_manager = SessionManager()
    
    def render(self) -> None:
        """Rend la page des comptes."""
        with ui.column().classes('w-full gap-6 p-8'):
            # En-tête
            with ui.row().classes('items-center gap-3 mb-2'):
                ui.html(svg(ICON_ACCOUNT, 40, 'var(--primary)'))
                ui.label('Comptes Telegram').classes('text-3xl font-bold').style(
                    'color: var(--text-primary);'
                )
            
            # Bouton ajouter
            with ui.button(on_click=self.app.add_account_dialog).classes('btn-primary mb-2'):
                with ui.row().classes('items-center gap-2'):
                    ui.html(svg('add_circle', 20, 'white'))
                    ui.label('Ajouter un compte')
            
            # Sous-titre
            with ui.row().classes('w-full justify-center'):
                ui.label('Gérez vos comptes Telegram connectés').classes('text-sm').style(
                    'color: var(--text-secondary);'
                )
            
            ui.separator().style('background: var(--border); height: 1px; border: none; margin: 16px 0;')
            
            # Liste des comptes
            self._render_accounts_grid()
    
    def _render_accounts_grid(self) -> None:
        """Rend la grille des comptes."""
        # Forcer le rechargement des settings pour avoir les infos à jour
        accounts = self.telegram_manager.list_accounts(reload_settings=True)
        
        if accounts:
            with ui.column().classes('w-full items-center'):
                # Organiser par groupes de 4
                for i in range(0, len(accounts), 4):
                    row_accounts = accounts[i:i+4]
                    
                    with ui.row().classes('gap-6 mb-6'):
                        for account in row_accounts:
                            self._render_account_card(account)
        else:
            with ui.card().classes('w-full p-8 card-modern text-center'):
                ui.html(svg('remove_circle', 60, 'var(--secondary)'))
                ui.label(MSG_NO_ACCOUNT).classes('text-lg font-semibold mb-2').style(
                    'color: var(--text-secondary);'
                )
                ui.label('Ajoutez votre premier compte Telegram pour commencer').classes('text-sm').style(
                    'color: var(--text-secondary); opacity: 0.7;'
                )
    
    def _render_account_card(self, account: dict) -> None:
        """
        Rend une carte de compte.
        
        Args:
            account: Dictionnaire avec les informations du compte
        """
        is_connected = account.get('is_connected', False)
        is_master = account.get('settings', {}).get('is_master', False)
        session_id = account.get('session_id')
        
        # Style doré élégant pour le compte maître
        if is_master:
            card_style = '''
                border: 2px solid #D4AF37;
                background: linear-gradient(135deg, #FFF8DC 0%, #FFFAEB 50%, #FFF8DC 100%);
                box-shadow: 0 4px 20px rgba(212, 175, 55, 0.3), 0 0 0 1px rgba(212, 175, 55, 0.1);
                position: relative;
            '''
        else:
            card_style = ''
        
        with ui.card().classes('p-4 card-modern').style(
            f'width: 300px; height: 120px; flex-shrink: 0; display: flex; flex-direction: row; gap: 12px; {card_style}'
        ) as card:
            # Badge couronne pour le compte maître
            if is_master:
                from ui.components.svg_icons import svg as svg_icon
                ui.html(f'''
                    <div style="
                        position: absolute;
                        top: -8px;
                        right: 10px;
                        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
                        color: white;
                        padding: 2px 8px;
                        border-radius: 12px;
                        font-size: 11px;
                        font-weight: bold;
                        box-shadow: 0 2px 8px rgba(212, 175, 55, 0.4);
                        border: 1px solid #D4AF37;
                        display: flex;
                        align-items: center;
                        gap: 4px;
                    ">{svg_icon('crown', 14, 'white')} MAÎTRE</div>
                ''')
            
            # Photo de profil (cliquable)
            with ui.element('div').classes('flex-shrink-0').style('width: 80px; height: 80px;'):
                # Conteneur avec click handler pour modifier la photo
                async def change_photo():
                    """Ouvre un dialogue pour changer la photo de profil."""
                    await self.open_photo_change_dialog(account)
                
                # Récupérer la photo de profil depuis le cache local
                from utils.paths import get_temp_dir
                photo_path = get_temp_dir() / "photos" / f"profile_{session_id}.jpg"
                
                if photo_path.exists():
                    # CORRECTION : Utiliser base64 pour PyInstaller avec HTML direct
                    from utils.paths import get_image_base64_data
                    base64_data = get_image_base64_data(str(photo_path))
                    if base64_data:
                        # Afficher la photo avec HTML direct pour éviter les problèmes NiceGUI
                        ui.html(f'''
                            <div style="
                                position: relative; width: 80px; height: 80px; cursor: pointer; 
                                border-radius: 50%; overflow: hidden; border: 3px solid var(--primary);
                                display: inline-block;
                            " onclick="window.photoChangeHandler_{session_id}()">
                                <img src="{base64_data}" style="width: 100%; height: 100%; object-fit: cover;" />
                                <div style="
                                    position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                                    background: rgba(0,0,0,0.5); display: flex; align-items: center;
                                    justify-content: center; opacity: 0; transition: opacity 0.2s;
                                    pointer-events: none;
                                " onmouseenter="this.style.opacity='1'" onmouseleave="this.style.opacity='0'">
                                    <span style="color: white; font-size: 12px; font-weight: bold;">Modifier</span>
                                </div>
                            </div>
                        ''')
                        
                        # Créer le handler JavaScript pour le clic
                        ui.run_javascript(f'''
                            window.photoChangeHandler_{session_id} = function() {{
                                // Déclencher l'événement de changement de photo
                                console.log('Photo change requested for session {session_id}');
                            }};
                        ''')
                else:
                    # Avatar par défaut avec initiales
                    account_name = account.get('account_name', 'U')
                    initials = ''.join([word[0].upper() for word in account_name.split()[:2]])
                    with ui.element('div').style(
                        'width: 80px; height: 80px; border-radius: 50%; '
                        'background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); '
                        'display: flex; align-items: center; justify-content: center; '
                        'color: white; font-size: 28px; font-weight: bold; cursor: pointer; '
                        'border: 3px solid var(--primary);'
                    ).on('click', change_photo):
                        ui.label(initials)
            
            # Contenu de la carte
            with ui.column().classes('flex-1 h-full justify-between min-w-0'):
                # Header avec status et infos
                with ui.column().classes('gap-1 flex-1'):
                    with ui.row().classes('w-full items-center gap-1'):
                        with ui.row().classes('items-center gap-2 flex-1 min-w-0'):
                            # Icône couronne pour le compte maître
                            if is_master:
                                ui.html(svg('crown', 20, '#D4AF37')).style('filter: drop-shadow(0 2px 4px rgba(212, 175, 55, 0.5)); flex-shrink: 0;')
                            
                            # Status badge
                            status_class = 'status-online' if is_connected else 'status-offline'
                            ui.html(f'<span class="status-badge {status_class}"></span>').style('flex-shrink: 0;')
                            
                            # Nom du compte avec couleur dorée pour le maître
                            text_color = '#B8860B' if is_master else 'var(--text-primary)'
                            ui.label(account.get('account_name', 'Sans nom')).classes(
                                'text-base font-bold'
                            ).style(
                                f'color: {text_color}; white-space: nowrap; overflow: hidden; '
                                'text-overflow: ellipsis;'
                            )
                    
                    # Numéro de téléphone
                    ui.label(account.get('phone', 'N/A')).classes('text-xs').style(
                        'color: var(--text-secondary);'
                    )
                    
                    # Boutons d'action
                    with ui.row().classes('w-full gap-1 items-center'):
                        # Bouton Paramètres
                        with ui.button(
                            on_click=lambda a=account: self.open_account_settings(a)
                        ).props('flat dense size=sm').style(
                            'color: var(--accent); font-size: 11px;'
                        ):
                            with ui.row().classes('items-center gap-1'):
                                ui.html(svg('settings', 14, 'var(--accent)'))
                                ui.label('Paramètres')
                        
                        # Bouton Supprimer
                        with ui.button(
                            on_click=lambda a=account: self.app.delete_account(a)
                        ).props('flat dense size=sm').style(
                            'color: var(--danger); font-size: 11px;'
                        ):
                            with ui.row().classes('items-center gap-1'):
                                ui.html(svg('delete', 14, '#ef4444'))
                                ui.label('Supprimer')
                        
                        # Bouton Reconnecter si nécessaire
                        if not is_connected:
                            with ui.button(
                                on_click=lambda a=account: self.app.reconnect_account(a)
                            ).props('flat dense size=sm').style('color: var(--warning); font-size: 11px;'):
                                with ui.row().classes('items-center gap-1'):
                                    ui.html(svg('sync', 14, 'var(--warning)'))
                                    ui.label('Reconnecter')
    
    async def open_photo_change_dialog(self, account: dict) -> None:
        """
        Ouvre un dialogue pour changer la photo de profil.
        
        Args:
            account: Dictionnaire avec les informations du compte
        """
        session_id = account.get('session_id')
        account_name = account.get('account_name', 'Sans nom')
        
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6 card-modern'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.html(svg('photo', 28, 'var(--primary)'))
                ui.label('Changer la photo de profil').classes('text-2xl font-bold').style(
                    'color: var(--text-primary);'
                )
            
            ui.label(f"Compte: {account_name}").classes('text-gray-600 mb-4')
            
            with ui.column().classes('w-full gap-4'):
                # Upload de fichier
                ui.label('Sélectionner une nouvelle photo').classes('font-medium')
                
                uploaded_file_path = {'path': None}
                
                async def handle_upload(e):
                    """Gère l'upload du fichier."""
                    try:
                        from utils.paths import get_temp_dir
                        import shutil
                        
                        # Sauvegarder le fichier uploadé
                        temp_dir = get_temp_dir() / "uploads"
                        temp_dir.mkdir(parents=True, exist_ok=True)
                        
                        file_path = temp_dir / e.name
                        with open(file_path, 'wb') as f:
                            f.write(e.content.read())
                        
                        uploaded_file_path['path'] = str(file_path)
                        notify('Photo chargée !', type='positive')
                    except Exception as error:
                        logger.error(f"Erreur upload photo: {error}")
                        notify(f'Erreur: {error}', type='negative')
                
                ui.upload(
                    on_upload=handle_upload,
                    auto_upload=True,
                    max_files=1
                ).props('accept="image/*"').classes('w-full')
                
                with ui.card().classes('bg-blue-50 p-3'):
                    with ui.row().classes('items-center gap-2'):
                        ui.html(svg('info', 18, '#1e40af'))
                        ui.label(
                            'Cette photo sera visible par tous vos contacts Telegram'
                        ).classes('text-sm text-blue-800')
                
                async def save_photo() -> None:
                    """Sauvegarde la nouvelle photo."""
                    if not uploaded_file_path['path']:
                        notify('Veuillez sélectionner une photo', type='warning')
                        return
                    
                    try:
                        notify('Mise à jour de la photo...', type='info')
                        success, error = await self.telegram_manager.update_account_profile_photo(
                            session_id,
                            uploaded_file_path['path']
                        )
                        
                        if success:
                            notify('Photo de profil mise à jour !', type='positive')
                            dialog.close()
                            # Rafraîchir la page
                            self.app.show_page('comptes')
                        else:
                            notify(f'Erreur: {error}', type='negative')
                    except Exception as e:
                        logger.error(f"Erreur sauvegarde photo: {e}")
                        notify(f'Erreur: {e}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat').style(
                        'color: var(--secondary);'
                    )
                    with ui.button(on_click=save_photo).classes('btn-primary'):
                        ui.html(svg('save', 18, 'white'))
                        ui.label('Sauvegarder').classes('ml-1')
        
        dialog.open()
    
    def open_account_settings(self, account: dict) -> None:
        """
        Ouvre le dialogue de paramètres d'un compte.
        
        Args:
            account: Dictionnaire avec les informations du compte
        """
        session_id = account.get('session_id')
        account_name = account.get('account_name', 'Sans nom')
        phone = account.get('phone')
        
        # Charger les paramètres actuels
        settings = self.session_manager.get_account_settings(session_id)
        is_master = settings.get('is_master', False)
        can_unset_master = self.session_manager.can_unset_master(session_id)
        
        with ui.dialog() as dialog, ui.card().classes('w-[600px] p-6 card-modern'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.html(svg('settings', 28, 'var(--text-primary)'))
                ui.label('Paramètres du compte').classes('text-2xl font-bold').style(
                    'color: var(--text-primary);'
                )
            ui.label(f"{account_name} ({phone})").classes('text-gray-600 mb-4')
            
            with ui.column().classes('w-full gap-4'):
                # Compte maître
                with ui.card().classes('p-4 bg-yellow-50 border-2 border-yellow-200'):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.html(svg('crown', 22, '#D97706'))
                        ui.label('Compte Maître').classes('font-bold text-lg').style('color: #D97706;')
                    ui.label(
                        'Le compte maître est utilisé pour afficher les groupes en commun et y répondre. '
                        'Un seul compte peut être maître à la fois.'
                    ).classes('text-sm text-gray-600 mb-3')
                    
                    master_checkbox = ui.checkbox('Définir comme compte maître', value=is_master).classes('font-semibold')
                    
                    # Désactiver la case si c'est le seul compte et qu'il est maître
                    if is_master and not can_unset_master:
                        master_checkbox.disable()
                        with ui.row().classes('items-center gap-1 mt-1'):
                            ui.html(svg('warning', 14, '#ea580c'))
                            ui.label('Impossible de décocher (compte unique)').classes('text-xs text-orange-600')
                
                ui.separator()
                
                # Nom du compte Telegram (modifiable et synchronisé avec Telegram)
                with ui.card().classes('p-4 bg-purple-50 border-2 border-purple-200'):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.html(svg('person', 22, '#7c3aed'))
                        ui.label('Nom Telegram').classes('font-bold text-lg').style('color: #7c3aed;')
                    ui.label(
                        'Ce nom sera visible par tous vos contacts Telegram lors de l\'envoi de messages'
                    ).classes('text-sm text-gray-600 mb-3')
                    
                    ui.label('Nom complet').classes('font-medium text-sm')
                    # Input HTML natif
                    name_html = f'''
                    <input 
                        type="text"
                        id="name_input_native"
                        value="{account_name}"
                        style="
                            width: 520px;
                            max-width: 100%;
                            height: 56px;
                            background: #ffffff;
                            border: 2px solid #d1d5db;
                            border-radius: 8px;
                            font-size: 16px;
                            padding: 14px 16px;
                            box-sizing: border-box;
                            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        "
                    />
                    '''
                    name_input = ui.html(name_html).classes('w-full')
                    
                    with ui.row().classes('items-center gap-1 mt-2'):
                        ui.html(svg('info', 14, '#7c3aed'))
                        ui.label('Vous pouvez mettre un prénom et nom de famille séparés par un espace').classes('text-xs').style('color: #7c3aed;')
                
                ui.separator()
                
                # Message par défaut
                ui.label('Message par défaut').classes('font-medium')
                # Textarea HTML natif
                default_msg = settings.get('default_message', '')
                message_html = f'''
                <textarea 
                    id="message_input_native"
                    rows="4"
                    style="
                        width: 520px;
                        max-width: 100%;
                        background: #ffffff;
                        border: 2px solid #d1d5db;
                        border-radius: 8px;
                        font-size: 16px;
                        padding: 14px 16px;
                        resize: vertical;
                        box-sizing: border-box;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    "
                >{default_msg}</textarea>
                '''
                message_input = ui.html(message_html).classes('w-full')
                
                # Horaires prédéfinis
                ui.label('Horaires prédéfinis').classes('font-medium')
                
                schedules_list = settings.get('default_schedules', []).copy()
                schedules_container = ui.column().classes('w-full gap-2')
                
                def render_schedules() -> None:
                    """Affiche la liste des horaires."""
                    schedules_container.clear()
                    with schedules_container:
                        if schedules_list:
                            for schedule in sorted(schedules_list):
                                with ui.card().classes('w-full p-2 bg-gray-50'):
                                    with ui.row().classes('w-full items-center gap-2'):
                                        ui.html(svg('access_time', 18, 'var(--text-secondary)'))
                                        ui.label(schedule).classes('flex-1')
                                        
                                        def make_delete_handler(s: str):
                                            def delete() -> None:
                                                schedules_list.remove(s)
                                                render_schedules()
                                            return delete
                                        
                                        with ui.button(
                                            on_click=make_delete_handler(schedule)
                                        ).props('flat dense size=sm').style('color: #ef4444;'):
                                            ui.html(svg('delete', 16, '#ef4444'))
                        else:
                            ui.label('Aucun horaire prédéfini').classes('text-gray-500 text-sm')
                
                # Ajouter un horaire
                with ui.row().classes('w-full gap-2 items-end'):
                    with ui.column().classes('flex-1'):
                        ui.label('Ajouter un horaire (HH:MM)').classes('text-sm text-gray-600')
                        # Input HTML natif
                        time_html = '''
                        <input 
                            type="text"
                            id="time_input_native"
                            placeholder="09:00"
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
                        />
                        '''
                        time_input = ui.html(time_html).classes('w-full')
                    
                    async def add_time() -> None:
                        """Ajoute un horaire."""
                        try:
                            time_str = await ui.run_javascript('document.getElementById("time_input_native").value', timeout=1.0) or ""
                            time_str = str(time_str).strip()
                        except Exception:
                            notify('Erreur de lecture de l\'horaire', type='negative')
                            return
                        
                        is_valid, error_msg = validate_time_format(time_str)
                        if not is_valid:
                            notify(error_msg, type='warning')
                            return
                        
                        formatted = format_time(time_str)
                        
                        if formatted in schedules_list:
                            notify('Cet horaire existe déjà', type='warning')
                            return
                        
                        schedules_list.append(formatted)
                        schedules_list.sort()
                        await ui.run_javascript('document.getElementById("time_input_native").value = ""')
                        render_schedules()
                        notify(f'{formatted} ajouté', type='positive')
                    
                    with ui.button(on_click=add_time).props('color=primary'):
                        with ui.row().classes('items-center gap-1'):
                            ui.html(svg('add_circle', 18, 'white'))
                            ui.label('Ajouter')
                
                render_schedules()
                
                with ui.card().classes('bg-blue-50 p-3 mt-2'):
                    with ui.row().classes('items-center gap-2'):
                        ui.html(svg('info', 18, '#1e40af'))
                        ui.label(
                            'Les horaires prédéfinis seront automatiquement proposés lors de la création de messages'
                        ).classes('text-sm text-blue-800')
                
                async def save() -> None:
                    """Sauvegarde les paramètres."""
                    try:
                        # Variable pour savoir si on doit rafraîchir
                        needs_full_refresh = False
                        
                        # Gérer le changement de compte maître
                        new_is_master = master_checkbox.value
                        if new_is_master != is_master:
                            needs_full_refresh = True  # Le compte maître a changé
                            if new_is_master:
                                # Définir ce compte comme maître (retire automatiquement les autres)
                                self.session_manager.set_master_account(session_id)
                                notify('Compte maître défini !', type='positive')
                            elif can_unset_master:
                                # Si on retire le statut maître, définir un autre compte comme maître
                                # Prendre le premier compte disponible
                                all_accounts = self.telegram_manager.list_accounts()
                                for acc in all_accounts:
                                    if acc['session_id'] != session_id:
                                        self.session_manager.set_master_account(acc['session_id'])
                                        notify(f'{acc["account_name"]} est maintenant le compte maître', type='info')
                                        break
                        
                        # Sauvegarder et mettre à jour le nom Telegram (sur Telegram ET localement)
                        try:
                            new_name = await ui.run_javascript('document.getElementById("name_input_native").value', timeout=1.0) or ""
                            new_name = str(new_name).strip()
                        except Exception:
                            new_name = ""
                        
                        if new_name and new_name != account_name:
                            notify('Mise à jour du nom sur Telegram...', type='info')
                            success, error = await self.telegram_manager.update_account_profile_name(session_id, new_name)
                            if success:
                                notify('Nom Telegram mis à jour !', type='positive')
                                needs_full_refresh = True
                            else:
                                notify(f'Erreur mise à jour nom: {error}', type='warning')
                        
                        # Sauvegarder les paramètres
                        try:
                            new_message = await ui.run_javascript('document.getElementById("message_input_native").value', timeout=1.0) or ""
                            new_message = str(new_message).strip()
                        except Exception:
                            new_message = ""
                        self.session_manager.update_account_settings(
                            session_id,
                            default_message=new_message,
                            default_schedules=schedules_list
                        )
                        
                        dialog.close()
                        
                        # Rafraîchir la page pour afficher les changements
                        if needs_full_refresh:
                            notify('Paramètres sauvegardés ! Actualisation...', type='positive')
                            # Double rafraîchissement pour être sûr que ça prend
                            self.app.show_page('comptes')
                        else:
                            notify('Paramètres sauvegardés !', type='positive')
                            self.app.show_page('comptes')
                        
                    except Exception as e:
                        logger.error(f"Erreur sauvegarde paramètres: {e}")
                        notify(f'Erreur: {e}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat').style(
                        'color: var(--secondary);'
                    )
                    with ui.button(on_click=save).classes('btn-primary'):
                        ui.html(svg('save', 18, 'white'))
                        ui.label('Sauvegarder').classes('ml-1')
        
        dialog.open()

