"""
Page de gestion des messages programmés
"""
import asyncio
from nicegui import ui
from utils.logger import get_logger

logger = get_logger()


class ScheduledMessagesPage:
    """Page de gestion des messages programmés"""
    
    def __init__(self, telegram_manager):
        self.telegram_manager = telegram_manager
        self.selected_account = None
        self.messages_container = None
        self.current_messages = []  # Cache des messages chargés
    
    def render(self):
        """Rendu de la page"""
        with ui.column().classes('w-full gap-6 p-8'):
            # En-tête moderne
            with ui.row().classes('items-center gap-3 mb-2'):
                ui.label('⏱').classes('text-4xl').style('color: var(--primary);')
                ui.label('Messages Programmés').classes('text-3xl font-bold').style('color: var(--text-primary);')
            ui.label('Gérez tous vos messages programmés').classes('text-sm').style('color: var(--text-secondary);')
            ui.separator().style('background: var(--border); height: 1px; border: none; margin: 16px 0;')
            
            # Sélection du compte
            with ui.card().classes('w-full p-5 mb-4 card-modern'):
                ui.label('Sélectionnez un compte').classes('text-lg font-bold mb-3').style('color: var(--text-primary);')
                
                accounts = self.telegram_manager.list_accounts()
                connected_accounts = [acc for acc in accounts if acc.get('is_connected', False)]
                
                if not connected_accounts:
                    ui.label('✕ Aucun compte connecté').classes('font-semibold').style('color: var(--danger);')
                else:
                    with ui.row().classes('gap-3 flex-wrap'):
                        for account in connected_accounts:
                            is_selected = self.selected_account == account['session_id']
                            
                            def make_select_handler(sid, name):
                                async def select_account():
                                    self.selected_account = sid
                                    ui.notify(f'Compte sélectionné: {name}', type='info')
                                    await self.load_scheduled_messages()
                                return select_account
                            
                            if is_selected:
                                ui.button(f"● {account['account_name']}", 
                                        on_click=make_select_handler(account['session_id'], account['account_name'])).classes('btn-primary')
                            else:
                                ui.button(f"○ {account['account_name']}", 
                                        on_click=make_select_handler(account['session_id'], account['account_name'])).props('outline').style('color: var(--text-secondary);')
            
            # Container pour les messages
            self.messages_container = ui.column().classes('w-full')
    
    async def load_scheduled_messages(self):
        """Charge les messages programmés"""
        if not self.selected_account:
            return
        
        self.messages_container.clear()
        
        with self.messages_container:
            # Dialog de chargement avec info
            with ui.card().classes('w-full p-8 card-modern text-center'):
                with ui.column().classes('w-full items-center gap-4'):
                    ui.spinner(size='lg').style('color: var(--primary);')
                    ui.label('Analyse en cours...').classes('text-xl font-bold mt-2').style('color: var(--text-primary);')
                    ui.label('Scan exhaustif de vos groupes et messages programmés').classes('text-sm').style('color: var(--text-secondary);')
                    ui.label('Veuillez patienter quelques instants').classes('text-xs').style('color: var(--text-secondary); opacity: 0.7;')
        
        # Récupérer le compte
        account = self.telegram_manager.get_account(self.selected_account)
        if not account:
            self.messages_container.clear()
            with self.messages_container:
                with ui.card().classes('w-full p-4 bg-red-50'):
                    ui.label('❌ Compte introuvable').classes('text-red-700')
            return
        
        try:
            # Récupérer tous les messages programmés
            scheduled_messages = await account.get_all_scheduled_messages()
            self.current_messages = scheduled_messages  # Sauvegarder dans le cache
            
            self.display_messages()
        
        except Exception as e:
            logger.error(f"Erreur chargement messages programmés: {e}")
            self.messages_container.clear()
            with self.messages_container:
                with ui.card().classes('w-full p-4 bg-red-50'):
                    ui.label('❌ Erreur lors du chargement').classes('text-red-700 font-bold')
                    ui.label(str(e)).classes('text-sm text-red-600')
    
    def display_messages(self):
        """Affiche les messages depuis le cache (sans rescan)"""
        self.messages_container.clear()
        
        account = self.telegram_manager.get_account(self.selected_account)
        if not account:
            return
        
        with self.messages_container:
            if self.current_messages:
                # Boutons d'action globaux
                with ui.row().classes('w-full gap-3 mb-4'):
                    # Bouton rafraîchir
                    async def refresh():
                        ui.notify('↻ Rechargement...', type='info')
                        await self.load_scheduled_messages()
                    
                    ui.button('↻ Rafraîchir', on_click=refresh).props('outline').style('color: var(--accent);')
                    
                    # Bouton supprimer TOUT de TOUS les groupes
                    def delete_all_everywhere():
                        with ui.dialog() as dialog, ui.card().classes('p-6 card-modern'):
                            ui.label('⚠ ATTENTION').classes('text-2xl font-bold mb-4').style('color: var(--danger);')
                            ui.label(f'Supprimer TOUS les {len(self.current_messages)} messages programmés de TOUS les groupes ?').classes('text-lg font-bold mb-2')
                            ui.label('Cette action est IRRÉVERSIBLE et supprimera tous les messages programmés du compte.').classes('text-sm text-gray-600 mb-4')
                            
                            async def confirm_delete_all():
                                try:
                                    dialog.close()
                                    ui.notify('🗑️ Suppression de tous les messages...', type='warning')
                                    
                                    # Grouper par chat
                                    chats = {}
                                    for msg in self.current_messages:
                                        if msg['chat_id'] not in chats:
                                            chats[msg['chat_id']] = []
                                        chats[msg['chat_id']].append(msg['message_id'])
                                    
                                    # Supprimer tous les messages de chaque chat
                                    deleted_count = 0
                                    for chat_id, msg_ids in chats.items():
                                        success, error = await account.delete_scheduled_messages(chat_id, msg_ids)
                                        if success:
                                            deleted_count += len(msg_ids)
                                    
                                    ui.notify(f'✅ {deleted_count} message(s) supprimé(s) !', type='positive')
                                    
                                    # Vider le cache et réafficher
                                    self.current_messages = []
                                    self.display_messages()
                                    
                                except Exception as e:
                                    logger.error(f"Erreur suppression totale: {e}")
                                    ui.notify(f'❌ Erreur: {e}', type='negative')
                            
                            with ui.row().classes('w-full justify-end gap-2'):
                                ui.button('Annuler', on_click=dialog.close).props('flat').style('color: var(--secondary);')
                                ui.button('✕ TOUT SUPPRIMER', on_click=confirm_delete_all).props('color=red')
                        
                        dialog.open()
                    
                    ui.button('✕ Tout supprimer (TOUS)', on_click=delete_all_everywhere).props('color=red')
                
                # Grouper par chat
                chats_dict = {}
                for msg in self.current_messages:
                    chat_id = msg['chat_id']
                    if chat_id not in chats_dict:
                        chats_dict[chat_id] = {
                            'title': msg['chat_title'],
                            'messages': []
                        }
                    chats_dict[chat_id]['messages'].append(msg)
                
                # Afficher par groupe
                with ui.card().classes('w-full p-5 mb-4').style('background: #ecfdf5; border-left: 3px solid var(--success);'):
                    ui.label(f'✓ {len(self.current_messages)} message(s) programmé(s) dans {len(chats_dict)} groupe(s)').classes('text-lg font-bold').style('color: #065f46;')
                
                for chat_id, chat_data in chats_dict.items():
                    with ui.card().classes('w-full p-5 mb-4 card-modern'):
                        # En-tête du groupe
                        with ui.row().classes('w-full items-center gap-3 mb-4'):
                            ui.label(f'● {chat_data["title"]}').classes('text-lg font-bold flex-1').style('color: var(--text-primary);')
                            ui.label(f'{len(chat_data["messages"])} message(s)').classes('px-3 py-1 rounded text-sm font-semibold').style('background: rgba(30, 58, 138, 0.1); color: var(--primary);')
                            
                            # Bouton supprimer tous les messages de ce groupe
                            def make_delete_all_handler(cid, title):
                                def delete_all():
                                    with ui.dialog() as dialog, ui.card().classes('p-4'):
                                        ui.label(f'⚠️ Supprimer tous les messages de "{title}" ?').classes('text-lg font-bold mb-3')
                                        ui.label('Cette action est irréversible.').classes('text-sm text-gray-600 mb-4')
                                        
                                        async def confirm():
                                            try:
                                                ui.notify('Suppression en cours...', type='info')
                                                success, error = await account.delete_scheduled_messages(cid, None)
                                                if success:
                                                    dialog.close()
                                                    ui.notify('✅ Messages supprimés !', type='positive')
                                                    # Mettre à jour le cache local (enlever les messages de ce chat)
                                                    self.current_messages = [msg for msg in self.current_messages if msg['chat_id'] != cid]
                                                    self.display_messages()
                                                else:
                                                    ui.notify(f'❌ Erreur: {error}', type='negative')
                                            except Exception as e:
                                                logger.error(f"Erreur suppression: {e}")
                                                ui.notify(f'❌ Erreur: {e}', type='negative')
                                        
                                        with ui.row().classes('w-full justify-end gap-2'):
                                            ui.button('Annuler', on_click=dialog.close).props('flat')
                                            ui.button('Supprimer tout', on_click=confirm).props('color=red')
                                    
                                    dialog.open()
                                return delete_all
                            
                            ui.button('✕ Tout supprimer', on_click=make_delete_all_handler(chat_id, chat_data['title'])).props('flat dense').style('color: var(--danger);')
                        
                        # Liste des messages
                        with ui.column().classes('w-full gap-2'):
                            for msg in sorted(chat_data['messages'], key=lambda x: x['date']):
                                with ui.card().classes('w-full p-4').style('background: var(--bg-secondary); border: 1px solid var(--border);'):
                                    with ui.row().classes('w-full items-start gap-3'):
                                        with ui.column().classes('flex-1 gap-2'):
                                            # Date et heure
                                            ui.label(msg['date'].strftime('%d/%m/%Y %H:%M')).classes('font-bold').style('color: var(--primary);')
                                            
                                            # Texte du message
                                            text = msg['text'][:100] + ('...' if len(msg['text']) > 100 else '')
                                            ui.label(text).classes('text-sm').style('color: var(--text-primary);')
                                            
                                            # Média si présent
                                            if msg['has_media']:
                                                ui.label(f'📎 {msg["media_type"]}').classes('text-xs').style('color: var(--accent);')
                                        
                                        # Bouton supprimer ce message
                                        def make_delete_msg_handler(cid, mid):
                                            async def delete_msg():
                                                try:
                                                    ui.notify('Suppression...', type='info')
                                                    success, error = await account.delete_scheduled_messages(cid, [mid])
                                                    if success:
                                                        ui.notify('✅ Message supprimé', type='positive')
                                                        # Mettre à jour le cache local (enlever ce message spécifique)
                                                        self.current_messages = [m for m in self.current_messages if not (m['chat_id'] == cid and m['message_id'] == mid)]
                                                        self.display_messages()
                                                    else:
                                                        ui.notify(f'❌ Erreur: {error}', type='negative')
                                                except Exception as e:
                                                    logger.error(f"Erreur suppression message: {e}")
                                                    ui.notify(f'❌ Erreur: {e}', type='negative')
                                            return delete_msg
                                        
                                        ui.button('✕', on_click=make_delete_msg_handler(chat_id, msg['message_id'])).props('flat dense').style('color: var(--danger);')
            else:
                with ui.card().classes('w-full p-8 card-modern text-center'):
                    ui.label('●').classes('text-5xl mb-3').style('color: var(--secondary); opacity: 0.3;')
                    ui.label('Aucun message programmé').classes('text-xl font-bold mb-2').style('color: var(--text-secondary);')
                    ui.label('Les messages que vous programmez apparaîtront ici.').classes('text-sm').style('color: var(--text-secondary); opacity: 0.7;')
