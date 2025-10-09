"""
Page de gestion des comptes Telegram
"""
from nicegui import ui
from utils.logger import get_logger

logger = get_logger()


class AccountsPage:
    """Page de gestion des comptes"""
    
    def __init__(self, telegram_manager, app=None):
        self.telegram_manager = telegram_manager
        self.app = app
        self.temp_phone = None
        self.temp_session_id = None
    
    def render(self):
        """Rendu de la page des comptes"""
        with ui.column().classes('w-full gap-4 p-6'):
            ui.label('📱 Compte Telegram').classes('text-3xl font-bold')
            ui.separator()
            
            # Liste des comptes
            accounts = self.telegram_manager.list_accounts()
            
            if accounts:
                for account in accounts:
                    with ui.card().classes('w-full p-4'):
                        with ui.row().classes('w-full items-center gap-4'):
                            status_icon = '🟢' if account.get('is_connected', False) else '🔴'
                            ui.label(f"{status_icon} {account.get('account_name', 'Sans nom')}").classes('text-lg font-bold')
                            ui.label(f"({account.get('phone', 'N/A')})").classes('text-gray-600')
                            ui.space()
                            
                            # Boutons d'action
                            with ui.row().classes('gap-2'):
                                ui.button('⚙️ Paramètres', on_click=lambda a=account: self.open_account_settings(a)).props('flat color=blue')
                                if not account.get('is_connected', False):
                                    ui.button('🔄 Se reconnecter', on_click=lambda a=account: self.reconnect_account(a)).props('flat color=orange')
                                ui.button('🗑️ Supprimer', on_click=lambda a=account: self.delete_account(a)).props('flat color=red')
            else:
                with ui.card().classes('w-full p-6'):
                    ui.label('Aucun compte configuré').classes('text-gray-600')
                    ui.label('Cliquez sur "Ajouter un compte" pour commencer').classes('text-sm text-gray-500 mt-2')
            
            # Bouton ajouter
            ui.button('➕ Ajouter un compte', on_click=self.add_account_dialog).props('color=primary size=lg').classes('w-full')
    
    async def add_account_dialog(self):
        """Dialogue pour ajouter un compte"""
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6'):
            ui.label('➕ Ajouter un compte Telegram').classes('text-2xl font-bold mb-4')
            
            with ui.column().classes('w-full gap-4'):
                ui.label('Nom de compte').classes('font-medium')
                name_input = ui.input(placeholder='Ex: Mon Compte Pro').classes('w-full')
                
                ui.label('Numéro de téléphone').classes('font-medium')
                phone_input = ui.input(placeholder='+33612345678').classes('w-full')
                
                with ui.card().classes('bg-blue-50 p-3'):
                    ui.label('✅ Simple : Entrez votre numéro, recevez le code, connectez-vous !').classes('text-sm text-blue-800')
                
                async def submit():
                    name = name_input.value.strip()
                    phone = phone_input.value.strip()
                    
                    if not name:
                        ui.notify('Veuillez entrer un nom de compte', type='warning')
                        return
                    
                    if not phone:
                        ui.notify('Veuillez entrer un numéro de téléphone', type='warning')
                        return
                    
                    if not phone.startswith('+'):
                        ui.notify('Le numéro doit commencer par + (ex: +33612345678)', type='warning')
                        return
                    
                    try:
                        ui.notify('Envoi du code de vérification...', type='info')
                        
                        # Ajouter le compte et envoyer le code
                        success, message, session_id = await self.telegram_manager.add_account(phone, name)
                        
                        if success:
                            self.temp_phone = phone
                            self.temp_session_id = session_id
                            ui.notify('Code envoyé ! Vérifiez votre Telegram', type='positive')
                            
                            # Créer le dialog de vérification
                            verification_dialog = ui.dialog().props('persistent')
                            
                            with verification_dialog, ui.card().classes('w-96 p-6'):
                                ui.label('🔐 Vérification').classes('text-2xl font-bold mb-4')
                                
                                with ui.column().classes('w-full gap-4'):
                                    ui.label(f'Compte: {phone}').classes('text-gray-600')
                                    
                                    ui.label('Code de vérification').classes('font-medium')
                                    code_input = ui.input(placeholder='12345').classes('w-full')
                                    
                                    ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                                    password_input = ui.input(placeholder='Laissez vide si pas de 2FA', password=True, password_toggle_button=True).classes('w-full')
                                    
                                    with ui.card().classes('bg-yellow-50 p-3'):
                                        ui.label('⚠️ Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram').classes('text-sm text-yellow-800')
                                    
                                    async def verify():
                                        code = code_input.value.strip()
                                        password = password_input.value.strip() if password_input.value else None
                                        
                                        if not code:
                                            ui.notify('Veuillez entrer le code de vérification', type='warning')
                                            return
                                        
                                        try:
                                            ui.notify('Vérification en cours...', type='info')
                                            
                                            success, error = await self.telegram_manager.verify_account(session_id, code, password)
                                            
                                            if success:
                                                verification_dialog.close()
                                                dialog.close()
                                                ui.notify('✅ Compte ajouté avec succès !', type='positive')
                                                self.temp_phone = None
                                                self.temp_session_id = None
                                                # Rafraîchir la page
                                                if self.app:
                                                    ui.timer(0.2, lambda: self.app.show_page('comptes'), once=True)
                                            else:
                                                ui.notify(f'❌ {error}', type='negative')
                                        
                                        except Exception as e:
                                            logger.error(f"Erreur vérification: {e}")
                                            ui.notify(f'Erreur: {e}', type='negative')
                                    
                                    with ui.row().classes('w-full justify-end gap-2 mt-4'):
                                        ui.button('Annuler', on_click=verification_dialog.close).props('flat')
                                        ui.button('Vérifier', on_click=verify).props('color=primary')
                            
                            verification_dialog.open()
                        else:
                            ui.notify(f'Erreur: {message}', type='negative')
                    
                    except Exception as e:
                        logger.error(f"Erreur ajout compte: {e}")
                        ui.notify(f'Erreur: {e}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat')
                    ui.button('Continuer', on_click=submit).props('color=primary')
        
        dialog.open()
    
    async def reconnect_account(self, account):
        """Reconnecte un compte non autorisé"""
        session_id = account.get('session_id')
        phone = account.get('phone')
        
        try:
            # Renvoyer le code
            ui.notify('Envoi du nouveau code de vérification...', type='info')
            success, message = await self.telegram_manager.resend_code(session_id)
            
            if success:
                # Stocker les infos temporaires
                self.temp_phone = phone
                self.temp_session_id = session_id
                
                ui.notify('Code envoyé ! Vérifiez votre Telegram', type='positive')
                
                # Créer le dialog de vérification
                verification_dialog = ui.dialog().props('persistent')
                
                with verification_dialog, ui.card().classes('w-96 p-6'):
                    ui.label('🔄 Reconnexion').classes('text-2xl font-bold mb-4')
                    
                    with ui.column().classes('w-full gap-4'):
                        ui.label(f'Compte: {phone}').classes('text-gray-600')
                        
                        ui.label('Code de vérification').classes('font-medium')
                        code_input = ui.input(placeholder='12345').classes('w-full')
                        
                        ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                        password_input = ui.input(placeholder='Laissez vide si pas de 2FA', password=True, password_toggle_button=True).classes('w-full')
                        
                        with ui.card().classes('bg-orange-50 p-3'):
                            ui.label('⚠️ Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram').classes('text-sm text-orange-800')
                        
                        async def verify():
                            code = code_input.value.strip()
                            password = password_input.value.strip() if password_input.value else None
                            
                            if not code:
                                ui.notify('Veuillez entrer le code de vérification', type='warning')
                                return
                            
                            try:
                                ui.notify('Vérification en cours...', type='info')
                                
                                success, error = await self.telegram_manager.verify_account(session_id, code, password)
                                
                                if success:
                                    verification_dialog.close()
                                    ui.notify('✅ Compte reconnecté avec succès !', type='positive')
                                    self.temp_phone = None
                                    self.temp_session_id = None
                                    # Rafraîchir la page
                                    if self.app:
                                        ui.timer(0.2, lambda: self.app.show_page('comptes'), once=True)
                                else:
                                    ui.notify(f'❌ {error}', type='negative')
                            
                            except Exception as e:
                                logger.error(f"Erreur vérification reconnexion: {e}")
                                ui.notify(f'Erreur: {e}', type='negative')
                        
                        with ui.row().classes('w-full justify-end gap-2 mt-4'):
                            ui.button('Annuler', on_click=verification_dialog.close).props('flat')
                            ui.button('Vérifier', on_click=verify).props('color=primary')
                
                verification_dialog.open()
            else:
                ui.notify(f'Erreur: {message}', type='negative')
                
        except Exception as e:
            logger.error(f"Erreur reconnexion compte: {e}")
            ui.notify(f'Erreur: {e}', type='negative')
    
    async def delete_account(self, account):
        """Supprime un compte"""
        session_id = account.get('session_id')
        phone = account.get('phone')
        
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6'):
            ui.label('⚠️ Supprimer le compte ?').classes('text-xl font-bold text-red-600 mb-4')
            ui.label(f'Compte: {account.get("account_name")} ({phone})').classes('text-gray-700')
            ui.label('Cette action est irréversible.').classes('text-sm text-gray-500 mt-2')
            
            async def confirm():
                try:
                    await self.telegram_manager.remove_account(session_id)
                    dialog.close()
                    ui.notify('✅ Compte supprimé', type='positive')
                    # Rafraîchir la page
                    if self.app:
                        ui.timer(0.2, lambda: self.app.show_page('comptes'), once=True)
                except Exception as e:
                    ui.notify(f'Erreur: {e}', type='negative')
            
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Annuler', on_click=dialog.close).props('flat')
                ui.button('Supprimer', on_click=confirm).props('color=red')
        
        dialog.open()
    
    def open_account_settings(self, account):
        """Ouvre le dialogue de paramètres d'un compte"""
        session_id = account.get('session_id')
        account_name = account.get('account_name', 'Sans nom')
        
        # Récupérer les paramètres actuels
        session_manager = self.telegram_manager.session_manager
        settings = session_manager.get_account_settings(session_id)
        
        with ui.dialog() as dialog, ui.card().classes('w-[600px] p-6'):
            ui.label(f'⚙️ Paramètres de {account_name}').classes('text-2xl font-bold mb-4')
            
            with ui.column().classes('w-full gap-3'):
                # Nom du compte
                ui.label('Nom du compte').classes('font-medium')
                account_name_input = ui.input(
                    placeholder='Ex: Mon Compte Pro',
                    value=account_name
                ).classes('w-full')
                
                ui.separator()
                
                # Message prédéfini
                ui.label('Message prédéfini').classes('font-medium')
                message_input = ui.textarea(
                    placeholder='Entrez votre message prédéfini...',
                    value=settings.get('default_message', '')
                ).classes('w-full').props('rows=3')
                
                ui.separator()
                
                # Horaires prédéfinis
                ui.label('Horaires prédéfinis').classes('font-medium')
                
                # Liste des horaires existants
                schedules_list = settings.get('default_schedules', [])
                schedules_container = ui.column().classes('w-full gap-1 mt-1')
                
                def update_schedules_display():
                    """Met à jour l'affichage des horaires"""
                    schedules_container.clear()
                    with schedules_container:
                        if schedules_list:
                            for i, time in enumerate(schedules_list):
                                with ui.card().classes('w-full p-2 bg-blue-50'):
                                    with ui.row().classes('w-full items-center gap-2'):
                                        ui.label(f'🕐 {time}').classes('flex-1 font-medium')
                                        
                                        def make_remove_handler(idx):
                                            def remove():
                                                schedules_list.pop(idx)
                                                update_schedules_display()
                                            return remove
                                        
                                        ui.button('🗑️', on_click=make_remove_handler(i)).props('flat dense color=red size=sm')
                        else:
                            ui.label('Aucun horaire défini').classes('text-gray-500 text-sm italic')
                
                update_schedules_display()
                
                # Ajouter un horaire
                with ui.row().classes('w-full gap-2 mt-2'):
                    time_input = ui.input(placeholder='HH:MM (ex: 09:00)').classes('flex-1')
                    
                    def add_schedule():
                        time_str = time_input.value.strip()
                        if time_str:
                            # Valider le format HH:MM
                            try:
                                parts = time_str.split(':')
                                if len(parts) == 2:
                                    hour = int(parts[0])
                                    minute = int(parts[1])
                                    if 0 <= hour <= 23 and 0 <= minute <= 59:
                                        formatted = f"{hour:02d}:{minute:02d}"
                                        if formatted not in schedules_list:
                                            schedules_list.append(formatted)
                                            schedules_list.sort()
                                            time_input.value = ''
                                            update_schedules_display()
                                        else:
                                            ui.notify('Horaire déjà présent', type='warning')
                                    else:
                                        ui.notify('Heure ou minute invalide', type='warning')
                                else:
                                    ui.notify('Format invalide (utilisez HH:MM)', type='warning')
                            except ValueError:
                                ui.notify('Format invalide (utilisez HH:MM)', type='warning')
                    
                    ui.button('➕ Ajouter', on_click=add_schedule).props('color=green')
                
                ui.separator()
                
                # Boutons d'action
                async def save_settings():
                    try:
                        new_name = account_name_input.value.strip()
                        new_message = message_input.value.strip()
                        
                        # Mettre à jour le nom du compte
                        if new_name and new_name != account_name:
                            self.telegram_manager.update_account_name(session_id, new_name)
                        
                        # Mettre à jour les paramètres
                        session_manager.update_account_settings(
                            session_id,
                            default_message=new_message,
                            default_schedules=schedules_list
                        )
                        
                        dialog.close()
                        ui.notify('✅ Paramètres sauvegardés', type='positive')
                        # Rafraîchir la page
                        if self.app:
                            ui.timer(0.2, lambda: self.app.show_page('comptes'), once=True)
                    except Exception as e:
                        logger.error(f"Erreur sauvegarde paramètres: {e}")
                        ui.notify(f'Erreur: {e}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat')
                    ui.button('💾 Sauvegarder', on_click=save_settings).props('color=primary')
        
        dialog.open()
