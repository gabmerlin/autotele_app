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
from utils.constants import APP_NAME, ICON_ACCOUNT, ICON_MESSAGE, ICON_SCHEDULED, ICON_WARNING, ICON_ERROR
from utils.validators import validate_phone_number, validate_account_name, validate_verification_code
from utils.notification_manager import notify

logger = get_logger()


class AutoTeleApp:
    """Application principale AutoTele."""
    
    def __init__(self):
        """Initialise l'application."""
        self.telegram_manager = TelegramManager()
        self.current_page = 'comptes'
        self.content_area: Optional[ui.column] = None
        self.is_loading_accounts = True
        self.loading_progress = 0
        self.loading_message = "Initialisation..."
        self.progress_bar: Optional[ui.linear_progress] = None
        self.progress_label: Optional[ui.label] = None
        self.progress_message: Optional[ui.label] = None
        
        # Import des pages (lazy import pour éviter les imports circulaires)
        from ui.pages.accounts_page import AccountsPage
        from ui.pages.new_message_page import NewMessagePage
        from ui.pages.scheduled_messages_page import ScheduledMessagesPage
        from ui.pages.messaging_page import MessagingPage
        from ui.pages.sending_tasks_page import SendingTasksPage
        from utils.notification_manager import notify
        
        self.accounts_page = AccountsPage(self.telegram_manager, self)
        self.new_message_page = NewMessagePage(self.telegram_manager)
        self.scheduled_messages_page = ScheduledMessagesPage(self.telegram_manager)
        self.messaging_page = MessagingPage(self.telegram_manager)
        self.sending_tasks_page = SendingTasksPage()
    
    def _create_verification_callback(self, success_message: str):
        """
        Crée un callback de vérification réutilisable.
        
        Args:
            success_message: Message à afficher en cas de succès
            
        Returns:
            Fonction callback async
        """
        async def on_verify(sid: str, code: str, password: Optional[str]) -> None:
            """Callback de vérification."""
            success, error = await self.telegram_manager.verify_account(sid, code, password)
            if success:
                notify(success_message, type='positive')
                ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
            else:
                raise Exception(error)
        
        return on_verify
    
    async def initialize(self) -> None:
        """Initialise l'application (charge les sessions existantes)."""
        try:
            # Mise à jour de la progression
            self._update_loading_progress(10, "Chargement des sessions...")
            
            # Charger les sessions avec callback de progression
            await self.telegram_manager.load_existing_sessions_with_progress(
                lambda progress, message: self._update_loading_progress(progress, message)
            )
            
            nb_accounts = len(self.telegram_manager.list_accounts())
            
            # Finalisation
            self._update_loading_progress(100, f"✓ {nb_accounts} compte(s) chargé(s)")
            
            # Attendre un peu pour voir le 100%
            await asyncio.sleep(0.5)
            
            self.is_loading_accounts = False
            
            # Rafraîchir l'affichage maintenant que le chargement est terminé
            self.show_page(self.current_page)
        except Exception as e:
            logger.error(f"Erreur initialisation: {e}")
            self._update_loading_progress(100, f"Erreur: {e}")
            await asyncio.sleep(1)
            self.is_loading_accounts = False
            
            # Rafraîchir l'affichage même en cas d'erreur
            self.show_page(self.current_page)
    
    def _update_loading_progress(self, progress: int, message: str) -> None:
        """
        Met à jour la progression du chargement.
        
        Args:
            progress: Pourcentage de progression (0-100)
            message: Message à afficher
        """
        self.loading_progress = progress
        self.loading_message = message
        
        # Mettre à jour les éléments UI si ils existent
        if self.progress_bar:
            self.progress_bar.set_value(progress / 100)
        if self.progress_label:
            self.progress_label.set_text(f"{progress}%")
        if self.progress_message:
            self.progress_message.set_text(message)
    
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
                    '💬  Messagerie',
                    on_click=lambda: self.show_page('messagerie')
                ).props('flat align=left').classes('w-full sidebar-btn text-white')
                
                ui.button(
                    f'{ICON_MESSAGE}  Nouveau Message',
                    on_click=lambda: self.show_page('nouveau')
                ).props('flat align=left').classes('w-full sidebar-btn text-white')
                
                ui.button(
                    f'{ICON_SCHEDULED}  Messages Programmés',
                    on_click=lambda: self.show_page('programme')
                ).props('flat align=left').classes('w-full sidebar-btn text-white')
                
                ui.button(
                    '📤  Envois en cours',
                    on_click=lambda: self.show_page('envois')
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
            page_name: Nom de la page ('comptes', 'messagerie', 'nouveau', 'programme', 'envois')
        """
        self.current_page = page_name
        
        if self.content_area:
            self.content_area.clear()
            
            with self.content_area:
                # Afficher l'écran de chargement si les comptes sont en cours de chargement
                if self.is_loading_accounts:
                    self._render_loading_screen()
                else:
                    if page_name == 'comptes':
                        self.accounts_page.render()
                    elif page_name == 'messagerie':
                        self.messaging_page.render()
                    elif page_name == 'nouveau':
                        self.new_message_page.render()
                    elif page_name == 'programme':
                        self.scheduled_messages_page.render()
                    elif page_name == 'envois':
                        self.sending_tasks_page.render()
            
            self.content_area.update()
    
    def _render_loading_screen(self) -> None:
        """Rend l'écran de chargement pendant l'initialisation des comptes."""
        with ui.column().classes('w-full h-full items-center justify-center gap-6').style(
            'min-height: 60vh;'
        ):
            # Logo de chargement animé
            with ui.column().classes('items-center gap-6'):
                # Spinner animé
                ui.html('''
                    <div style="
                        width: 60px;
                        height: 60px;
                        border: 4px solid #e2e8f0;
                        border-top: 4px solid #3b82f6;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                    "></div>
                    <style>
                        @keyframes spin {
                            0% { transform: rotate(0deg); }
                            100% { transform: rotate(360deg); }
                        }
                    </style>
                ''', sanitize=False)
                
                # Texte de chargement
                ui.label('Chargement des comptes Telegram...').classes('text-xl font-semibold').style(
                    'color: var(--text-primary);'
                )
                
                # Message de progression
                self.progress_message = ui.label(self.loading_message).classes('text-sm').style(
                    'color: var(--text-secondary);'
                )
                
                # Barre de progression avec pourcentage intégré
                with ui.column().classes('w-80 items-center').style('position: relative; height: 32px;'):
                    self.progress_bar = ui.linear_progress(value=self.loading_progress / 100).classes('w-full').style(
                        'height: 32px; border-radius: 8px;'
                    )
                    # Label du pourcentage superposé à la barre
                    self.progress_label = ui.label(f"{self.loading_progress}%").classes('text-base font-bold').style(
                        'position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); '
                        'color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.8); z-index: 10; pointer-events: none;'
                    )
    
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
                        notify(error_msg, type='warning')
                        return
                    
                    is_valid, error_msg = validate_phone_number(phone)
                    if not is_valid:
                        notify(error_msg, type='warning')
                        return
                    
                    try:
                        notify('Envoi du code de vérification...', type='info')
                        
                        success, message, session_id = await self.telegram_manager.add_account(phone, name)
                        
                        if success:
                            notify('Code envoyé ! Vérifiez votre Telegram', type='positive')
                            
                            # Vider le contenu du dialogue actuel et le remplacer par le formulaire de vérification
                            dialog.clear()
                            
                            with dialog:
                                with ui.card().classes('w-96 p-6 card-modern'):
                                    ui.label('✓ Vérification').classes('text-2xl font-bold mb-4').style(
                                        'color: var(--text-primary);'
                                    )
                                    
                                    with ui.column().classes('w-full gap-4'):
                                        ui.label(f'Compte: {name} ({phone})').classes('text-gray-600')
                                        
                                        ui.label('Code de vérification').classes('font-medium')
                                        code_input = ui.input(placeholder='12345').classes('w-full')
                                        
                                        ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                                        password_input = ui.input(
                                            placeholder='Laissez vide si pas de 2FA',
                                            password=True
                                        ).classes('w-full')
                                        
                                        with ui.card().classes('p-3').style(
                                            'background: #fef3c7; border-left: 3px solid var(--warning);'
                                        ):
                                            ui.label(
                                                f'{ICON_WARNING} Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram'
                                            ).classes('text-sm').style('color: #92400e;')
                                        
                                        async def verify() -> None:
                                            """Vérifie le code de vérification."""
                                            code = code_input.value.strip()
                                            password = password_input.value.strip() if password_input.value else None
                                            
                                            # Validation
                                            is_valid, error_msg = validate_verification_code(code)
                                            if not is_valid:
                                                notify(error_msg, type='warning')
                                                return
                                            
                                            try:
                                                notify('Vérification en cours...', type='info')
                                                success_msg, error = await self.telegram_manager.verify_account(session_id, code, password)
                                                if success_msg:
                                                    notify('🎉 Compte ajouté avec succès !', type='positive')
                                                    dialog.close()
                                                    ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
                                                else:
                                                    notify(f'{ICON_ERROR} {error}', type='negative')
                                            except Exception as e:
                                                logger.error(f"Erreur vérification: {e}")
                                                notify(f'{ICON_ERROR} {e}', type='negative')
                                        
                                        def cancel() -> None:
                                            """Annule la vérification."""
                                            dialog.close()
                                        
                                        with ui.row().classes('w-full justify-end gap-2 mt-4'):
                                            ui.button('Annuler', on_click=cancel).props('flat').style(
                                                'color: var(--secondary);'
                                            )
                                            ui.button('✓ Vérifier', on_click=verify).classes('btn-primary')
                        else:
                            notify(f'Erreur: {message}', type='negative')
                    
                    except Exception as e:
                        logger.error(f"Erreur ajout compte: {e}")
                        notify(f'Erreur: {e}', type='negative')
                
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
            notify('✅ Compte supprimé', type='positive')
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
            notify('Envoi du nouveau code de vérification...', type='info')
            success, message = await self.telegram_manager.resend_code(session_id)
            
            if success:
                notify('Code envoyé ! Vérifiez votre Telegram', type='positive')
                
                # Créer le dialogue sans contexte spécifique (au niveau global)
                verification_dialog = ui.dialog().props('persistent')
                
                with verification_dialog, ui.card().classes('w-96 p-6 card-modern'):
                    ui.label('✓ Vérification').classes('text-2xl font-bold mb-4').style(
                        'color: var(--text-primary);'
                    )
                    
                    with ui.column().classes('w-full gap-4'):
                        ui.label(f'Compte: {account_name} ({phone})').classes('text-gray-600')
                        
                        ui.label('Code de vérification').classes('font-medium')
                        code_input = ui.input(placeholder='12345').classes('w-full')
                        
                        ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                        password_input = ui.input(
                            placeholder='Laissez vide si pas de 2FA',
                            password=True
                        ).classes('w-full')
                        
                        with ui.card().classes('p-3').style(
                            'background: #fef3c7; border-left: 3px solid var(--warning);'
                        ):
                            ui.label(
                                f'{ICON_WARNING} Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram'
                            ).classes('text-sm').style('color: #92400e;')
                        
                        async def verify() -> None:
                            """Vérifie le code de vérification."""
                            code = code_input.value.strip()
                            password = password_input.value.strip() if password_input.value else None
                            
                            # Validation
                            is_valid, error_msg = validate_verification_code(code)
                            if not is_valid:
                                notify(error_msg, type='warning')
                                return
                            
                            try:
                                notify('Vérification en cours...', type='info')
                                success_msg, error = await self.telegram_manager.verify_account(session_id, code, password)
                                if success_msg:
                                    notify('✅ Compte reconnecté avec succès !', type='positive')
                                    verification_dialog.close()
                                    ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
                                else:
                                    notify(f'{ICON_ERROR} {error}', type='negative')
                            except Exception as e:
                                logger.error(f"Erreur vérification: {e}")
                                notify(f'{ICON_ERROR} {e}', type='negative')
                        
                        def cancel() -> None:
                            """Annule la vérification."""
                            verification_dialog.close()
                        
                        with ui.row().classes('w-full justify-end gap-2 mt-4'):
                            ui.button('Annuler', on_click=cancel).props('flat').style(
                                'color: var(--secondary);'
                            )
                            ui.button('✓ Vérifier', on_click=verify).classes('btn-primary')
                
                verification_dialog.open()
            else:
                notify(f'Erreur: {message}', type='negative')
        
        except Exception as e:
            logger.error(f"Erreur reconnexion: {e}")
            notify(f'Erreur: {e}', type='negative')
    
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

