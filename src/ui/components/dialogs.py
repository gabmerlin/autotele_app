"""
Composants de dialogues réutilisables.
"""
from typing import Callable, Optional
from nicegui import ui
from utils.logger import get_logger
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
            ui.label('✓ Vérification').classes('text-2xl font-bold mb-4').style(
                'color: var(--text-primary);'
            )
            
            with ui.column().classes('w-full gap-4'):
                ui.label(f'Compte: {self.account_name} ({self.phone})').classes('text-gray-600')
                
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
                        ui.notify(error_msg, type='warning')
                        return
                    
                    try:
                        ui.notify('Vérification en cours...', type='info')
                        await self.on_verify(self.session_id, code, password)
                        self.close()
                    except Exception as e:
                        logger.error(f"Erreur vérification: {e}")
                        ui.notify(f'{ICON_ERROR} {e}', type='negative')
                
                def cancel() -> None:
                    """Annule la vérification."""
                    self.close()
                    if self.on_cancel:
                        self.on_cancel()
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=cancel).props('flat').style(
                        'color: var(--secondary);'
                    )
                    ui.button('✓ Vérifier', on_click=verify).classes('btn-primary')
        
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
                    ui.notify(f'{ICON_ERROR} {e}', type='negative')
            
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
        icon: str = "ℹ️",
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
            ui.label(self.icon).classes('text-5xl mb-3')
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

