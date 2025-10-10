"""
Classe principale de l'application AutoTele.
"""
import asyncio
from typing import Optional
from nicegui import ui

from core.telegram.manager import TelegramManager
from ui.components.styles import get_global_styles
from ui.components.dialogs import VerificationDialog, ConfirmDialog
from utils.logger import get_logger
from utils.constants import APP_NAME, ICON_ACCOUNT, ICON_MESSAGE, ICON_SCHEDULED
from utils.validators import validate_phone_number, validate_account_name

logger = get_logger()


class AutoTeleApp:
    """Application principale AutoTele."""
    
    def __init__(self):
        """Initialise l'application."""
        self.telegram_manager = TelegramManager()
        self.current_page = 'comptes'
        self.content_area: Optional[ui.column] = None
        
        # Import des pages (lazy import pour éviter les imports circulaires)
        from ui.pages.accounts_page import AccountsPage
        from ui.pages.new_message_page import NewMessagePage
        from ui.pages.scheduled_messages_page import ScheduledMessagesPage
        
        self.accounts_page = AccountsPage(self.telegram_manager, self)
        self.new_message_page = NewMessagePage(self.telegram_manager)
        self.scheduled_messages_page = ScheduledMessagesPage(self.telegram_manager)
    
    async def initialize(self) -> None:
        """Initialise l'application (charge les sessions existantes)."""
        try:
            await self.telegram_manager.load_existing_sessions()
            nb_accounts = len(self.telegram_manager.list_accounts())
            logger.info(f"{nb_accounts} compte(s) chargé(s)")
        except Exception as e:
            logger.error(f"Erreur initialisation: {e}")
    
    def create_sidebar(self) -> None:
        """Crée le menu latéral gauche."""
        with ui.column().classes('w-64 h-screen app-sidebar p-6 gap-3').style(
            'margin: 0 !important; padding: 24px !important;'
        ):
            # Logo/Titre
            with ui.row().classes('items-center gap-3 mb-6'):
                ui.label('▸').classes('text-3xl').style('color: #60a5fa;')
                ui.label(APP_NAME).classes('text-2xl sidebar-title')
            
            ui.separator().style('background: rgba(255, 255, 255, 0.1); height: 1px; border: none;')
            
            # Menu items
            with ui.column().classes('gap-2 mt-4'):
                ui.button(
                    f'{ICON_ACCOUNT}  Comptes',
                    on_click=lambda: self.show_page('comptes')
                ).props('flat align=left').classes('w-full sidebar-btn text-white')
                
                ui.button(
                    f'{ICON_MESSAGE}  Nouveau Message',
                    on_click=lambda: self.show_page('nouveau')
                ).props('flat align=left').classes('w-full sidebar-btn text-white')
                
                ui.button(
                    f'{ICON_SCHEDULED}  Messages Programmés',
                    on_click=lambda: self.show_page('programme')
                ).props('flat align=left').classes('w-full sidebar-btn text-white')
            
            ui.space()
            
            # Footer
            with ui.column().classes('gap-1'):
                ui.label('Version 2.0').classes('text-xs').style('color: rgba(255, 255, 255, 0.5);')
                ui.label('Pro Edition').classes('text-xs font-semibold').style('color: #60a5fa;')
    
    def show_page(self, page_name: str) -> None:
        """
        Affiche une page spécifique.
        
        Args:
            page_name: Nom de la page ('comptes', 'nouveau', 'programme')
        """
        self.current_page = page_name
        
        if self.content_area:
            self.content_area.clear()
            
            with self.content_area:
                if page_name == 'comptes':
                    self.accounts_page.render()
                elif page_name == 'nouveau':
                    self.new_message_page.render()
                elif page_name == 'programme':
                    self.scheduled_messages_page.render()
            
            self.content_area.update()
    
    async def add_account_dialog(self) -> None:
        """Affiche le dialogue d'ajout de compte."""
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6 card-modern'):
            ui.label('＋ Ajouter un compte').classes('text-2xl font-bold mb-4').style(
                'color: var(--text-primary);'
            )
            
            with ui.column().classes('w-full gap-4'):
                ui.label('Nom du compte').classes('font-medium')
                name_input = ui.input(placeholder='Ex: Mon Compte Pro').classes('w-full')
                
                ui.label('Numéro de téléphone').classes('font-medium')
                phone_input = ui.input(placeholder='+33612345678').classes('w-full')
                
                with ui.card().classes('bg-blue-50 p-3'):
                    ui.label(
                        '✅ Simple : Nom du compte, numéro, code, connectez-vous !'
                    ).classes('text-sm text-blue-800')
                
                async def submit() -> None:
                    """Soumet le formulaire d'ajout de compte."""
                    name = name_input.value.strip()
                    phone = phone_input.value.strip()
                    
                    # Validations
                    is_valid, error_msg = validate_account_name(name)
                    if not is_valid:
                        ui.notify(error_msg, type='warning')
                        return
                    
                    is_valid, error_msg = validate_phone_number(phone)
                    if not is_valid:
                        ui.notify(error_msg, type='warning')
                        return
                    
                    try:
                        ui.notify('Envoi du code de vérification...', type='info')
                        
                        success, message, session_id = await self.telegram_manager.add_account(phone, name)
                        
                        if success:
                            ui.notify('Code envoyé ! Vérifiez votre Telegram', type='positive')
                            dialog.close()
                            
                            # Afficher le dialogue de vérification
                            async def on_verify(sid: str, code: str, password: Optional[str]) -> None:
                                """Callback de vérification."""
                                success, error = await self.telegram_manager.verify_account(sid, code, password)
                                if success:
                                    ui.notify('🎉 Compte ajouté avec succès !', type='positive')
                                    ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
                                else:
                                    raise Exception(error)
                            
                            verification_dialog = VerificationDialog(
                                name, phone, session_id, on_verify
                            )
                            verification_dialog.show()
                        else:
                            ui.notify(f'Erreur: {message}', type='negative')
                    
                    except Exception as e:
                        logger.error(f"Erreur ajout compte: {e}")
                        ui.notify(f'Erreur: {e}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat').style(
                        'color: var(--secondary);'
                    )
                    ui.button('→ Continuer', on_click=submit).classes('btn-primary')
        
        dialog.open()
    
    async def delete_account(self, account: dict) -> None:
        """
        Supprime un compte.
        
        Args:
            account: Dictionnaire avec les infos du compte
        """
        session_id = account.get('session_id')
        phone = account.get('phone')
        account_name = account.get('account_name')
        
        async def on_confirm() -> None:
            """Confirme la suppression."""
            await self.telegram_manager.remove_account(session_id)
            ui.notify('✅ Compte supprimé', type='positive')
            ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
        
        confirm_dialog = ConfirmDialog(
            title=f"⚠ Supprimer le compte ?",
            message=f"Compte: {account_name} ({phone})",
            on_confirm=on_confirm,
            confirm_text="✕ Supprimer",
            is_danger=True
        )
        confirm_dialog.show()
    
    async def reconnect_account(self, account: dict) -> None:
        """
        Reconnecte un compte non autorisé.
        
        Args:
            account: Dictionnaire avec les infos du compte
        """
        session_id = account.get('session_id')
        phone = account.get('phone')
        account_name = account.get('account_name')
        
        try:
            ui.notify('Envoi du nouveau code de vérification...', type='info')
            success, message = await self.telegram_manager.resend_code(session_id)
            
            if success:
                ui.notify('Code envoyé ! Vérifiez votre Telegram', type='positive')
                
                # Afficher le dialogue de vérification
                async def on_verify(sid: str, code: str, password: Optional[str]) -> None:
                    """Callback de vérification."""
                    success, error = await self.telegram_manager.verify_account(sid, code, password)
                    if success:
                        ui.notify('✅ Compte reconnecté avec succès !', type='positive')
                        ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
                    else:
                        raise Exception(error)
                
                verification_dialog = VerificationDialog(
                    account_name, phone, session_id, on_verify
                )
                verification_dialog.show()
            else:
                ui.notify(f'Erreur: {message}', type='negative')
        
        except Exception as e:
            logger.error(f"Erreur reconnexion: {e}")
            ui.notify(f'Erreur: {e}', type='negative')
    
    def setup_ui(self) -> None:
        """Configure l'interface utilisateur principale."""
        # Ajouter les styles globaux
        ui.add_head_html(get_global_styles())
        
        with ui.row().classes('w-full h-screen').style(
            'margin: 0 !important; padding: 0 !important; background: var(--bg-secondary); '
            'overflow: hidden; width: 100vw !important; height: 100vh !important;'
        ):
            # Menu latéral
            self.create_sidebar()
            
            # Zone de contenu
            self.content_area = ui.column().classes('flex-1 content-scrollable')
            
            # Charger la page par défaut
            self.show_page('comptes')
            
            # Charger les sessions existantes après que l'UI soit prête
            ui.timer(0.1, lambda: asyncio.create_task(self.initialize()), once=True)

