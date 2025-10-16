"""
Composants de dialogues réutilisables.
"""
from typing import Callable, Optional
from nicegui import ui
from ui.components.svg_icons import svg
from utils.logger import get_logger
from utils.notification_manager import notify
from utils.constants import ICON_WARNING, ICON_SUCCESS, ICON_ERROR
from utils.validators import validate_verification_code

logger = get_logger()


class VerificationDialog:
    """Dialogue de vérification de compte Telegram."""
    
    def __init__(
        self,
        account_name: str,
        phone: str,
        session_id: str,
        on_verify: Callable,
        on_cancel: Optional[Callable] = None
    ):
        """
        Initialise le dialogue de vérification.
        
        Args:
            account_name: Nom du compte
            phone: Numéro de téléphone
            session_id: ID de session
            on_verify: Fonction à appeler lors de la vérification
            on_cancel: Fonction à appeler lors de l'annulation (optionnel)
        """
        self.account_name = account_name
        self.phone = phone
        self.session_id = session_id
        self.on_verify = on_verify
        self.on_cancel = on_cancel
        self.dialog = None
    
    def show(self) -> None:
        """Affiche le dialogue de vérification."""
        self.dialog = ui.dialog().props('persistent')
        
        with self.dialog, ui.card().classes('w-96 p-6 card-modern'):
            with ui.row().classes('items-center gap-2 mb-4'):
                ui.html(svg('check_circle', 28, 'var(--primary)'))
                ui.label('Vérification').classes('text-2xl font-bold').style(
                    'color: var(--text-primary);'
                )
            
            with ui.column().classes('w-full gap-4'):
                ui.label(f'Compte: {self.account_name} ({self.phone})').classes('text-gray-600')
                
                ui.label('Code de vérification').classes('font-medium')
                # Input HTML natif
                code_html = '''
                <input 
                    type="text"
                    id="code_input_dialog_native"
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
                    id="password_input_dialog_native"
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
                    'background: #fef3c7; border-left: 3px solid var(--warning);'
                ):
                    with ui.row().classes('items-center gap-2'):
                        ui.html(svg(ICON_WARNING, 18, '#92400e'))
                        ui.label(
                            'Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram'
                        ).classes('text-sm').style('color: #92400e;')
                
                async def verify() -> None:
                    """Vérifie le code de vérification."""
                    # Récupérer les valeurs via JavaScript
                    try:
                        code = await ui.run_javascript('document.getElementById("code_input_dialog_native").value', timeout=1.0) or ""
                        code = str(code).strip()
                        password_val = await ui.run_javascript('document.getElementById("password_input_dialog_native").value', timeout=1.0) or ""
                        password = str(password_val).strip() if password_val else None
                    except Exception:
                        notify('Erreur de lecture des champs', type='negative')
                        return
                    
                    # Validation
                    is_valid, error_msg = validate_verification_code(code)
                    if not is_valid:
                        notify(error_msg, type='warning')
                        return
                    
                    try:
                        notify('Vérification en cours...', type='info')
                        await self.on_verify(self.session_id, code, password)
                        self.close()
                    except Exception as e:
                        logger.error(f"Erreur vérification: {e}")
                        notify(str(e), type='negative')
                
                def cancel() -> None:
                    """Annule la vérification."""
                    self.close()
                    if self.on_cancel:
                        self.on_cancel()
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=cancel).props('flat').style(
                        'color: var(--secondary);'
                    )
                    with ui.button(on_click=verify).classes('btn-primary'):
                        with ui.row().classes('items-center gap-1'):
                            ui.html(svg('check', 18, 'white'))
                            ui.label('Vérifier')
        
        self.dialog.open()
    
    def close(self) -> None:
        """Ferme le dialogue."""
        if self.dialog:
            self.dialog.close()


class ConfirmDialog:
    """Dialogue de confirmation générique."""
    
    def __init__(
        self,
        title: str,
        message: str,
        on_confirm: Callable,
        on_cancel: Optional[Callable] = None,
        confirm_text: str = "Confirmer",
        cancel_text: str = "Annuler",
        is_danger: bool = False
    ):
        """
        Initialise le dialogue de confirmation.
        
        Args:
            title: Titre du dialogue
            message: Message à afficher
            on_confirm: Fonction à appeler lors de la confirmation
            on_cancel: Fonction à appeler lors de l'annulation (optionnel)
            confirm_text: Texte du bouton de confirmation
            cancel_text: Texte du bouton d'annulation
            is_danger: Si True, affiche en rouge (pour les actions dangereuses)
        """
        self.title = title
        self.message = message
        self.on_confirm = on_confirm
        self.on_cancel = on_cancel
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text
        self.is_danger = is_danger
        self.dialog = None
    
    def show(self) -> None:
        """Affiche le dialogue de confirmation."""
        self.dialog = ui.dialog()
        
        with self.dialog, ui.card().classes('w-96 p-6 card-modern'):
            title_color = 'var(--danger)' if self.is_danger else 'var(--text-primary)'
            ui.label(self.title).classes('text-xl font-bold mb-4').style(
                f'color: {title_color};'
            )
            
            ui.label(self.message).classes('text-gray-700 mb-2')
            
            if self.is_danger:
                ui.label('Cette action est irréversible.').classes('text-sm text-gray-500 mt-2')
            
            async def confirm() -> None:
                """Confirme l'action."""
                try:
                    await self.on_confirm()
                    self.close()
                except Exception as e:
                    logger.error(f"Erreur confirmation: {e}")
                    notify(str(e), type='negative')
            
            def cancel() -> None:
                """Annule l'action."""
                self.close()
                if self.on_cancel:
                    self.on_cancel()
            
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button(self.cancel_text, on_click=cancel).props('flat').style(
                    'color: var(--secondary);'
                )
                
                if self.is_danger:
                    ui.button(self.confirm_text, on_click=confirm).props('color=red')
                else:
                    ui.button(self.confirm_text, on_click=confirm).classes('btn-primary')
        
        self.dialog.open()
    
    def close(self) -> None:
        """Ferme le dialogue."""
        if self.dialog:
            self.dialog.close()


class InfoDialog:
    """Dialogue d'information générique."""
    
    def __init__(
        self,
        title: str,
        message: str,
        icon: str = "info",
        button_text: str = "OK"
    ):
        """
        Initialise le dialogue d'information.
        
        Args:
            title: Titre du dialogue
            message: Message à afficher
            icon: Icône à afficher
            button_text: Texte du bouton
        """
        self.title = title
        self.message = message
        self.icon = icon
        self.button_text = button_text
        self.dialog = None
    
    def show(self) -> None:
        """Affiche le dialogue d'information."""
        self.dialog = ui.dialog()
        
        with self.dialog, ui.card().classes('w-96 p-6 card-modern text-center'):
            ui.html(svg('info', 60, 'var(--primary)'))
            ui.label(self.title).classes('text-xl font-bold mb-2').style(
                'color: var(--text-primary);'
            )
            ui.label(self.message).classes('text-gray-600 mb-4')
            
            with ui.row().classes('w-full justify-center'):
                ui.button(self.button_text, on_click=self.close).classes('btn-primary')
        
        self.dialog.open()
    
    def close(self) -> None:
        """Ferme le dialogue."""
        if self.dialog:
            self.dialog.close()

