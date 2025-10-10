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
                ui.label(ICON_ACCOUNT).classes('text-4xl').style('color: var(--primary);')
                ui.label('Comptes Telegram').classes('text-3xl font-bold').style(
                    'color: var(--text-primary);'
                )
            
            # Bouton ajouter
            ui.button('＋ Ajouter un compte', on_click=self.app.add_account_dialog).classes(
                'btn-primary mb-2'
            )
            
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
                ui.label('●').classes('text-5xl mb-3').style('color: var(--secondary); opacity: 0.3;')
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
            f'width: 280px; height: 96px; flex-shrink: 0; display: flex; flex-direction: column; {card_style}'
        ):
            # Badge couronne pour le compte maître
            if is_master:
                ui.html('''
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
                    ">👑 MAÎTRE</div>
                ''', sanitize=False)
            
            with ui.column().classes('w-full h-full justify-between'):
                # Header avec status et infos
                with ui.column().classes('gap-2 flex-1'):
                    with ui.row().classes('w-full items-center gap-1'):
                        with ui.row().classes('items-center gap-2 flex-1 min-w-0'):
                            # Icône couronne pour le compte maître
                            if is_master:
                                ui.label('👑').classes('text-xl').style('filter: drop-shadow(0 2px 4px rgba(212, 175, 55, 0.5));')
                            
                            # Status badge
                            status_class = 'status-online' if is_connected else 'status-offline'
                            ui.html(f'<span class="status-badge {status_class}"></span>', sanitize=False)
                            
                            # Nom du compte avec couleur dorée pour le maître
                            text_color = '#B8860B' if is_master else 'var(--text-primary)'
                            ui.label(account.get('account_name', 'Sans nom')).classes(
                                'text-lg font-bold'
                            ).style(
                                f'color: {text_color}; white-space: nowrap; overflow: hidden; '
                                'text-overflow: ellipsis; max-width: 145px;'
                            )
                        
                        # Bouton Paramètres
                        ui.button(
                            '⚙ Paramètres',
                            on_click=lambda a=account: self.open_account_settings(a)
                        ).props('flat dense').style(
                            'color: var(--accent); flex-shrink: 0; white-space: nowrap; '
                            'font-size: 11px; margin-right: -15%;'
                        )
                    
                    with ui.row().classes('w-full items-center gap-1'):
                        # Numéro de téléphone
                        ui.label(account.get('phone', 'N/A')).classes('text-xs').style(
                            'color: var(--text-secondary); flex: 1; min-width: 0;'
                        )
                        
                        # Bouton Supprimer
                        ui.button(
                            '✕ Supprimer',
                            on_click=lambda a=account: self.app.delete_account(a)
                        ).props('flat dense').style(
                            'color: var(--danger); flex-shrink: 0; white-space: nowrap; '
                            'font-size: 11px; margin-right: -15%;'
                        )
                
                # Bouton Reconnecter si nécessaire
                if not is_connected:
                    with ui.row().classes('w-full justify-center'):
                        ui.button(
                            '↻ Reconnecter',
                            on_click=lambda a=account: self.app.reconnect_account(a)
                        ).props('flat dense').style('color: var(--warning); font-size: 11px;')
    
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
            ui.label('⚙ Paramètres du compte').classes('text-2xl font-bold mb-4').style(
                'color: var(--text-primary);'
            )
            ui.label(f"{account_name} ({phone})").classes('text-gray-600 mb-4')
            
            with ui.column().classes('w-full gap-4'):
                # Compte maître
                with ui.card().classes('p-4 bg-yellow-50 border-2 border-yellow-200'):
                    ui.label('👑 Compte Maître').classes('font-bold text-lg mb-2').style('color: #D97706;')
                    ui.label(
                        'Le compte maître est utilisé pour afficher les groupes en commun et y répondre. '
                        'Un seul compte peut être maître à la fois.'
                    ).classes('text-sm text-gray-600 mb-3')
                    
                    master_checkbox = ui.checkbox('Définir comme compte maître', value=is_master).classes('font-semibold')
                    
                    # Désactiver la case si c'est le seul compte et qu'il est maître
                    if is_master and not can_unset_master:
                        master_checkbox.disable()
                        ui.label('⚠ Impossible de décocher (compte unique)').classes('text-xs text-orange-600 mt-1')
                
                ui.separator()
                
                # Nom du compte
                ui.label('Nom du compte').classes('font-medium')
                name_input = ui.input(value=account_name).classes('w-full')
                
                # Message par défaut
                ui.label('Message par défaut').classes('font-medium')
                message_input = ui.textarea(value=settings.get('default_message', '')).classes(
                    'w-full'
                ).props('rows=4')
                
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
                                        ui.label(f'🕐 {schedule}').classes('flex-1')
                                        
                                        def make_delete_handler(s: str):
                                            def delete() -> None:
                                                schedules_list.remove(s)
                                                render_schedules()
                                            return delete
                                        
                                        ui.button(
                                            '🗑️',
                                            on_click=make_delete_handler(schedule)
                                        ).props('flat dense color=red size=sm')
                        else:
                            ui.label('Aucun horaire prédéfini').classes('text-gray-500 text-sm')
                
                # Ajouter un horaire
                with ui.row().classes('w-full gap-2 items-end'):
                    with ui.column().classes('flex-1'):
                        ui.label('Ajouter un horaire (HH:MM)').classes('text-sm text-gray-600')
                        time_input = ui.input(placeholder='09:00').classes('w-full')
                    
                    def add_time() -> None:
                        """Ajoute un horaire."""
                        time_str = time_input.value.strip()
                        
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
                        time_input.value = ''
                        render_schedules()
                        notify(f'{ICON_SUCCESS} {formatted} ajouté', type='positive')
                    
                    ui.button('➕ Ajouter', on_click=add_time).props('color=primary')
                
                render_schedules()
                
                with ui.card().classes('bg-blue-50 p-3 mt-2'):
                    ui.label(
                        '💡 Les horaires prédéfinis seront automatiquement proposés lors de la création de messages'
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
                                notify('👑 Compte maître défini !', type='positive')
                            elif can_unset_master:
                                # Si on retire le statut maître, définir un autre compte comme maître
                                # Prendre le premier compte disponible
                                all_accounts = self.telegram_manager.list_accounts()
                                for acc in all_accounts:
                                    if acc['session_id'] != session_id:
                                        self.session_manager.set_master_account(acc['session_id'])
                                        notify(f'👑 {acc["account_name"]} est maintenant le compte maître', type='info')
                                        break
                        
                        # Sauvegarder le nom
                        new_name = name_input.value.strip()
                        if new_name:
                            self.session_manager.update_account_name(session_id, new_name)
                        
                        # Sauvegarder les paramètres
                        new_message = message_input.value.strip()
                        self.session_manager.update_account_settings(
                            session_id,
                            default_message=new_message,
                            default_schedules=schedules_list
                        )
                        
                        dialog.close()
                        
                        # Rafraîchir la page pour afficher les changements
                        if needs_full_refresh:
                            notify('✅ Paramètres sauvegardés ! Actualisation...', type='positive')
                            # Double rafraîchissement pour être sûr que ça prend
                            self.app.show_page('comptes')
                            ui.timer(0.1, lambda: self.app.show_page('comptes'), once=True)
                        else:
                            notify('✅ Paramètres sauvegardés !', type='positive')
                            ui.timer(0.1, lambda: self.app.show_page('comptes'), once=True)
                        
                    except Exception as e:
                        logger.error(f"Erreur sauvegarde paramètres: {e}")
                        notify(f'Erreur: {e}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat').style(
                        'color: var(--secondary);'
                    )
                    ui.button('💾 Sauvegarder', on_click=save).classes('btn-primary')
        
        dialog.open()

