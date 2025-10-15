"""Classe principale de l'application AutoTele (refactorisée)."""
import asyncio
from typing import Optional

from nicegui import ui

from core.telegram.manager import TelegramManager
from .components.auth_dialog import show_auth_dialog
from .components.payment_dialog import show_payment_dialog
from .components.styles import get_global_styles
from .dialogs.account_dialogs import AccountDialogs
from .managers.auth_manager import AuthManager
from .managers.ui_manager import UIManager
from utils.logger import get_logger

logger = get_logger()


class AutoTeleApp:
    """Application principale AutoTele (refactorisée et modulaire)."""

    def __init__(self):
        """Initialise l'application."""
        self.telegram_manager = TelegramManager()
        self.auth_manager = AuthManager()
        self.ui_manager = UIManager(self.auth_manager)
        self.account_dialogs = AccountDialogs(self.telegram_manager)

        self.current_page = 'comptes'
        self.content_area: Optional[ui.column] = None
        self.is_loading_accounts = True
        self.main_container: Optional[ui.column] = None

        # Import des pages (lazy import pour éviter les imports circulaires)
        from .pages.accounts_page import AccountsPage
        from .pages.messaging_page import MessagingPage
        from .pages.new_message_page import NewMessagePage
        from .pages.scheduled_messages_page import ScheduledMessagesPage
        from .pages.sending_tasks_page import SendingTasksPage

        self.accounts_page = AccountsPage(self.telegram_manager, self)
        self.new_message_page = NewMessagePage(self.telegram_manager)
        self.scheduled_messages_page = ScheduledMessagesPage(
            self.telegram_manager
        )
        self.messaging_page = MessagingPage(self.telegram_manager)
        self.sending_tasks_page = SendingTasksPage()

    async def initialize(self) -> None:
        """Initialise l'application (charge les sessions existantes)."""
        try:
            self.ui_manager.update_loading_progress(
                10,
                "Chargement des sessions..."
            )

            await self.telegram_manager.load_existing_sessions_with_progress(
                lambda progress, message: self.ui_manager.update_loading_progress(  # noqa: E501
                    progress, message
                )
            )

            nb_accounts = len(self.telegram_manager.list_accounts())

            self.ui_manager.update_loading_progress(
                100,
                f"{nb_accounts} compte(s) chargé(s)"
            )

            await asyncio.sleep(0.5)

            self.is_loading_accounts = False

            await self.show_page(self.current_page)
            
            # Vérifier les mises à jour après 5 secondes (non bloquant)
            ui.timer(5.0, lambda: asyncio.create_task(self.check_for_updates()), once=True)
            
        except Exception as e:
            logger.error(f"Erreur initialisation: {e}")
            self.ui_manager.update_loading_progress(100, f"Erreur: {e}")
            await asyncio.sleep(1)
            self.is_loading_accounts = False

            await self.show_page(self.current_page)

    async def show_page(self, page_name: str) -> None:
        """
        Affiche une page spécifique.

        Args:
            page_name: Nom de la page.
        """
        if not self.auth_manager.has_active_subscription:
            if self.content_area:
                self.content_area.clear()
                with self.content_area:
                    self.ui_manager.render_subscription_required_screen(
                        self._start_subscription
                    )
            return

        self.current_page = page_name

        if self.content_area:
            self.content_area.clear()

            with self.content_area:
                if self.is_loading_accounts:
                    self.ui_manager.render_loading_screen()
                else:
                    self._render_page_content(page_name)

            self.content_area.update()

    def _render_page_content(self, page_name: str) -> None:
        """Rend le contenu d'une page spécifique."""
        page_map = {
            'comptes': self.accounts_page,
            'messagerie': self.messaging_page,
            'nouveau': self.new_message_page,
            'programme': self.scheduled_messages_page,
            'envois': self.sending_tasks_page
        }

        page = page_map.get(page_name)
        if page:
            page.render()

    async def add_account_dialog(self) -> None:
        """Affiche le dialogue d'ajout de compte."""
        await self.account_dialogs.show_add_account_dialog(
            lambda: self.show_page('comptes')
        )

    async def delete_account(self, account: dict) -> None:
        """Supprime un compte."""
        await self.account_dialogs.show_delete_account_dialog(
            account,
            lambda: self.show_page('comptes')
        )

    async def reconnect_account(self, account: dict) -> None:
        """Reconnecte un compte non autorisé."""
        await self.account_dialogs.show_reconnect_account_dialog(
            account,
            lambda: self.show_page('comptes')
        )

    async def _show_auth_or_app(self):
        """Affiche l'authentification ou l'application selon l'état."""
        is_ready = await self.auth_manager.check_auth_and_subscription()

        if not is_ready:
            if not self.auth_manager.is_authenticated:
                with self.main_container:
                    show_auth_dialog(on_success=self._on_auth_success)
            else:
                if self.main_container:
                    self.main_container.clear()
                    with self.main_container:
                        await self._setup_main_ui()

                await self._show_subscription_required()
        else:
            if self.main_container:
                self.main_container.clear()
                with self.main_container:
                    await self._setup_main_ui()

    async def _on_auth_success(self):
        """Appelé après une authentification réussie."""
        await self.auth_manager.on_auth_success(
            self.main_container,
            self._setup_main_ui,
            self._show_subscription_required
        )

    async def _on_payment_success(self):
        """Appelé après un paiement réussi."""
        await self.auth_manager.on_payment_success(
            self.auth_manager.update_subscription_status_display
        )

    async def _show_subscription_required(self):
        """Affiche un écran demandant de souscrire."""
        if not self.main_container:
            logger.error("main_container non disponible")
            return

        with self.main_container:
            with ui.dialog().props('persistent').classes('z-50') as dialog:
                with ui.card().classes('p-8 text-center max-w-md shadow-2xl'):
                    from .components.svg_icons import svg
                    ui.html(svg('lock', 80, '#3b82f6'))
                    ui.label('Abonnement requis').classes(
                        'text-2xl font-bold mb-2 mt-4'
                    )
                    ui.label(
                        'Pour utiliser AutoTele, vous devez souscrire à un '
                        'abonnement mensuel.'
                    ).classes('text-gray-600 mb-4')

                    price_display = (
                        self.auth_manager.subscription_service.get_price_display()  # noqa: E501
                    )
                    ui.label(price_display).classes(
                        'text-3xl font-bold text-blue-600 mb-6'
                    )

                    with ui.column().classes('gap-3'):
                        async def handle_subscribe():
                            await self._start_subscription()
                            dialog.close()

                        ui.button(
                            'Souscrire maintenant',
                            on_click=handle_subscribe
                        ).props('color=primary size=lg')

                        async def handle_logout():
                            dialog.close()
                            await self._handle_logout()

                        ui.button('Déconnexion', on_click=handle_logout) \
                            .props('flat')

            dialog.open()

    async def _start_subscription(self):
        """Démarre le processus de souscription."""
        with self.main_container:
            await show_payment_dialog(on_success=self._on_payment_success)

    async def _handle_logout(self):
        """Gère la déconnexion de l'utilisateur."""
        await self.auth_manager.handle_logout(
            self.main_container,
            self._show_auth_or_app
        )

    async def _setup_main_ui(self):
        """Configure l'interface principale de l'application."""
        with ui.row().classes('w-full h-screen').style(
            'margin: 0 !important; padding: 0 !important; '
            'background: var(--bg-secondary); '
            'overflow: hidden; width: 100vw !important; '
            'height: 100vh !important;'
        ):
            # Menu latéral
            self.ui_manager.create_sidebar(
                self.show_page,
                self._handle_logout
            )

            # Zone de contenu
            self.content_area = ui.column().classes(
                'flex-1 content-scrollable main-content'
            )

            # Charger la page par défaut
            await self.show_page('comptes')

            # Charger les sessions après que l'UI soit prête
            ui.timer(
                0.1,
                lambda: asyncio.create_task(self.initialize()),
                once=True
            )

    def setup_ui(self) -> None:
        """Configure l'interface utilisateur principale."""
        ui.add_head_html(get_global_styles())

        self.main_container = ui.column().classes('w-full h-screen').style(
            'margin: 0 !important; padding: 0 !important;'
        )

        with self.main_container:
            ui.timer(
                0.1,
                lambda: asyncio.create_task(self._show_auth_or_app()),
                once=True
            )
    
    async def check_for_updates(self):
        """
        Vérifie les mises à jour au démarrage.
        
        Affiche une notification si une mise à jour est disponible.
        """
        try:
            from utils.updater import get_updater
            import webbrowser
            
            updater = get_updater()
            
            # Vérifier (non bloquant)
            update_available, message = await updater.check_for_updates(use_github=True)
            
            if update_available:
                logger.info("Mise à jour disponible")
                
                # Afficher dialogue de mise à jour
                with ui.dialog().props('persistent') as update_dialog:
                    with ui.card().classes('p-6 max-w-md'):
                        from ui.components.svg_icons import svg
                        ui.html(svg('system_update', 64, '#3b82f6'))
                        
                        ui.label('🚀 Mise à jour disponible').classes(
                            'text-2xl font-bold mb-3 mt-2'
                        )
                        
                        ui.label(message).classes(
                            'text-gray-700 mb-4 whitespace-pre-line text-sm'
                        )
                        
                        if updater.is_update_required():
                            ui.label('⚠️ Cette mise à jour est OBLIGATOIRE').classes(
                                'text-red-600 font-bold mb-4'
                            )
                        
                        with ui.row().classes('gap-3 w-full'):
                            def open_download():
                                download_url = updater.get_download_url()
                                if download_url:
                                    webbrowser.open(download_url)
                                    ui.notify('Page de téléchargement ouverte', type='positive')
                                update_dialog.close()
                            
                            ui.button(
                                'Télécharger maintenant',
                                on_click=open_download
                            ).props('color=primary size=md').classes('flex-1')
                            
                            if not updater.is_update_required():
                                ui.button(
                                    'Plus tard',
                                    on_click=update_dialog.close
                                ).props('flat size=md')
                
                update_dialog.open()
        except Exception as e:
            # Erreur silencieuse (pas critique)
            logger.debug(f"Vérification mise à jour échouée: {e}")

