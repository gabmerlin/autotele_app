"""Gestionnaire d'authentification et d'abonnement."""
import asyncio

from nicegui import ui

from services.auth_service import get_auth_service
from services.subscription_service import get_subscription_service
from utils.logger import get_logger

logger = get_logger()


class AuthManager:
    """Gère l'authentification et les abonnements."""

    def __init__(self):
        """Initialise le gestionnaire d'authentification."""
        self.auth_service = get_auth_service()
        self.subscription_service = get_subscription_service()
        self.is_authenticated = False
        self.has_active_subscription = False
        self.subscription_status_label = None

    async def check_auth_and_subscription(self) -> bool:
        """
        Vérifie l'authentification et l'abonnement depuis Supabase.

        Returns:
            bool: True si l'utilisateur est authentifié avec abonnement actif.
        """
        session_restored = await self.auth_service.restore_session()

        if session_restored:
            self.is_authenticated = True

            user_id = self.auth_service.get_user_id()

            if not user_id:
                logger.error("Impossible de récupérer l'ID utilisateur")
                return False

            subscription = (
                await self.subscription_service._load_subscription_with_retry(
                    user_id
                )
            )

            if subscription:
                self.subscription_service.current_subscription = subscription
                self.has_active_subscription = True
                return True
            else:
                self.has_active_subscription = False
                return False

        return False

    async def handle_logout(self, main_container, show_auth_or_app_callback):
        """Gère la déconnexion de l'utilisateur."""
        await self.auth_service.sign_out()
        self.subscription_service.clear_subscription()
        self.is_authenticated = False
        self.has_active_subscription = False

        if main_container:
            main_container.clear()
            with main_container:
                await show_auth_or_app_callback()

    async def on_auth_success(
        self,
        main_container,
        setup_main_ui_callback,
        show_subscription_required_callback
    ):
        """Appelé après une authentification réussie."""
        self.is_authenticated = True

        user_id = self.auth_service.get_user_id()

        if user_id:
            subscription = (
                await self.subscription_service._load_subscription_with_retry(
                    user_id
                )
            )

            if subscription:
                self.subscription_service.current_subscription = subscription
                self.has_active_subscription = True
            else:
                self.has_active_subscription = False
        else:
            self.has_active_subscription = False
            logger.error("Impossible de récupérer l'ID utilisateur")

        if not self.has_active_subscription:
            if main_container:
                main_container.clear()
                with main_container:
                    await show_subscription_required_callback()
        else:
            if main_container:
                main_container.clear()
                with main_container:
                    await setup_main_ui_callback()

    async def on_payment_success(self, update_display_callback):
        """Appelé après un paiement réussi."""
        try:
            user_id = self.auth_service.get_user_id()
            if user_id:
                subscription = (
                    await self.subscription_service._load_subscription_from_supabase(  # noqa: E501
                        user_id
                    )
                )
                if subscription:
                    self.has_active_subscription = True
                    self.subscription_service.current_subscription = subscription

                    def update_ui():
                        try:
                            ui.notify(
                                'Abonnement activé !',
                                type='positive',
                                timeout=3000
                            )
                            update_display_callback()
                        except Exception as e:
                            logger.error(f"Erreur dans update_ui: {e}")

                    ui.timer(0.1, update_ui, once=True)
        except Exception as e:
            logger.error(f"Erreur lors du callback de paiement: {e}")

    def sync_refresh_subscription_status(self):
        """Rafraîchit le statut d'abonnement (wrapper synchrone)."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._async_refresh_subscription_status())
            else:
                loop.run_until_complete(
                    self._async_refresh_subscription_status()
                )
        except Exception as e:
            logger.error(f"Erreur lors du déclenchement du refresh: {e}")

    async def _async_refresh_subscription_status(self):
        """Rafraîchit le statut d'abonnement depuis Supabase."""
        try:
            user_id = self.auth_service.get_user_id()
            if not user_id:
                return

            subscription = (
                await self.subscription_service._load_subscription_with_retry(
                    user_id
                )
            )

            old_sub = self.subscription_service.current_subscription
            old_exists = old_sub is not None
            new_exists = subscription is not None

            old_id = old_sub.get('id') if old_sub else None
            new_id = subscription.get('id') if subscription else None

            old_has_subscription = self.has_active_subscription
            self.subscription_service.current_subscription = subscription
            self.has_active_subscription = subscription is not None

            subscription_changed = False

            if not old_exists and new_exists:
                subscription_changed = True
            elif old_exists and not new_exists:
                subscription_changed = True
            elif old_id != new_id:
                subscription_changed = True

            if subscription_changed:
                # Mettre à jour l'affichage via un wrapper qui gère le contexte UI
                try:
                    ui.timer(0.1, self.update_subscription_status_display, once=True)
                except Exception as timer_error:
                    # Si on est dans un contexte sans slot UI, appeler directement
                    logger.debug(f"Appel direct de update_subscription_status_display (pas de slot UI): {timer_error}")
                    try:
                        self.update_subscription_status_display()
                    except Exception:
                        pass  # Ignorer silencieusement si l'UI n'est pas prête

                if new_exists and not old_has_subscription:
                    try:
                        ui.timer(0.5, self._reload_interface_after_payment, once=True)
                    except Exception as timer_error:
                        # Si on est dans un contexte sans slot UI, appeler directement
                        logger.debug(f"Appel direct de _reload_interface_after_payment (pas de slot UI): {timer_error}")
                        try:
                            self._reload_interface_after_payment()
                        except Exception:
                            pass  # Ignorer silencieusement si l'UI n'est pas prête
        except Exception as e:
            logger.error(
                f"Erreur lors du rafraîchissement auto du statut: {e}"
            )

    def update_subscription_status_display(self):
        """Met à jour l'affichage du statut d'abonnement."""
        try:
            if self.subscription_status_label:
                status_info = (
                    self.subscription_service.get_subscription_status_display()
                )

                color_map = {
                    'red': '#ef4444',
                    'orange': '#f97316',
                    'green': '#22c55e'
                }
                status_color = color_map.get(status_info['color'], '#6b7280')

                self.subscription_status_label.text = status_info['text']
                self.subscription_status_label.style(
                    f'color: {status_color}; font-weight: bold;'
                )
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du statut: {e}")

    def _reload_interface_after_payment(self):
        """Recharge l'interface après un paiement réussi."""
        try:
            ui.notify(
                'Abonnement activé ! Redirection vers l\'application...',
                type='positive',
                timeout=3000
            )
            self.update_subscription_status_display()
        except Exception as e:
            logger.error(
                f"Erreur lors du rechargement de l'interface: {e}"
            )
            ui.notify(
                "Erreur lors du rechargement de l'interface",
                type='negative'
            )

