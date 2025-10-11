"""
Page de gestion des messages programmés.
"""
import asyncio
from typing import Optional, List, Dict
from nicegui import ui

from core.telegram.manager import TelegramManager
from ui.components.dialogs import ConfirmDialog
from utils.logger import get_logger
from utils.notification_manager import notify
from utils.constants import ICON_SCHEDULED, ICON_REFRESH, MSG_NO_CONNECTED_ACCOUNT

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
    
    def render(self) -> None:
        """Rend la page."""
        with ui.column().classes('w-full gap-6 p-8'):
            # En-tête
            with ui.row().classes('items-center gap-3 mb-2'):
                ui.label(ICON_SCHEDULED).classes('text-4xl').style('color: var(--primary);')
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
                ui.button(
                    '🔍 Scanner tous les comptes',
                    on_click=self.scan_all_accounts
                ).props('outline').style('color: var(--accent);')
            
            accounts = self.telegram_manager.list_accounts()
            connected = [acc for acc in accounts if acc.get('is_connected', False)]
            
            if not connected:
                ui.label(f'✕ {MSG_NO_CONNECTED_ACCOUNT}').classes('font-semibold').style(
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
                                f"● {account['account_name']}",
                                on_click=make_select(account['session_id'], account['account_name'])
                            ).classes('btn-primary')
                        else:
                            ui.button(
                                f"○ {account['account_name']}",
                                on_click=make_select(account['session_id'], account['account_name'])
                            ).props('outline').style('color: var(--text-secondary);')
    
    async def load_scheduled_messages(self) -> None:
        """Charge les messages programmés."""
        if not self.selected_account:
            return
        
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
                    ui.label('❌ Compte introuvable').classes('text-red-700')
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
                    ui.label('❌ Erreur lors du chargement').classes('text-red-700 font-bold')
                    ui.label(str(e)).classes('text-sm text-red-600')
    
    def display_messages(self) -> None:
        """Affiche les messages depuis le cache."""
        self.messages_container.clear()
        
        account = self.telegram_manager.get_account(self.selected_account)
        if not account:
            return
        
        with self.messages_container:
            if self.current_messages:
                # Boutons d'action
                with ui.row().classes('w-full gap-3 mb-4'):
                    async def refresh() -> None:
                        notify(f'{ICON_REFRESH} Rechargement...', type='info')
                        await self.load_scheduled_messages()
                    
                    ui.button(f'{ICON_REFRESH} Rafraîchir', on_click=refresh).props('outline').style(
                        'color: var(--accent);'
                    )
                    
                    ui.button(
                        '✕ Tout supprimer (TOUS)',
                        on_click=self._delete_all_everywhere
                    ).props('color=red')
                
                # Grouper par chat
                chats_dict: Dict[int, Dict] = {}
                for msg in self.current_messages:
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
                    ui.label(
                        f'✓ {len(self.current_messages)} message(s) programmé(s) dans {len(chats_dict)} groupe(s)'
                    ).classes('text-lg font-bold').style('color: #065f46;')
                
                # Afficher par groupe
                for chat_id, chat_data in chats_dict.items():
                    self._render_chat_messages(chat_id, chat_data, account)
            else:
                # Aucun message
                with ui.card().classes('w-full p-8 card-modern text-center'):
                    ui.label('●').classes('text-5xl mb-3').style('color: var(--secondary); opacity: 0.3;')
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
                ui.label(f'● {chat_data["title"]}').classes('text-lg font-bold flex-1').style(
                    'color: var(--text-primary);'
                )
                ui.label(f'{len(chat_data["messages"])} message(s)').classes(
                    'px-3 py-1 rounded text-sm font-semibold'
                ).style('background: rgba(30, 58, 138, 0.1); color: var(--primary);')
                
                def make_delete_all(cid: int, title: str):
                    def delete_all() -> None:
                        async def on_confirm() -> None:
                            try:
                                notify('Suppression en cours...', type='info')
                                success, error = await account.delete_scheduled_messages(cid, None)
                                if success:
                                    notify('✅ Messages supprimés !', type='positive')
                                    self.current_messages = [
                                        msg for msg in self.current_messages
                                        if msg['chat_id'] != cid
                                    ]
                                    self.display_messages()
                                else:
                                    notify(f'❌ Erreur: {error}', type='negative')
                            except Exception as e:
                                logger.error(f"Erreur suppression: {e}")
                                notify(f'❌ Erreur: {e}', type='negative')
                        
                        confirm = ConfirmDialog(
                            title=f'⚠️ Supprimer tous les messages de "{title}" ?',
                            message='Cette action est irréversible.',
                            on_confirm=on_confirm,
                            confirm_text='Supprimer tout',
                            is_danger=True
                        )
                        confirm.show()
                    return delete_all
                
                ui.button(
                    '✕ Tout supprimer',
                    on_click=make_delete_all(chat_id, chat_data['title'])
                ).props('flat dense').style('color: var(--danger);')
            
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
                        ui.label(f'📎 {msg["media_type"]}').classes('text-xs').style(
                            'color: var(--accent);'
                        )
                
                # Bouton supprimer
                def make_delete(cid: int, mid: int):
                    async def delete() -> None:
                        try:
                            notify('Suppression...', type='info')
                            success, error = await account.delete_scheduled_messages(cid, [mid])
                            if success:
                                notify('✅ Message supprimé', type='positive')
                                self.current_messages = [
                                    m for m in self.current_messages
                                    if not (m['chat_id'] == cid and m['message_id'] == mid)
                                ]
                                self.display_messages()
                            else:
                                notify(f'❌ Erreur: {error}', type='negative')
                        except Exception as e:
                            logger.error(f"Erreur suppression message: {e}")
                            notify(f'❌ Erreur: {e}', type='negative')
                    return delete
                
                ui.button('✕', on_click=make_delete(chat_id, msg['message_id'])).props(
                    'flat dense'
                ).style('color: var(--danger);')
    
    def _delete_all_everywhere(self) -> None:
        """Supprime TOUS les messages de TOUS les groupes."""
        async def on_confirm() -> None:
            try:
                account = self.telegram_manager.get_account(self.selected_account)
                if not account:
                    return
                
                notify('🗑️ Suppression de tous les messages...', type='warning')
                
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
                
                notify(f'✅ {deleted_count} message(s) supprimé(s) !', type='positive')
                
                # Vider le cache
                self.current_messages = []
                self.display_messages()
                
            except Exception as e:
                logger.error(f"Erreur suppression totale: {e}")
                notify(f'❌ Erreur: {e}', type='negative')
        
        confirm = ConfirmDialog(
            title='⚠ ATTENTION',
            message=f'Supprimer TOUS les {len(self.current_messages)} messages programmés de TOUS les groupes ? Cette action est IRRÉVERSIBLE.',
            on_confirm=on_confirm,
            confirm_text='✕ TOUT SUPPRIMER',
            is_danger=True
        )
        confirm.show()
    
    async def scan_all_accounts(self) -> None:
        """Scanne tous les comptes connectés et affiche tous les messages avec barre de progression."""
        accounts = self.telegram_manager.list_accounts()
        connected = [acc for acc in accounts if acc.get('is_connected', False)]
        
        if not connected:
            notify('❌ Aucun compte connecté', type='negative')
            return
        
        total_accounts = len(connected)
        self.messages_container.clear()
        
        # Créer la carte de progression
        with self.messages_container:
            with ui.card().classes('w-full p-8 card-modern'):
                with ui.column().classes('w-full items-center gap-4'):
                    # Titre
                    ui.label('🔍 Scan global en cours...').classes('text-2xl font-bold mb-2').style(
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
            progress_label.set_text('✅ Scan terminé !')
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
                    ui.label('❌ Erreur lors du scan global').classes('text-red-700 font-bold')
                    ui.label(str(e)).classes('text-sm text-red-600')
    
    def display_all_accounts_messages(self) -> None:
        """Affiche tous les messages de tous les comptes."""
        self.messages_container.clear()
        
        with self.messages_container:
            if self.current_messages:
                # Boutons d'action
                with ui.row().classes('w-full gap-3 mb-4'):
                    async def refresh() -> None:
                        notify(f'{ICON_REFRESH} Rechargement de tous les comptes...', type='info')
                        await self.scan_all_accounts()
                    
                    ui.button(f'{ICON_REFRESH} Rafraîchir tout', on_click=refresh).props('outline').style(
                        'color: var(--accent);'
                    )
                    
                    ui.button(
                        '✕ Tout supprimer (TOUS LES COMPTES)',
                        on_click=self._delete_all_from_all_accounts
                    ).props('color=red')
                
                # Grouper par compte
                accounts_dict: Dict[str, Dict] = {}
                for msg in self.current_messages:
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
                    ui.label(
                        f'✓ {len(self.current_messages)} message(s) programmé(s) sur {len(accounts_dict)} compte(s)'
                    ).classes('text-lg font-bold').style('color: #065f46;')
                
                # Afficher par compte
                for account_id, account_data in accounts_dict.items():
                    self._render_account_section(account_id, account_data)
            else:
                # Aucun message
                with ui.card().classes('w-full p-8 card-modern text-center'):
                    ui.label('●').classes('text-5xl mb-3').style('color: var(--secondary); opacity: 0.3;')
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
                ui.label(f'👤 {account_data["name"]}').classes('text-xl font-bold flex-1').style(
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
                                    notify('❌ Compte introuvable', type='negative')
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
                                
                                notify(f'✅ {deleted_count} message(s) supprimé(s) de {acc_name} !', type='positive')
                                
                                # Recharger
                                await self.scan_all_accounts()
                                
                            except Exception as e:
                                logger.error(f"Erreur suppression compte: {e}")
                                notify(f'❌ Erreur: {e}', type='negative')
                        
                        confirm = ConfirmDialog(
                            title=f'⚠️ Supprimer tous les messages de "{acc_name}" ?',
                            message='Cette action est irréversible.',
                            on_confirm=on_confirm,
                            confirm_text='Supprimer tout',
                            is_danger=True
                        )
                        confirm.show()
                    return delete_account
                
                ui.button(
                    '✕ Tout supprimer',
                    on_click=make_delete_account(account_id, account_data['name'])
                ).props('flat dense').style('color: var(--danger);')
            
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
                                ui.label(f'📎').classes('text-xs')
    
    def _delete_all_from_all_accounts(self) -> None:
        """Supprime TOUS les messages de TOUS les comptes."""
        async def on_confirm() -> None:
            try:
                notify('🗑️ Suppression globale en cours...', type='warning')
                
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
                
                notify(f'✅ {total_deleted} message(s) supprimé(s) de tous les comptes !', type='positive')
                
                # Recharger
                await self.scan_all_accounts()
                
            except Exception as e:
                logger.error(f"Erreur suppression globale: {e}")
                notify(f'❌ Erreur: {e}', type='negative')
        
        confirm = ConfirmDialog(
            title='⚠ DANGER - SUPPRESSION GLOBALE',
            message=f'Supprimer TOUS les {len(self.current_messages)} messages de TOUS les comptes ? Cette action est IRRÉVERSIBLE et affectera TOUS vos comptes connectés.',
            on_confirm=on_confirm,
            confirm_text='✕ SUPPRIMER ABSOLUMENT TOUT',
            is_danger=True
        )
        confirm.show()

