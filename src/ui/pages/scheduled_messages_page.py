"""
Page de gestion des messages programmés.
"""
import asyncio
from typing import Optional, List, Dict, Set, Tuple
from datetime import datetime
from nicegui import ui
from telethon.tl.functions.messages import GetScheduledHistoryRequest, DeleteScheduledMessagesRequest

from core.telegram.manager import TelegramManager
from ui.components.dialogs import ConfirmDialog
from utils.logger import get_logger
from utils.notification_manager import notify
from utils.constants import ICON_SCHEDULED, ICON_REFRESH, MSG_NO_CONNECTED_ACCOUNT
from ui.components.svg_icons import svg

logger = get_logger()


class ScheduledMessagesPage:
    """Page de gestion des messages programmés."""
    
    def __init__(self, telegram_manager: TelegramManager):
        """
        Initialise la page.
        
        Args:
            telegram_manager: Gestionnaire de comptes Telegram
        """
        self.telegram_manager = telegram_manager
        self.selected_account: Optional[str] = None
        self.messages_container: Optional[ui.column] = None
        self.current_messages: List[Dict] = []
        self.selected_chat_id: Optional[int] = None  # Filtre par groupe
        self.groups_menu_container: Optional[ui.row] = None  # Container pour le menu des groupes
        
        # Système de sélection pour édition
        self.selected_messages: Set[Tuple[int, int]] = set()  # Set de (chat_id, message_id)
        self.action_bar_container: Optional[ui.row] = None  # Barre d'action pour édition en lot
        self.checkboxes: Dict[Tuple[int, int], ui.checkbox] = {}  # Référence aux checkboxes
    
    def render(self) -> None:
        """Rend la page."""
        with ui.column().classes('w-full gap-6 p-8'):
            # En-tête
            with ui.row().classes('items-center gap-3 mb-2'):
                ui.html(svg('schedule', 40, 'var(--primary)'))
                ui.label('Messages Programmés').classes('text-3xl font-bold').style(
                    'color: var(--text-primary);'
                )
            
            ui.label('Gérez tous vos messages programmés').classes('text-sm').style(
                'color: var(--text-secondary);'
            )
            ui.separator().style('background: var(--border); height: 1px; border: none; margin: 16px 0;')
            
            # Sélection du compte
            self._render_account_selection()
            
            # Container pour les messages
            self.messages_container = ui.column().classes('w-full')
    
    def _render_account_selection(self) -> None:
        """Rend la sélection de compte."""
        with ui.card().classes('w-full p-5 mb-4 card-modern'):
            with ui.row().classes('w-full items-center justify-between mb-3'):
                ui.label('Sélectionnez un compte').classes('text-lg font-bold').style(
                    'color: var(--text-primary);'
                )
                
                # Bouton pour scanner tous les comptes
                with ui.button(
                    on_click=self.scan_all_accounts
                ).props('outline').style('color: var(--accent);'):
                    with ui.row().classes('items-center gap-2'):
                        ui.html(svg('search', 18, 'var(--accent)'))
                        ui.label('Scanner tous les comptes')
            
            accounts = self.telegram_manager.list_accounts()
            connected = [acc for acc in accounts if acc.get('is_connected', False)]
            
            if not connected:
                ui.label(f'{MSG_NO_CONNECTED_ACCOUNT}').classes('font-semibold').style(
                    'color: var(--danger);'
                )
            else:
                with ui.row().classes('gap-3 flex-wrap'):
                    for account in connected:
                        is_selected = self.selected_account == account['session_id']
                        
                        def make_select(sid: str, name: str):
                            async def select() -> None:
                                self.selected_account = sid
                                notify(f'Compte sélectionné: {name}', type='info')
                                await self.load_scheduled_messages()
                            return select
                        
                        if is_selected:
                            ui.button(
                                f"{account['account_name']}",
                                on_click=make_select(account['session_id'], account['account_name'])
                            ).classes('btn-primary')
                        else:
                            ui.button(
                                f"{account['account_name']}",
                                on_click=make_select(account['session_id'], account['account_name'])
                            ).props('outline').style('color: var(--text-secondary);')
    
    async def load_scheduled_messages(self) -> None:
        """Charge les messages programmés."""
        if not self.selected_account:
            return
        
        # Réinitialiser le filtre de groupe quand on change de compte
        self.selected_chat_id = None
        
        self.messages_container.clear()
        
        with self.messages_container:
            # Indicateur de chargement
            with ui.card().classes('w-full p-8 card-modern text-center'):
                with ui.column().classes('w-full items-center gap-4'):
                    ui.spinner(size='lg').style('color: var(--primary);')
                    ui.label('Analyse en cours...').classes('text-xl font-bold mt-2').style(
                        'color: var(--text-primary);'
                    )
                    ui.label('Scan exhaustif de vos groupes et messages programmés').classes('text-sm')
        
        # Récupérer le compte
        account = self.telegram_manager.get_account(self.selected_account)
        if not account:
            self.messages_container.clear()
            with self.messages_container:
                with ui.card().classes('w-full p-4 bg-red-50'):
                    ui.html(svg('error', 32, '#b91c1c'))
                    ui.label('Compte introuvable').classes('text-red-700')
            return
        
        try:
            # Récupérer tous les messages programmés
            scheduled_messages = await account.get_all_scheduled_messages()
            self.current_messages = scheduled_messages
            self.display_messages()
            
        except Exception as e:
            logger.error(f"Erreur chargement messages: {e}")
            self.messages_container.clear()
            with self.messages_container:
                with ui.card().classes('w-full p-4 bg-red-50'):
                    ui.html(svg('error', 32, '#b91c1c'))
                    ui.label('Erreur lors du chargement').classes('text-red-700 font-bold')
                    ui.label(str(e)).classes('text-sm text-red-600')
    
    def display_messages(self) -> None:
        """Affiche les messages depuis le cache."""
        self.messages_container.clear()
        
        account = self.telegram_manager.get_account(self.selected_account)
        if not account:
            return
        
        with self.messages_container:
            if self.current_messages:
                # Réinitialiser la sélection et les checkboxes
                self.selected_messages.clear()
                self.checkboxes.clear()
                
                # Boutons d'action
                with ui.row().classes('w-full gap-3 mb-4'):
                    async def refresh() -> None:
                        ui.notify('Rechargement...', type='info')
                        await self.load_scheduled_messages()
                    
                    with ui.button(on_click=refresh).props('outline').style('color: var(--accent);'):
                        with ui.row().classes('items-center gap-2'):
                            ui.html(svg('sync', 18, 'var(--accent)'))
                            ui.label('Rafraîchir')
                    
                    # Sélectionner tout
                    with ui.button(on_click=self._select_all_everywhere).props('outline').style('color: #10b981;'):
                        with ui.row().classes('items-center gap-2'):
                            ui.html(svg('check_circle', 18, '#10b981'))
                            ui.label('Tout sélectionner')
                    
                    with ui.button(on_click=self._delete_all_everywhere).props('color=red'):
                        with ui.row().classes('items-center gap-2'):
                            ui.html(svg('delete_forever', 18, 'white'))
                            ui.label('Tout supprimer (TOUS)')
                
                # Barre d'action pour l'édition (apparaît quand des messages sont sélectionnés)
                self.action_bar_container = ui.row().classes('w-full mb-4')
                
                # Menu de filtrage par groupe
                self._render_groups_filter_menu()
                
                # Filtrer les messages selon le groupe sélectionné
                filtered_messages = self.current_messages
                if self.selected_chat_id is not None:
                    filtered_messages = [
                        msg for msg in self.current_messages 
                        if msg['chat_id'] == self.selected_chat_id
                    ]
                
                # Grouper par chat (utiliser les messages filtrés)
                chats_dict: Dict[int, Dict] = {}
                for msg in filtered_messages:
                    chat_id = msg['chat_id']
                    if chat_id not in chats_dict:
                        chats_dict[chat_id] = {
                            'title': msg['chat_title'],
                            'messages': []
                        }
                    chats_dict[chat_id]['messages'].append(msg)
                
                # Résumé
                with ui.card().classes('w-full p-5 mb-4').style(
                    'background: #ecfdf5; border-left: 3px solid var(--success);'
                ):
                    if self.selected_chat_id is None:
                        ui.label(
                            f'{len(self.current_messages)} message(s) programmé(s) dans {len(chats_dict)} groupe(s)'
                        ).classes('text-lg font-bold').style('color: #065f46;')
                    else:
                        # Afficher le nom du groupe filtré
                        filtered_chat_title = next(
                            (msg['chat_title'] for msg in filtered_messages if msg['chat_id'] == self.selected_chat_id),
                            "Groupe inconnu"
                        )
                        ui.label(
                            f'{len(filtered_messages)} message(s) dans "{filtered_chat_title}"'
                        ).classes('text-lg font-bold').style('color: #065f46;')
                
                # Afficher par groupe
                for chat_id, chat_data in chats_dict.items():
                    self._render_chat_messages(chat_id, chat_data, account)
            else:
                # Aucun message
                with ui.card().classes('w-full p-8 card-modern text-center'):
                    ui.html(svg('remove_circle', 60, 'var(--secondary)'))
                    ui.label('Aucun message programmé').classes('text-xl font-bold mb-2').style(
                        'color: var(--text-secondary);'
                    )
                    ui.label('Les messages que vous programmez apparaîtront ici.').classes('text-sm').style(
                        'color: var(--text-secondary); opacity: 0.7;'
                    )
    
    def _render_chat_messages(self, chat_id: int, chat_data: Dict, account) -> None:
        """Rend les messages d'un chat."""
        with ui.card().classes('w-full p-5 mb-4 card-modern'):
            # En-tête du groupe
            with ui.row().classes('w-full items-center gap-3 mb-4'):
                with ui.row().classes('items-center gap-2 flex-1'):
                    ui.html(svg('chat', 18, 'var(--text-primary)'))
                    ui.label(f'{chat_data["title"]}').classes('text-lg font-bold').style(
                    'color: var(--text-primary);'
                )
                ui.label(f'{len(chat_data["messages"])} message(s)').classes(
                    'px-3 py-1 rounded text-sm font-semibold'
                ).style('background: rgba(30, 58, 138, 0.1); color: var(--primary);')
                
                # Bouton pour sélectionner tout le groupe
                def make_select_group(cid: int, msgs: List[Dict]):
                    def select_group():
                        self._select_all_in_group(cid, msgs)
                    return select_group
                
                with ui.button(
                    on_click=make_select_group(chat_id, chat_data['messages'])
                ).props('flat dense').style('color: #10b981;'):
                    with ui.row().classes('items-center gap-1'):
                        ui.html(svg('check_circle', 16, '#10b981'))
                        ui.label('Sélectionner tout')
                
                def make_delete_all(cid: int, title: str, acc, messages: List[Dict]):
                    async def on_confirm() -> None:
                        try:
                            ui.notify('Suppression en cours...', type='info')
                            # Extraire tous les IDs des messages de ce groupe
                            message_ids = [msg['message_id'] for msg in messages]
                            success, error = await acc.delete_scheduled_messages(cid, message_ids)
                            if success:
                                ui.notify(f'{len(message_ids)} message(s) supprimé(s) !', type='positive')
                                self.current_messages = [
                                    msg for msg in self.current_messages
                                    if msg['chat_id'] != cid
                                ]
                                self.display_messages()
                            else:
                                ui.notify(f'Erreur: {error}', type='negative')
                        except Exception as e:
                            logger.error(f"Erreur suppression: {e}")
                            ui.notify(f'Erreur: {e}', type='negative')
                    
                    def delete_all() -> None:
                        confirm = ConfirmDialog(
                            title=f'Supprimer tous les messages de "{title}" ?',
                            message='Cette action est irréversible.',
                            on_confirm=on_confirm,
                            confirm_text='Supprimer tout',
                            is_danger=True
                        )
                        confirm.show()
                    return delete_all
                
                with ui.button(
                    on_click=make_delete_all(chat_id, chat_data['title'], account, chat_data['messages'])
                ).props('flat dense').style('color: var(--danger);'):
                    with ui.row().classes('items-center gap-1'):
                        ui.html(svg('close', 16, 'var(--danger)'))
                        ui.label('Tout supprimer')
            
            # Liste des messages
            with ui.column().classes('w-full gap-2'):
                for msg in sorted(chat_data['messages'], key=lambda x: x['date']):
                    self._render_message_card(msg, chat_id, account)
    
    def _render_message_card(self, msg: Dict, chat_id: int, account) -> None:
        """Rend une carte de message."""
        with ui.card().classes('w-full p-4').style(
            'background: var(--bg-secondary); border: 1px solid var(--border);'
        ):
            with ui.row().classes('w-full items-start gap-3'):
                # Checkbox de sélection
                key = (chat_id, msg['message_id'])
                
                def make_checkbox_handler(cid: int, mid: int):
                    def handler(e):
                        self._update_selection_state(cid, mid, e.value)
                    return handler
                
                checkbox = ui.checkbox(value=False).props('dense').on_value_change(
                    make_checkbox_handler(chat_id, msg['message_id'])
                )
                self.checkboxes[key] = checkbox
                
                with ui.column().classes('flex-1 gap-2'):
                    # Date et heure
                    ui.label(msg['date'].strftime('%d/%m/%Y %H:%M')).classes('font-bold').style(
                        'color: var(--primary);'
                    )
                    
                    # Texte du message
                    text = msg['text'][:100] + ('...' if len(msg['text']) > 100 else '')
                    ui.label(text).classes('text-sm').style('color: var(--text-primary);')
                    
                    # Média si présent
                    if msg['has_media']:
                        with ui.row().classes('items-center gap-1'):
                            ui.html(svg('attach_file', 14, 'var(--text-secondary)'))
                            ui.label(f'{msg["media_type"]}').classes('text-xs').style(
                            'color: var(--accent);'
                        )
                
                # Boutons d'action
                with ui.column().classes('gap-1'):
                    # Bouton éditer
                    def make_edit(cid: int, mid: int, txt: str, dt: datetime):
                        def edit():
                            self._show_single_edit_dialog(cid, mid, txt, dt)
                        return edit
                    
                    with ui.button(on_click=make_edit(chat_id, msg['message_id'], msg['text'], msg['date'])).props(
                        'flat dense round'
                    ).style('color: #10b981;'):
                        ui.html(svg('edit', 18, '#10b981'))
                    
                    # Bouton supprimer
                    def make_delete(cid: int, mid: int, acc):
                        async def delete() -> None:
                            try:
                                ui.notify('Suppression...', type='info')
                                success, error = await acc.delete_scheduled_messages(cid, [mid])
                                if success:
                                    ui.notify('Message supprimé', type='positive')
                                    self.current_messages = [
                                        m for m in self.current_messages
                                        if not (m['chat_id'] == cid and m['message_id'] == mid)
                                    ]
                                    self.display_messages()
                                else:
                                    ui.notify(f'Erreur: {error}', type='negative')
                            except Exception as e:
                                logger.error(f"Erreur suppression message: {e}")
                                ui.notify(f'Erreur: {e}', type='negative')
                        return delete
                    
                    with ui.button(on_click=make_delete(chat_id, msg['message_id'], account)).props(
                        'flat dense round'
                    ).style('color: var(--danger);'):
                        ui.html(svg('close', 18, '#ef4444'))
    
    def _delete_all_everywhere(self) -> None:
        """Supprime TOUS les messages de TOUS les groupes."""
        async def on_confirm() -> None:
            try:
                account = self.telegram_manager.get_account(self.selected_account)
                if not account:
                    return
                
                notify('Suppression de tous les messages...', type='warning')
                
                # Grouper par chat
                chats: Dict[int, List[int]] = {}
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
                
                notify(f'{deleted_count} message(s) supprimé(s) !', type='positive')
                
                # Vider le cache
                self.current_messages = []
                self.display_messages()
                
            except Exception as e:
                logger.error(f"Erreur suppression totale: {e}")
                notify(f'Erreur: {e}', type='negative')
        
        confirm = ConfirmDialog(
            title='ATTENTION',
            message=f'Supprimer TOUS les {len(self.current_messages)} messages programmés de TOUS les groupes ? Cette action est IRRÉVERSIBLE.',
            on_confirm=on_confirm,
            confirm_text='TOUT SUPPRIMER',
            is_danger=True
        )
        confirm.show()
    
    async def scan_all_accounts(self) -> None:
        """Scanne tous les comptes connectés et affiche tous les messages avec barre de progression."""
        accounts = self.telegram_manager.list_accounts()
        connected = [acc for acc in accounts if acc.get('is_connected', False)]
        
        if not connected:
            notify('Aucun compte connecté', type='negative')
            return
        
        # Réinitialiser le filtre de groupe lors d'un nouveau scan
        self.selected_chat_id = None
        
        total_accounts = len(connected)
        self.messages_container.clear()
        
        # Créer la carte de progression
        with self.messages_container:
            with ui.card().classes('w-full p-8 card-modern'):
                with ui.column().classes('w-full items-center gap-4'):
                    # Titre
                    with ui.row().classes('items-center gap-3 mb-2'):
                        ui.html(svg('search', 32, '#1e40af'))
                        ui.label('Scan global en cours...').classes('text-2xl font-bold').style(
                        'color: var(--primary);'
                        )
                    
                    # Label de progression
                    progress_label = ui.label('Préparation du scan...').classes('text-lg mb-4').style(
                        'color: var(--text-secondary);'
                    )
                    
                    # Barre de progression
                    progress_bar = ui.linear_progress(value=0, show_value=False).classes('w-full')
                    
                    # Pourcentage en grand
                    percentage_label = ui.label('0%').classes('text-4xl font-bold mt-4').style(
                        'color: var(--primary);'
                    )
                    
                    # Détails
                    details_label = ui.label('0 / 0 comptes scannés').classes('text-sm mt-2').style(
                        'color: var(--text-secondary);'
                    )
        
        try:
            all_messages = []
            scanned = 0
            
            for idx, account_info in enumerate(connected, 1):
                # Mettre à jour la progression
                account_name = account_info['account_name']
                progress_label.set_text(f'Scan de {account_name}...')
                percentage = (idx - 1) / total_accounts
                progress_bar.set_value(percentage)
                percentage_label.set_text(f'{int(percentage * 100)}%')
                details_label.set_text(f'{idx - 1} / {total_accounts} comptes scannés')
                
                account = self.telegram_manager.get_account(account_info['session_id'])
                if not account:
                    continue
                
                try:
                    messages = await account.get_all_scheduled_messages()
                    # Ajouter le nom du compte et session_id à chaque message
                    for msg in messages:
                        msg['account_name'] = account.account_name
                        msg['account_session_id'] = account_info['session_id']
                    all_messages.extend(messages)
                    scanned += 1
                except Exception as e:
                    logger.error(f"Erreur scan {account.account_name}: {e}")
                
                # Mise à jour finale pour ce compte
                progress_bar.set_value(idx / total_accounts)
                percentage_label.set_text(f'{int((idx / total_accounts) * 100)}%')
                details_label.set_text(f'{idx} / {total_accounts} comptes scannés')
            
            # Progression à 100%
            progress_label.set_text('Scan terminé !')
            progress_bar.set_value(1.0)
            percentage_label.set_text('100%')
            details_label.set_text(f'{scanned} / {total_accounts} comptes scannés avec succès')
            
            # Petit délai pour voir le 100%
            await asyncio.sleep(0.5)
            
            # Stocker les messages
            self.current_messages = all_messages
            self.selected_account = None  # Mode "tous les comptes"
            
            # Afficher les messages
            self.display_all_accounts_messages()
            
        except Exception as e:
            logger.error(f"Erreur scan global: {e}")
            self.messages_container.clear()
            with self.messages_container:
                with ui.card().classes('w-full p-4 bg-red-50'):
                    ui.html(svg('error', 32, '#b91c1c'))
                    ui.label('Erreur lors du scan global').classes('text-red-700 font-bold')
                    ui.label(str(e)).classes('text-sm text-red-600')
    
    def display_all_accounts_messages(self) -> None:
        """Affiche tous les messages de tous les comptes."""
        self.messages_container.clear()
        
        with self.messages_container:
            if self.current_messages:
                # Réinitialiser la sélection et les checkboxes
                self.selected_messages.clear()
                self.checkboxes.clear()
                
                # Boutons d'action
                with ui.row().classes('w-full gap-3 mb-4'):
                    async def refresh() -> None:
                        ui.notify('Rechargement de tous les comptes...', type='info')
                        await self.scan_all_accounts()
                    
                    with ui.button(on_click=refresh).props('outline').style('color: var(--accent);'):
                        with ui.row().classes('items-center gap-2'):
                            ui.html(svg('sync', 18, 'var(--accent)'))
                            ui.label('Rafraîchir tout')
                    
                    # Sélectionner tout
                    with ui.button(on_click=self._select_all_everywhere).props('outline').style('color: #10b981;'):
                        with ui.row().classes('items-center gap-2'):
                            ui.html(svg('check_circle', 18, '#10b981'))
                            ui.label('Tout sélectionner')
                    
                    with ui.button(on_click=self._delete_all_from_all_accounts).props('color=red'):
                        with ui.row().classes('items-center gap-2'):
                            ui.html(svg('delete_forever', 18, 'white'))
                            ui.label('Tout supprimer (TOUS LES COMPTES)')
                
                # Barre d'action pour l'édition (apparaît quand des messages sont sélectionnés)
                self.action_bar_container = ui.row().classes('w-full mb-4')
                
                # Menu de filtrage par groupe
                self._render_groups_filter_menu()
                
                # Filtrer les messages selon le groupe sélectionné
                filtered_messages = self.current_messages
                if self.selected_chat_id is not None:
                    filtered_messages = [
                        msg for msg in self.current_messages 
                        if msg['chat_id'] == self.selected_chat_id
                    ]
                
                # Grouper par compte
                accounts_dict: Dict[str, Dict] = {}
                for msg in filtered_messages:
                    account_id = msg['account_session_id']
                    account_name = msg['account_name']
                    
                    if account_id not in accounts_dict:
                        accounts_dict[account_id] = {
                            'name': account_name,
                            'messages': []
                        }
                    accounts_dict[account_id]['messages'].append(msg)
                
                # Résumé global
                with ui.card().classes('w-full p-5 mb-4').style(
                    'background: #ecfdf5; border-left: 3px solid var(--success);'
                ):
                    if self.selected_chat_id is None:
                        ui.label(
                            f'{len(self.current_messages)} message(s) programmé(s) sur {len(accounts_dict)} compte(s)'
                        ).classes('text-lg font-bold').style('color: #065f46;')
                    else:
                        # Afficher le nom du groupe filtré
                        filtered_chat_title = next(
                            (msg['chat_title'] for msg in filtered_messages if msg['chat_id'] == self.selected_chat_id),
                            "Groupe inconnu"
                        )
                        ui.label(
                            f'{len(filtered_messages)} message(s) dans "{filtered_chat_title}"'
                        ).classes('text-lg font-bold').style('color: #065f46;')
                
                # Afficher par compte
                for account_id, account_data in accounts_dict.items():
                    self._render_account_section(account_id, account_data)
            else:
                # Aucun message
                with ui.card().classes('w-full p-8 card-modern text-center'):
                    ui.html(svg('remove_circle', 60, 'var(--secondary)'))
                    ui.label('Aucun message programmé').classes('text-xl font-bold mb-2').style(
                        'color: var(--text-secondary);'
                    )
                    ui.label('Aucun message programmé trouvé sur tous les comptes.').classes('text-sm').style(
                        'color: var(--text-secondary); opacity: 0.7;'
                    )
    
    def _render_account_section(self, account_id: str, account_data: Dict) -> None:
        """Rend une section pour un compte avec tous ses messages."""
        with ui.card().classes('w-full p-5 mb-4 card-modern'):
            # En-tête du compte
            with ui.row().classes('w-full items-center gap-3 mb-4'):
                with ui.row().classes('items-center gap-2 flex-1'):
                    ui.html(svg('person', 22, 'var(--text-primary)'))
                    ui.label(f'{account_data["name"]}').classes('text-xl font-bold').style(
                    'color: var(--primary);'
                )
                ui.label(f'{len(account_data["messages"])} message(s)').classes(
                    'px-3 py-1 rounded text-sm font-semibold'
                ).style('background: rgba(30, 58, 138, 0.1); color: var(--primary);')
                
                def make_delete_account(acc_id: str, acc_name: str):
                    def delete_account() -> None:
                        async def on_confirm() -> None:
                            try:
                                notify(f'Suppression des messages de {acc_name}...', type='info')
                                account = self.telegram_manager.get_account(acc_id)
                                if not account:
                                    notify('Compte introuvable', type='negative')
                                    return
                                
                                # Grouper par chat
                                chats: Dict[int, List[int]] = {}
                                for msg in account_data["messages"]:
                                    if msg['chat_id'] not in chats:
                                        chats[msg['chat_id']] = []
                                    chats[msg['chat_id']].append(msg['message_id'])
                                
                                # Supprimer tous les messages de chaque chat
                                deleted_count = 0
                                for chat_id, msg_ids in chats.items():
                                    success, error = await account.delete_scheduled_messages(chat_id, msg_ids)
                                    if success:
                                        deleted_count += len(msg_ids)
                                
                                notify(f'{deleted_count} message(s) supprimé(s) de {acc_name} !', type='positive')
                                
                                # Recharger
                                await self.scan_all_accounts()
                                
                            except Exception as e:
                                logger.error(f"Erreur suppression compte: {e}")
                                notify(f'Erreur: {e}', type='negative')
                        
                        confirm = ConfirmDialog(
                            title=f'Supprimer tous les messages de "{acc_name}" ?',
                            message='Cette action est irréversible.',
                            on_confirm=on_confirm,
                            confirm_text='Supprimer tout',
                            is_danger=True
                        )
                        confirm.show()
                    return delete_account
                
                with ui.button(
                    on_click=make_delete_account(account_id, account_data['name'])
                ).props('flat dense').style('color: var(--danger);'):
                    with ui.row().classes('items-center gap-1'):
                        ui.html(svg('close', 16, 'var(--danger)'))
                        ui.label('Tout supprimer')
            
            # Grouper par chat
            chats_dict: Dict[int, Dict] = {}
            for msg in account_data["messages"]:
                chat_id = msg['chat_id']
                if chat_id not in chats_dict:
                    chats_dict[chat_id] = {
                        'title': msg['chat_title'],
                        'messages': []
                    }
                chats_dict[chat_id]['messages'].append(msg)
            
            # Afficher par groupe
            for chat_id, chat_data in chats_dict.items():
                with ui.column().classes('w-full gap-2 pl-4'):
                    # En-tête du groupe
                    with ui.row().classes('w-full items-center gap-2 mb-2'):
                        ui.label(f'• {chat_data["title"]}').classes('text-sm font-semibold').style(
                            'color: var(--text-primary);'
                        )
                        ui.label(f'{len(chat_data["messages"])} msg').classes('text-xs px-2 py-1 rounded').style(
                            'background: rgba(0, 0, 0, 0.05); color: var(--text-secondary);'
                        )
                    
                    # Messages
                    for msg in sorted(chat_data['messages'], key=lambda x: x['date']):
                        with ui.row().classes('w-full items-center gap-2 pl-4 py-1'):
                            ui.label(msg['date'].strftime('%d/%m/%Y %H:%M')).classes('text-xs font-mono').style(
                                'color: var(--accent); min-width: 100px;'
                            )
                            text = msg['text'][:60] + ('...' if len(msg['text']) > 60 else '')
                            ui.label(text).classes('text-xs flex-1').style('color: var(--text-secondary);')
                            
                            if msg['has_media']:
                                ui.html(svg('attach_file', 14, 'var(--text-secondary)'))
    
    def _delete_all_from_all_accounts(self) -> None:
        """Supprime TOUS les messages de TOUS les comptes."""
        async def on_confirm() -> None:
            try:
                notify('Suppression globale en cours...', type='warning')
                
                # Grouper par compte
                accounts_dict: Dict[str, List] = {}
                for msg in self.current_messages:
                    account_id = msg['account_session_id']
                    if account_id not in accounts_dict:
                        accounts_dict[account_id] = []
                    accounts_dict[account_id].append(msg)
                
                total_deleted = 0
                
                # Pour chaque compte
                for account_id, messages in accounts_dict.items():
                    account = self.telegram_manager.get_account(account_id)
                    if not account:
                        continue
                    
                    # Grouper par chat
                    chats: Dict[int, List[int]] = {}
                    for msg in messages:
                        if msg['chat_id'] not in chats:
                            chats[msg['chat_id']] = []
                        chats[msg['chat_id']].append(msg['message_id'])
                    
                    # Supprimer tous les messages de chaque chat
                    for chat_id, msg_ids in chats.items():
                        success, error = await account.delete_scheduled_messages(chat_id, msg_ids)
                        if success:
                            total_deleted += len(msg_ids)
                
                notify(f'{total_deleted} message(s) supprimé(s) de tous les comptes !', type='positive')
                
                # Recharger
                await self.scan_all_accounts()
                
            except Exception as e:
                logger.error(f"Erreur suppression globale: {e}")
                notify(f'Erreur: {e}', type='negative')
        
        confirm = ConfirmDialog(
            title='DANGER - SUPPRESSION GLOBALE',
            message=f'Supprimer TOUS les {len(self.current_messages)} messages de TOUS les comptes ? Cette action est IRRÉVERSIBLE et affectera TOUS vos comptes connectés.',
            on_confirm=on_confirm,
            confirm_text='SUPPRIMER ABSOLUMENT TOUT',
            is_danger=True
        )
        confirm.show()
    
    def _render_groups_filter_menu(self) -> None:
        """Rend le menu de filtrage par groupe."""
        # Extraire tous les groupes uniques avec leur nombre de messages
        groups_dict: Dict[int, Dict] = {}
        for msg in self.current_messages:
            chat_id = msg['chat_id']
            if chat_id not in groups_dict:
                groups_dict[chat_id] = {
                    'title': msg['chat_title'],
                    'count': 0
                }
            groups_dict[chat_id]['count'] += 1
        
        # Afficher seulement s'il y a au moins 1 groupe
        if len(groups_dict) == 0:
            return
        
        # Trier par nombre de messages (décroissant)
        sorted_groups = sorted(
            groups_dict.items(), 
            key=lambda x: x[1]['count'], 
            reverse=True
        )
        
        # Rendre le menu
        with ui.card().classes('w-full p-4 mb-4').style(
            'background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); '
            'border: 2px solid #0ea5e9; border-radius: 12px;'
        ):
            with ui.row().classes('items-center gap-2 mb-3'):
                ui.html(svg('search', 20, '#0369a1'))
                ui.label('Filtrer par groupe :').classes('text-lg font-bold').style(
                    'color: #0369a1;'
                )
                ui.label(f'{len(groups_dict)} groupe(s)').classes('text-xs px-2 py-1 rounded').style(
                    'background: rgba(14, 165, 233, 0.2); color: #0369a1;'
                )
            
            # Menu scrollable horizontal
            with ui.row().classes('gap-2 flex-wrap'):
                # Bouton "Tous"
                def select_all():
                    self.selected_chat_id = None
                    # Vérifier si on est en mode "compte unique" ou "scan global"
                    if self.selected_account:
                        self.display_messages()
                    else:
                        self.display_all_accounts_messages()
                
                is_all_selected = self.selected_chat_id is None
                button_style = (
                    'background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); '
                    'color: white; font-weight: bold; border: 2px solid #1d4ed8;'
                    if is_all_selected else
                    'background: #f3f4f6; color: #6b7280; border: 2px solid #e5e7eb;'
                )
                
                with ui.button(on_click=select_all).props('dense').style(button_style):
                    with ui.row().classes('items-center gap-2'):
                        ui.label('📋 Tous les groupes').classes('text-sm')
                        ui.label(f'({len(self.current_messages)})').classes('text-xs')
                
                # Bouton pour chaque groupe
                for chat_id, group_data in sorted_groups:
                    def make_select(cid: int):
                        def select():
                            self.selected_chat_id = cid
                            # Vérifier si on est en mode "compte unique" ou "scan global"
                            if self.selected_account:
                                self.display_messages()
                            else:
                                self.display_all_accounts_messages()
                        return select
                    
                    is_selected = self.selected_chat_id == chat_id
                    button_style = (
                        'background: linear-gradient(135deg, #10b981 0%, #059669 100%); '
                        'color: white; font-weight: bold; border: 2px solid #047857;'
                        if is_selected else
                        'background: white; color: #374151; border: 2px solid #d1d5db;'
                    )
                    
                    with ui.button(on_click=make_select(chat_id)).props('dense').style(button_style):
                        with ui.row().classes('items-center gap-2'):
                            # Tronquer le titre si trop long
                            title = group_data['title']
                            if len(title) > 25:
                                title = title[:22] + '...'
                            ui.label(title).classes('text-sm')
                            ui.label(f'({group_data["count"]})').classes('text-xs')
    
    def _update_selection_state(self, chat_id: int, message_id: int, is_checked: bool) -> None:
        """Met à jour l'état de sélection d'un message."""
        key = (chat_id, message_id)
        if is_checked:
            self.selected_messages.add(key)
        else:
            self.selected_messages.discard(key)
        
        # Mettre à jour la barre d'action
        self._update_action_bar()
    
    def _update_action_bar(self) -> None:
        """Met à jour la barre d'action selon le nombre de messages sélectionnés."""
        if not self.action_bar_container:
            return
        
        count = len(self.selected_messages)
        self.action_bar_container.clear()
        
        if count > 0:
            with self.action_bar_container:
                with ui.card().classes('w-full p-4').style(
                    'background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%); '
                    'border: 2px solid #3b82f6; border-radius: 12px;'
                ):
                    with ui.row().classes('w-full items-center gap-4'):
                        # Compteur
                        with ui.row().classes('items-center gap-2 flex-1'):
                            ui.html(svg('check_circle', 24, '#3b82f6'))
                            ui.label(f'{count} message(s) sélectionné(s)').classes('text-lg font-bold').style(
                                'color: #1e40af;'
                            )
                        
                        # Boutons d'action
                        with ui.row().classes('gap-2'):
                            # Tout désélectionner
                            with ui.button(on_click=self._deselect_all).props('outline').style(
                                'color: #6b7280; border-color: #9ca3af;'
                            ):
                                with ui.row().classes('items-center gap-2'):
                                    ui.html(svg('close', 18, '#6b7280'))
                                    ui.label('Tout désélectionner')
                            
                            # Éditer la sélection
                            with ui.button(on_click=self._show_bulk_edit_dialog).props('color=primary'):
                                with ui.row().classes('items-center gap-2'):
                                    ui.html(svg('edit', 18, 'white'))
                                    ui.label('Modifier la sélection')
    
    def _deselect_all(self) -> None:
        """Désélectionne tous les messages."""
        self.selected_messages.clear()
        # Décocher toutes les checkboxes
        for checkbox in self.checkboxes.values():
            checkbox.value = False
        self._update_action_bar()
    
    def _select_all_in_group(self, chat_id: int, messages: List[Dict]) -> None:
        """Sélectionne tous les messages d'un groupe."""
        for msg in messages:
            key = (chat_id, msg['message_id'])
            self.selected_messages.add(key)
            if key in self.checkboxes:
                self.checkboxes[key].value = True
        self._update_action_bar()
    
    def _select_all_everywhere(self) -> None:
        """Sélectionne tous les messages de tous les groupes."""
        for msg in self.current_messages:
            key = (msg['chat_id'], msg['message_id'])
            self.selected_messages.add(key)
            if key in self.checkboxes:
                self.checkboxes[key].value = True
        self._update_action_bar()
    
    def _show_bulk_edit_dialog(self) -> None:
        """Affiche le dialogue d'édition en lot."""
        if not self.selected_messages:
            notify('Aucun message sélectionné', type='warning')
            return
        
        dialog = ui.dialog()
        
        with dialog, ui.card().classes('w-full p-6').style('min-width: 600px;'):
            with ui.column().classes('w-full gap-4'):
                # En-tête
                with ui.row().classes('w-full items-center gap-3 mb-2'):
                    ui.html(svg('edit', 32, '#3b82f6'))
                    ui.label('Modifier les messages sélectionnés').classes('text-2xl font-bold').style(
                        'color: #1e40af;'
                    )
                
                ui.label(f'{len(self.selected_messages)} message(s) seront modifiés').classes('text-sm').style(
                    'color: #6b7280;'
                )
                
                ui.separator()
                
                # Champ texte
                ui.label('Nouveau texte du message').classes('text-lg font-semibold mt-2')
                ui.label('Ce texte remplacera le contenu de tous les messages sélectionnés').classes('text-sm mb-3').style(
                    'color: #6b7280;'
                )
                
                new_text_input_html = '''
                <textarea 
                    id="bulk_edit_text_input" 
                    rows="6"
                    placeholder="Entrez le nouveau texte..."
                    style="
                        width: 100%;
                        min-height: 150px;
                        min-width: 500px;
                        background: #ffffff;
                        border: 2px solid #d1d5db;
                        border-radius: 8px;
                        font-size: 14px;
                        padding: 12px;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        resize: both;
                    "
                ></textarea>
                '''
                ui.html(new_text_input_html)
                
                # Message d'erreur
                error_label = ui.label('').classes('text-red-500 text-sm mt-2')
                
                ui.separator().classes('mt-4')
                
                # Boutons
                with ui.row().classes('w-full gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat').classes('flex-1')
                    
                    async def apply_bulk_edit():
                        error_label.text = ''
                        
                        # Récupérer le nouveau texte avec timeout adaptatif
                        try:
                            # Timeout adaptatif selon le nombre de messages
                            timeout = max(2.0, len(self.selected_messages) * 0.1)
                            new_text = await ui.run_javascript('document.getElementById("bulk_edit_text_input").value', timeout=timeout) or ""
                            new_text = str(new_text).strip()
                            if not new_text:
                                error_label.text = 'Le nouveau texte ne peut pas être vide'
                                return
                        except asyncio.TimeoutError:
                            error_label.text = 'Timeout - Veuillez réessayer avec moins de messages'
                            return
                        except Exception as e:
                            logger.error(f"Erreur lecture texte: {e}")
                            error_label.text = 'Erreur de lecture du texte'
                            return
                        
                        # Fermer le dialogue et appliquer les modifications
                        dialog.close()
                        await self._apply_bulk_edit(new_text, None)
                    
                    ui.button('Appliquer', on_click=apply_bulk_edit).props('color=primary').classes('flex-1')
        
        dialog.open()
    
    async def _apply_bulk_edit(self, new_text: Optional[str], new_schedule: Optional[datetime]) -> None:
        """Applique les modifications en lot - VERSION SIMPLIFIÉE."""
        total = len(self.selected_messages)
        success_count = 0
        error_count = 0
        errors = []
        
        # Afficher un message de progression persistant
        ui.notify('Messages en cours de modification, veuillez patienter...', type='info')
        
        # Ne pas rafraîchir automatiquement - cela coupe les modifications
        # Le rafraîchissement se fera après les modifications
        
        # Grouper par compte ET par chat pour optimiser
        messages_by_account_and_chat = {}
        for chat_id, message_id in self.selected_messages:
            # Trouver le message dans current_messages
            msg = next((m for m in self.current_messages if m['chat_id'] == chat_id and m['message_id'] == message_id), None)
            if msg:
                account_id = msg.get('account_session_id', self.selected_account)
                key = (account_id, chat_id)
                if key not in messages_by_account_and_chat:
                    messages_by_account_and_chat[key] = []
                messages_by_account_and_chat[key].append((message_id, msg))
        
        # Appliquer les modifications par groupe (compte + chat) pour optimiser
        for (account_id, chat_id), messages in messages_by_account_and_chat.items():
            account = self.telegram_manager.get_account(account_id or self.selected_account)
            if not account:
                error_count += len(messages)
                continue
            
            try:
                # Récupérer TOUS les messages programmés du chat UNE SEULE FOIS
                peer = await account.client.get_input_entity(chat_id)
                result = await account.client(GetScheduledHistoryRequest(peer=peer, hash=0))
                
                # Créer un dictionnaire des messages actuels pour accès rapide
                current_messages_dict = {}
                if hasattr(result, 'messages') and result.messages:
                    for msg in result.messages:
                        if msg and msg.id:
                            current_messages_dict[msg.id] = msg
                
                # Modifier tous les messages de ce chat avec rate limiting
                for idx, (message_id, msg) in enumerate(messages):
                    try:
                        current_message = current_messages_dict.get(message_id)
                        if not current_message:
                            error_count += 1
                            errors.append(f"Message {message_id}: introuvable")
                            continue
                        
                        # Déterminer les nouvelles valeurs
                        text_to_use = new_text if new_text is not None else (getattr(current_message, 'message', None) or getattr(current_message, 'text', None) or "")
                        schedule_to_use = new_schedule if new_schedule is not None else current_message.date
                        
                        # Supprimer l'ancien message
                        await account.client(DeleteScheduledMessagesRequest(peer=peer, id=[message_id]))
                        
                        # Délai entre suppression et recréation (rate limit Telegram)
                        await asyncio.sleep(0.1)
                        
                        # Recréer le message
                        await account.client.send_message(
                            entity=peer,
                            message=text_to_use,
                            schedule=schedule_to_use
                        )
                        
                        success_count += 1
                        
                        # Rate limiting : Délai de 0.65s entre chaque message
                        # Total = 0.75s par message = 10 msg en 7.5s = 2.67 req/sec (safe)
                        if idx < len(messages) - 1:
                            await asyncio.sleep(0.65)
                        
                    except Exception as e:
                        logger.error(f"Erreur édition message {message_id}: {e}")
                        error_count += 1
                        errors.append(f"Message {message_id}: {str(e)}")
                
            except Exception as e:
                logger.error(f"Erreur récupération messages chat {chat_id}: {e}")
                error_count += len(messages)
                errors.append(f"Chat {chat_id}: {str(e)}")
        
        # Afficher le résultat
        if success_count > 0:
            notify(f'{success_count} message(s) modifié(s) avec succès !', type='positive')
        
        if error_count > 0:
            error_msg = f'{error_count} erreur(s) lors de la modification'
            if errors:
                error_msg += f'\n\nPremières erreurs:\n' + '\n'.join(errors[:3])
            notify(error_msg, type='negative')
        
        # Rafraîchir l'UI après modification (méthode simple et fiable)
        await self._update_ui_after_modification()
        
        # Désélectionner tout
        self._deselect_all()
    
    async def _update_ui_after_modification(self) -> None:
        """Met à jour l'UI après modification - OPTIMISÉE."""
        try:
            # Délai minimal pour s'assurer que les modifications sont prises en compte
            modified_count = len(self.selected_messages)
            delay = 0.3  # Délai fixe court
            await asyncio.sleep(delay)
            
            # Stratégie optimisée selon le volume
            if modified_count <= 10:
                # Mise à jour ciblée pour petits volumes
                await self._refresh_targeted_messages()
            else:
                # Rechargement complet pour gros volumes
                if self.selected_account:
                    await self.load_scheduled_messages()
                else:
                    await self.scan_all_accounts()
            
            # Forcer le rafraîchissement de l'UI
            self.display_messages()
            
            notify(f'Interface mise à jour ({modified_count} messages)', type='positive')
            
        except Exception as e:
            logger.error(f"Erreur mise à jour UI après modification: {e}")
            # Fallback : rechargement complet
            self.display_messages()
    
    async def _refresh_targeted_messages(self) -> None:
        """Rafraîchit seulement les messages modifiés - VERSION OPTIMISÉE."""
        if not self.selected_messages:
            return
        
        try:
            # Grouper par compte et chat pour minimiser les requêtes
            messages_by_account_and_chat = {}
            for chat_id, message_id in self.selected_messages:
                msg = next((m for m in self.current_messages if m['chat_id'] == chat_id and m['message_id'] == message_id), None)
                if msg:
                    account_id = msg.get('account_session_id', self.selected_account)
                    key = (account_id, chat_id)
                    if key not in messages_by_account_and_chat:
                        messages_by_account_and_chat[key] = []
                    messages_by_account_and_chat[key].append(message_id)
            
            # Rafraîchir chaque groupe de messages (une requête par chat)
            updated_count = 0
            for (account_id, chat_id), message_ids in messages_by_account_and_chat.items():
                account = self.telegram_manager.get_account(account_id or self.selected_account)
                if not account:
                    continue
                
                try:
                    # Récupérer seulement les messages de ce chat
                    peer = await account.client.get_input_entity(chat_id)
                    result = await account.client(GetScheduledHistoryRequest(peer=peer, hash=0))
                    
                    if hasattr(result, 'messages') and result.messages:
                        # Mettre à jour seulement les messages modifiés dans current_messages
                        for msg in result.messages:
                            if msg and msg.id in message_ids:
                                # Trouver et mettre à jour le message dans current_messages
                                for i, current_msg in enumerate(self.current_messages):
                                    if (current_msg['chat_id'] == chat_id and 
                                        current_msg['message_id'] == msg.id):
                                        self.current_messages[i] = {
                                            "message_id": msg.id,
                                            "chat_id": chat_id,
                                            "chat_title": current_msg['chat_title'],
                                            "text": getattr(msg, 'message', None) or getattr(msg, 'text', None) or "[Fichier]",
                                            "date": msg.date,
                                            "has_media": hasattr(msg, 'media') and msg.media is not None,
                                            "media_type": type(msg.media).__name__ if hasattr(msg, 'media') and msg.media else None,
                                            "account_session_id": account_id
                                        }
                                        updated_count += 1
                                        break
                
                except Exception as e:
                    logger.warning(f"Erreur rafraîchissement messages pour chat {chat_id}: {e}")
                    continue
            
            # Rafraîchir l'affichage seulement si des messages ont été mis à jour
            if updated_count > 0:
                self.display_messages()
                notify(f'{updated_count} message(s) mis à jour', type='positive')
            else:
                # Si aucun message n'a été mis à jour, forcer le rechargement complet
                logger.warning("Aucun message mis à jour - rechargement complet")
                if self.selected_account:
                    await self.load_scheduled_messages()
                else:
                    await self.scan_all_accounts()
            
        except Exception as e:
            logger.error(f"Erreur rafraîchissement messages ciblés: {e}")
            # Fallback : recharger tout
            if self.selected_account:
                await self.load_scheduled_messages()
            else:
                await self.scan_all_accounts()
    
    # Méthodes obsolètes supprimées pour simplifier le code
    
    def _show_single_edit_dialog(self, chat_id: int, message_id: int, current_text: str, current_date: datetime) -> None:
        """Affiche le dialogue d'édition pour un seul message."""
        dialog = ui.dialog()
        
        with dialog, ui.card().classes('w-full p-6').style('min-width: 600px;'):
            with ui.column().classes('w-full gap-4'):
                # En-tête
                with ui.row().classes('w-full items-center gap-3 mb-2'):
                    ui.html(svg('edit', 32, '#10b981'))
                    ui.label('Modifier le message').classes('text-2xl font-bold').style(
                        'color: #059669;'
                    )
                
                ui.separator()
                
                # Texte du message
                ui.label('Texte du message').classes('text-lg font-semibold mt-2')
                ui.label('Modifiez le contenu du message').classes('text-sm mb-3').style(
                    'color: #6b7280;'
                )
                
                single_text_html = f'''
                <textarea 
                    id="single_edit_text_input" 
                    rows="6"
                    style="
                        width: 100%;
                        min-height: 150px;
                        min-width: 500px;
                        background: #ffffff;
                        border: 2px solid #d1d5db;
                        border-radius: 8px;
                        font-size: 14px;
                        padding: 12px;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                        resize: both;
                    "
                >{current_text}</textarea>
                '''
                ui.html(single_text_html)
                
                # Message d'erreur
                error_label = ui.label('').classes('text-red-500 text-sm mt-2')
                
                ui.separator().classes('mt-4')
                
                # Boutons
                with ui.row().classes('w-full gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat').classes('flex-1')
                    
                    async def apply_single_edit():
                        error_label.text = ''
                        
                        # Récupérer le nouveau texte avec timeout adaptatif
                        try:
                            new_text = await ui.run_javascript('document.getElementById("single_edit_text_input").value', timeout=3.0) or ""
                            new_text = str(new_text).strip()
                            if not new_text:
                                error_label.text = 'Le texte ne peut pas être vide'
                                return
                        except asyncio.TimeoutError:
                            error_label.text = 'Timeout - Veuillez réessayer'
                            return
                        except Exception as e:
                            logger.error(f"Erreur lecture texte: {e}")
                            error_label.text = 'Erreur de lecture du texte'
                            return
                        
                        # Fermer le dialogue
                        dialog.close()
                        
                        # Appliquer la modification
                        account = self.telegram_manager.get_account(self.selected_account)
                        if not account:
                            notify('Compte introuvable', type='negative')
                            return
                        
                        # Afficher un message de progression
                        ui.notify('Message en cours de modification, veuillez patienter...', type='info')
                        
                        success, error = await account.edit_scheduled_message(
                            chat_id,
                            message_id,
                            new_text=new_text,
                            new_schedule_date=None
                        )
                        
                        if success:
                            notify('Message modifié avec succès !', type='positive')
                            # Rafraîchir l'UI complètement pour s'assurer que les changements sont visibles
                            await self._update_ui_after_modification()
                        else:
                            notify(f'Erreur: {error}', type='negative')
                    
                    ui.button('Enregistrer', on_click=apply_single_edit).props('color=primary').classes('flex-1')
        
        dialog.open()

