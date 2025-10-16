"""Dialogues de gestion des comptes Telegram."""
import asyncio
from typing import Callable, Optional

from nicegui import ui

from ui.components.dialogs import ConfirmDialog
from ui.components.svg_icons import svg
from utils.constants import ICON_WARNING
from utils.logger import get_logger
from utils.notification_manager import notify
from utils.validators import (
    validate_phone_number,
    validate_verification_code
)

logger = get_logger()


class AccountDialogs:
    """Gère les dialogues de gestion des comptes."""

    def __init__(self, telegram_manager):
        """
        Initialise les dialogues de compte.

        Args:
            telegram_manager: Instance du gestionnaire Telegram.
        """
        self.telegram_manager = telegram_manager

    async def show_add_account_dialog(
        self,
        on_success_callback: Callable
    ) -> None:
        """
        Affiche le dialogue d'ajout de compte.

        Args:
            on_success_callback: Callback à appeler après succès.
        """
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6 card-modern'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.html(svg('add_circle', 28, 'var(--primary)'))
                ui.label('Ajouter un compte').classes(
                    'text-2xl font-bold'
                ).style('color: var(--text-primary);')

            with ui.column().classes('w-full gap-4'):
                ui.label('Numéro de téléphone').classes('font-medium')
                # Input HTML natif pour compatibilité PyInstaller
                phone_html = '''
                <input 
                    type="tel"
                    id="phone_input_native"
                    placeholder="+33612345678"
                    style="
                        width: 520px;
                        max-width: 100%;
                        height: 56px;
                        background: #ffffff;
                        border: 2px solid #d1d5db;
                        border-radius: 8px;
                        font-size: 16px;
                        padding: 14px 16px;
                        box-sizing: border-box;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    "
                />
                '''
                phone_input = ui.html(phone_html).classes('w-full')

                with ui.card().classes('bg-blue-50 p-3'):
                    with ui.row().classes('items-center gap-2'):
                        ui.html(svg('info', 20, '#1e40af'))
                        ui.label(
                            'Votre nom Telegram sera automatiquement récupéré '
                            'après connexion'
                        ).classes('text-sm text-blue-800')

                async def submit() -> None:
                    """Soumet le formulaire d'ajout de compte."""
                    # Récupérer le numéro via JavaScript
                    try:
                        phone = await ui.run_javascript('document.getElementById("phone_input_native").value', timeout=1.0) or ""
                        phone = str(phone).strip()
                    except Exception:
                        notify('Erreur de lecture du numéro', type='negative')
                        return

                    is_valid, error_msg = validate_phone_number(phone)
                    if not is_valid:
                        notify(error_msg, type='warning')
                        return

                    try:
                        notify(
                            'Envoi du code de vérification...',
                            type='info'
                        )

                        success, message, session_id = (
                            await self.telegram_manager.add_account(phone, None)
                        )

                        if success:
                            notify(
                                'Code envoyé ! Vérifiez votre Telegram',
                                type='positive'
                            )

                            dialog.clear()

                            with dialog:
                                self._render_verification_form(
                                    dialog,
                                    phone,
                                    session_id,
                                    on_success_callback
                                )
                        else:
                            notify(f'Erreur: {message}', type='negative')

                    except Exception as e:
                        logger.error(f"Erreur ajout compte: {e}")
                        notify(f'Erreur: {e}', type='negative')

                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props(
                        'flat'
                    ).style('color: var(--secondary);')
                    with ui.button(on_click=submit).classes('btn-primary'):
                        with ui.row().classes('items-center gap-1'):
                            ui.label('Continuer')
                            ui.html(svg('arrow_forward', 18, 'white'))

        dialog.open()

    def _render_verification_form(
        self,
        dialog,
        phone: str,
        session_id: str,
        on_success_callback: Callable
    ) -> None:
        """Rend le formulaire de vérification."""
        with ui.card().classes('w-96 p-6 card-modern'):
            ui.label('Vérification').classes('text-2xl font-bold mb-4').style(
                'color: var(--text-primary);'
            )

            with ui.column().classes('w-full gap-4'):
                ui.label(f'Téléphone: {phone}').classes('text-gray-600')

                ui.label('Code de vérification').classes('font-medium')
                # Input HTML natif
                code_html = '''
                <input 
                    type="text"
                    id="code_input_native"
                    placeholder="12345"
                    style="
                        width: 520px;
                        max-width: 100%;
                        height: 56px;
                        background: #ffffff;
                        border: 2px solid #d1d5db;
                        border-radius: 8px;
                        font-size: 16px;
                        padding: 14px 16px;
                        box-sizing: border-box;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    "
                />
                '''
                code_input = ui.html(code_html).classes('w-full')

                ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                # Input HTML natif pour password
                password_html = '''
                <input 
                    type="password"
                    id="password_input_native"
                    placeholder="Laissez vide si pas de 2FA"
                    style="
                        width: 520px;
                        max-width: 100%;
                        height: 56px;
                        background: #ffffff;
                        border: 2px solid #d1d5db;
                        border-radius: 8px;
                        font-size: 16px;
                        padding: 14px 16px;
                        box-sizing: border-box;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    "
                />
                '''
                password_input = ui.html(password_html).classes('w-full')

                with ui.card().classes('p-3').style(
                    'background: #fef3c7; '
                    'border-left: 3px solid var(--warning);'
                ):
                    with ui.row().classes('items-center gap-2'):
                        ui.html(svg(ICON_WARNING, 18, '#92400e'))
                        ui.label(
                            'Le mot de passe 2FA n\'est requis que si vous '
                            'l\'avez activé sur Telegram'
                        ).classes('text-sm').style('color: #92400e;')

                async def verify() -> None:
                    """Vérifie le code de vérification."""
                    # Récupérer les valeurs via JavaScript
                    try:
                        code = await ui.run_javascript('document.getElementById("code_input_native").value', timeout=1.0) or ""
                        code = str(code).strip()
                        password_val = await ui.run_javascript('document.getElementById("password_input_native").value', timeout=1.0) or ""
                        password = str(password_val).strip() if password_val else None
                    except Exception:
                        notify('Erreur de lecture des champs', type='negative')
                        return

                    is_valid, error_msg = validate_verification_code(code)
                    if not is_valid:
                        notify(error_msg, type='warning')
                        return

                    try:
                        notify('Vérification en cours...', type='info')
                        success_msg, error = (
                            await self.telegram_manager.verify_account(
                                session_id, code, password
                            )
                        )
                        if success_msg:
                            await self.telegram_manager.update_account_name_from_telegram(  # noqa: E501
                                session_id
                            )
                            notify(
                                'Compte ajouté avec succès !',
                                type='positive'
                            )
                            dialog.close()
                            await on_success_callback()
                        else:
                            notify(error, type='negative')
                    except Exception as e:
                        logger.error(f"Erreur vérification: {e}")
                        notify(str(e), type='negative')

                def cancel() -> None:
                    """Annule la vérification."""
                    dialog.close()

                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=cancel).props('flat').style(
                        'color: var(--secondary);'
                    )
                    ui.button('Vérifier', on_click=verify).classes(
                        'btn-primary'
                    )

    async def show_delete_account_dialog(
        self,
        account: dict,
        on_success_callback: Callable
    ) -> None:
        """
        Affiche le dialogue de suppression de compte.

        Args:
            account: Dictionnaire avec les infos du compte.
            on_success_callback: Callback à appeler après succès.
        """
        session_id = account.get('session_id')
        phone = account.get('phone')
        account_name = account.get('account_name')

        async def on_confirm() -> None:
            """Confirme la suppression."""
            await self.telegram_manager.remove_account(session_id)
            notify('Compte supprimé', type='positive')
            await on_success_callback()

        confirm_dialog = ConfirmDialog(
            title="Supprimer le compte ?",
            message=f"Compte: {account_name} ({phone})",
            on_confirm=on_confirm,
            confirm_text="Supprimer",
            is_danger=True
        )
        confirm_dialog.show()

    async def show_reconnect_account_dialog(
        self,
        account: dict,
        on_success_callback: Callable
    ) -> None:
        """
        Affiche le dialogue de reconnexion de compte.

        Args:
            account: Dictionnaire avec les infos du compte.
            on_success_callback: Callback à appeler après succès.
        """
        session_id = account.get('session_id')
        phone = account.get('phone')
        account_name = account.get('account_name')

        try:
            notify('Envoi du nouveau code de vérification...', type='info')
            success, message = await self.telegram_manager.resend_code(
                session_id
            )

            if success:
                notify(
                    'Code envoyé ! Vérifiez votre Telegram',
                    type='positive'
                )

                verification_dialog = ui.dialog().props('persistent')

                with verification_dialog, ui.card().classes(
                    'w-96 p-6 card-modern'
                ):
                    ui.label('Vérification').classes(
                        'text-2xl font-bold mb-4'
                    ).style('color: var(--text-primary);')

                    with ui.column().classes('w-full gap-4'):
                        ui.label(
                            f'Compte: {account_name} ({phone})'
                        ).classes('text-gray-600')

                        ui.label('Code de vérification').classes('font-medium')
                        # Input HTML natif
                        code_html = '''
                        <input 
                            type="text"
                            id="code_input_reconnect_native"
                            placeholder="12345"
                            style="
                                width: 520px;
                                max-width: 100%;
                                height: 56px;
                                background: #ffffff;
                                border: 2px solid #d1d5db;
                                border-radius: 8px;
                                font-size: 16px;
                                padding: 14px 16px;
                                box-sizing: border-box;
                                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                            "
                        />
                        '''
                        code_input = ui.html(code_html).classes('w-full')

                        ui.label('Mot de passe 2FA (si activé)').classes(
                            'font-medium'
                        )
                        # Input HTML natif pour password
                        password_html = '''
                        <input 
                            type="password"
                            id="password_input_reconnect_native"
                            placeholder="Laissez vide si pas de 2FA"
                            style="
                                width: 520px;
                                max-width: 100%;
                                height: 56px;
                                background: #ffffff;
                                border: 2px solid #d1d5db;
                                border-radius: 8px;
                                font-size: 16px;
                                padding: 14px 16px;
                                box-sizing: border-box;
                                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                            "
                        />
                        '''
                        password_input = ui.html(password_html).classes('w-full')

                        with ui.card().classes('p-3').style(
                            'background: #fef3c7; '
                            'border-left: 3px solid var(--warning);'
                        ):
                            with ui.row().classes('items-center gap-2'):
                                ui.html(svg(ICON_WARNING, 18, '#92400e'))
                                ui.label(
                                    'Le mot de passe 2FA n\'est requis que si '
                                    'vous l\'avez activé sur Telegram'
                                ).classes('text-sm').style('color: #92400e;')

                        async def verify() -> None:
                            """Vérifie le code de vérification."""
                            # Récupérer les valeurs via JavaScript
                            try:
                                code = await ui.run_javascript('document.getElementById("code_input_reconnect_native").value', timeout=1.0) or ""
                                code = str(code).strip()
                                password_val = await ui.run_javascript('document.getElementById("password_input_reconnect_native").value', timeout=1.0) or ""
                                password = str(password_val).strip() if password_val else None
                            except Exception:
                                notify('Erreur de lecture des champs', type='negative')
                                return

                            is_valid, error_msg = validate_verification_code(
                                code
                            )
                            if not is_valid:
                                notify(error_msg, type='warning')
                                return

                            try:
                                notify('Vérification en cours...', type='info')
                                success_msg, error = (
                                    await self.telegram_manager.verify_account(
                                        session_id, code, password
                                    )
                                )
                                if success_msg:
                                    notify(
                                        'Compte reconnecté avec succès !',
                                        type='positive'
                                    )
                                    verification_dialog.close()
                                    await on_success_callback()
                                else:
                                    notify(error, type='negative')
                            except Exception as e:
                                logger.error(f"Erreur vérification: {e}")
                                notify(str(e), type='negative')

                        def cancel() -> None:
                            """Annule la vérification."""
                            verification_dialog.close()

                        with ui.row().classes('w-full justify-end gap-2 mt-4'):
                            ui.button('Annuler', on_click=cancel).props(
                                'flat'
                            ).style('color: var(--secondary);')
                            ui.button('Vérifier', on_click=verify).classes(
                                'btn-primary'
                            )

                verification_dialog.open()
            else:
                notify(f'Erreur: {message}', type='negative')

        except Exception as e:
            logger.error(f"Erreur reconnexion: {e}")
            notify(f'Erreur: {e}', type='negative')

