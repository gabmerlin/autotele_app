"""Gestionnaire des éléments d'interface utilisateur."""
import asyncio
from typing import Optional

from nicegui import ui

from ui.components.svg_icons import svg
from utils.constants import APP_NAME, ICON_ACCOUNT, ICON_MESSAGE, ICON_SCHEDULED


class UIManager:
    """Gère les éléments d'interface utilisateur."""

    def __init__(self, auth_manager):
        """
        Initialise le gestionnaire UI.

        Args:
            auth_manager: Instance du gestionnaire d'authentification.
        """
        self.auth_manager = auth_manager
        self.progress_bar: Optional[ui.linear_progress] = None
        self.progress_label: Optional[ui.label] = None
        self.progress_message: Optional[ui.label] = None
        self.loading_progress = 0
        self.loading_message = "Initialisation..."

    def update_loading_progress(self, progress: int, message: str) -> None:
        """
        Met à jour la progression du chargement.

        Args:
            progress: Pourcentage de progression (0-100).
            message: Message à afficher.
        """
        self.loading_progress = progress
        self.loading_message = message

        if self.progress_bar:
            self.progress_bar.set_value(progress / 100)
        if self.progress_label:
            self.progress_label.set_text(f"{progress}%")
        if self.progress_message:
            self.progress_message.set_text(message)

    def render_loading_screen(self) -> None:
        """Rend l'écran de chargement."""
        with ui.column().classes(
            'w-full h-full items-center justify-center gap-6'
        ).style('min-height: 60vh;'):
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
                ''')

                ui.label('Chargement des comptes Telegram...').classes(
                    'text-xl font-semibold'
                ).style('color: var(--text-primary);')

                self.progress_message = ui.label(
                    self.loading_message
                ).classes('text-sm').style('color: var(--text-secondary);')

                with ui.column().classes('w-80 items-center').style(
                    'position: relative; height: 32px;'
                ):
                    self.progress_bar = ui.linear_progress(
                        value=self.loading_progress / 100
                    ).classes('w-full').style(
                        'height: 32px; border-radius: 8px;'
                    )

                    self.progress_label = ui.label(
                        f"{self.loading_progress}%"
                    ).classes('text-base font-bold').style(
                        'position: absolute; top: 50%; left: 50%; '
                        'transform: translate(-50%, -50%); '
                        'color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.8); '
                        'z-index: 10; pointer-events: none;'
                    )

    def create_sidebar(
        self,
        show_page_callback,
        handle_logout_callback
    ) -> None:
        """
        Crée le menu latéral gauche.

        Args:
            show_page_callback: Callback pour afficher une page.
            handle_logout_callback: Callback pour la déconnexion.
        """
        with ui.column().classes(
            'w-64 h-screen app-sidebar p-6 gap-3'
        ).style('margin: 0 !important; padding: 24px !important;'):
            # Logo/Titre
            with ui.row().classes('items-center gap-3 mb-6'):
                ui.html(svg('play_arrow', 28, '#60a5fa'))
                ui.label(APP_NAME).classes('text-2xl sidebar-title')

            ui.separator().style(
                'background: rgba(255, 255, 255, 0.1); '
                'height: 1px; border: none;'
            )

            # Info utilisateur
            if self.auth_manager.is_authenticated:
                self._render_user_info(handle_logout_callback)

            # Menu items
            self._render_menu_items(show_page_callback)

            ui.space()

            # Footer
            with ui.column().classes('gap-1'):
                ui.label('Version 2.0').classes('text-xs').style(
                    'color: rgba(255, 255, 255, 0.5);'
                )
                ui.label('Pro Edition').classes(
                    'text-xs font-semibold'
                ).style('color: #60a5fa;')

    def _render_user_info(self, handle_logout_callback) -> None:
        """Rend les informations utilisateur dans la sidebar."""
        with ui.card().classes('w-full bg-white/10 p-3 mt-2'):
            user_email = self.auth_manager.auth_service.get_user_email()
            if user_email:
                ui.label(user_email).classes('text-xs text-white truncate')

            # Statut d'abonnement
            self.auth_manager.subscription_status_label = ui.label('').classes(
                'text-xs mt-1'
            ).style('font-weight: bold;')
            self.auth_manager.update_subscription_status_display()

            # Timer pour mettre à jour le statut automatiquement
            ui.timer(
                2.0,
                self.auth_manager.sync_refresh_subscription_status
            )

            # Bouton de déconnexion
            ui.button('Déconnexion', on_click=handle_logout_callback) \
                .props('flat size=sm') \
                .classes('w-full text-white mt-2') \
                .style('font-size: 0.7rem;')

    def _render_menu_items(self, show_page_callback) -> None:
        """Rend les éléments du menu."""
        with ui.column().classes('gap-2 mt-4'):
            self._create_menu_button(
                'Comptes',
                ICON_ACCOUNT,
                'comptes',
                show_page_callback
            )
            self._create_menu_button(
                'Messagerie',
                'chat',
                'messagerie',
                show_page_callback,
                badge='BETA'
            )
            self._create_menu_button(
                'Nouveau Message',
                ICON_MESSAGE,
                'nouveau',
                show_page_callback
            )
            self._create_menu_button(
                'Messages Programmés',
                ICON_SCHEDULED,
                'programme',
                show_page_callback
            )
            self._create_menu_button(
                'Envois en cours',
                'send',
                'envois',
                show_page_callback
            )

    def _create_menu_button(
        self,
        label: str,
        icon: str,
        page: str,
        show_page_callback,
        badge: str = None
    ) -> None:
        """Crée un bouton de menu."""
        with ui.button(
            on_click=lambda: asyncio.create_task(show_page_callback(page))
        ).props('flat align=left').classes(
            'w-full sidebar-btn text-white'
        ):
            with ui.row().classes('items-center gap-2 justify-between w-full'):
                with ui.row().classes('items-center gap-2'):
                    ui.html(svg(icon, 20, 'white'))
                    ui.label(label)
                
                # Badge optionnel à droite
                if badge:
                    ui.label(badge).classes('text-xs px-2 py-1 rounded-full').style(
                        'background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); '
                        'color: white; font-weight: bold; font-size: 0.7rem;'
                    )

    def render_subscription_required_screen(
        self,
        start_subscription_callback
    ) -> None:
        """Affiche l'écran de souscription requise."""
        try:
            with ui.column().classes(
                'w-full h-full items-center justify-center gap-6 p-8'
            ):
                ui.html(svg('warning', 120, '#f59e0b'))
                ui.label('Abonnement requis').classes(
                    'text-3xl font-bold text-white'
                )
                ui.label(
                    'Vous devez souscrire un abonnement pour accéder à '
                    'AutoTele.'
                ).classes('text-lg text-center text-gray-300')

                async def handle_subscribe():
                    await start_subscription_callback()

                ui.button(
                    'Souscrire maintenant',
                    on_click=handle_subscribe
                ) \
                    .props('size=lg') \
                    .classes('bg-blue-600 text-white mt-4')

        except Exception as e:
            from utils.logger import get_logger
            logger = get_logger()
            logger.error(
                f"Erreur lors de l'affichage de l'écran de souscription: {e}"
            )

