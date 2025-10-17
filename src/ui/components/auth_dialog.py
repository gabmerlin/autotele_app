"""
Composants de dialogue d'authentification (Login/Signup)
"""
from nicegui import ui
from typing import Callable, Optional
import re

from services.auth_service import get_auth_service
from utils.logger import get_logger

logger = get_logger()


class AuthDialog:
    """Dialogue d'authentification avec login et signup"""
    
    def __init__(self, on_success: Optional[Callable] = None):
        """
        Args:
            on_success: Callback appelé après authentification réussie
        """
        self.auth_service = get_auth_service()
        self.on_success = on_success
        self.dialog = None
        self.mode = 'login'  # 'login' ou 'signup'
        
        # Champs du formulaire
        self.email_input = None
        self.password_input = None
        self.password_confirm_input = None
        self.name_input = None
        self.remember_me_checkbox = None
        self.error_label = None
        self.submit_button = None
        self.container = None
    
    def show(self):
        """Affiche le dialogue d'authentification - VERSION SANS DIALOG"""
        # BYPASS COMPLET du système ui.dialog() qui bloque les interactions
        # Créer directement dans le conteneur principal
        with ui.column().classes('w-full h-screen items-center justify-center').style(
            'position: fixed !important; '
            'top: 0 !important; '
            'left: 0 !important; '
            'z-index: 99999 !important; '
            'background: rgba(100, 100, 100, 0.8) !important; '
            'pointer-events: auto !important;'
        ):
            with ui.card().classes('w-full p-8').style(
                'pointer-events: auto !important; '
                'z-index: 999999 !important; '
                'position: relative !important; '
                'max-width: 600px !important; '
                'min-width: 550px !important;'
            ):
                # Conteneur principal qui sera rafraîchi lors du changement de mode
                self.container = ui.column().classes('w-full gap-4')
                with self.container:
                    self._render_content()
    
    def _render_content(self):
        """Affiche le contenu du dialogue selon le mode"""
        # Clear le contenu précédent lors du changement de mode
        if self.container and hasattr(self.container, 'clear'):
            self.container.clear()
        
        with self.container:
            # En-tête
            with ui.row().classes('w-full items-center justify-between'):
                ui.label('AutoTele').classes('text-2xl font-bold').style('font-family: "Roboto", sans-serif')
                ui.html('''
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="#1e40af">
                        <path d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zM9 6c0-1.66 1.34-3 3-3s3 1.34 3 3v2H9V6zm9 14H6V10h12v10zm-6-3c1.1 0 2-.9 2-2s-.9-2-2-2-2 .9-2 2 .9 2 2 2z"/>
                    </svg>
                ''')
            
            ui.separator()
            
            # Titre selon le mode
            if self.mode == 'login':
                ui.label('Connexion').classes('text-xl font-semibold')
                ui.label('Connectez-vous pour accéder à l\'application').classes('text-sm text-gray-600')
            else:
                ui.label('Créer un compte').classes('text-xl font-semibold')
                ui.label('Rejoignez AutoTele dès aujourd\'hui').classes('text-sm text-gray-600')
            
            # Formulaire
            with ui.column().classes('w-full gap-4').style('min-width: 380px; padding: 10px;'):
                self._render_form()
            
            # Message d'erreur
            self.error_label = ui.label('').classes('text-red-500 text-sm min-h-6').style('min-height:18px;')
            
            # Boutons d'action
            with ui.row().classes('w-full gap-2'):
                if self.mode == 'login':
                    self.submit_button = ui.button('Se connecter', on_click=self._handle_login) \
                        .classes('flex-1') \
                        .props('color=primary')
                else:
                    self.submit_button = ui.button('Créer mon compte', on_click=self._handle_signup) \
                        .classes('flex-1') \
                        .props('color=primary')
            
            # Lien pour changer de mode
            with ui.row().classes('w-full justify-center mt-2'):
                if self.mode == 'login':
                    ui.label('Pas encore de compte ?').classes('text-sm text-gray-600')
                    ui.button('Créer un compte', on_click=lambda: self._switch_mode('signup')) \
                        .props('flat dense no-caps') \
                        .classes('text-sm text-primary')
                else:
                    ui.label('Déjà un compte ?').classes('text-sm text-gray-600')
                    ui.button('Se connecter', on_click=lambda: self._switch_mode('login')) \
                        .props('flat dense no-caps') \
                        .classes('text-sm text-primary')
            
            # Lien mot de passe oublié (mode login uniquement)
            if self.mode == 'login':
                with ui.row().classes('w-full justify-center mt-1'):
                    ui.button('Mot de passe oublié ?', on_click=self._show_reset_password) \
                        .props('flat dense no-caps') \
                        .classes('text-xs text-gray-500')
    
    def _render_form(self):
        """Affiche les champs du formulaire"""
        if self.mode == 'signup':
            # Nom complet (optionnel)
            self.name_input = ui.input('Nom complet (optionnel)') \
                .classes('w-full') \
                .props('outlined dense')
        
        # EMAIL - Input HTML natif (compatible PyInstaller)
        ui.label('Email').classes('text-sm font-medium text-gray-700')
        email_html = '''
        <input 
            type="email" 
            id="email_input_native" 
            placeholder="votre@email.com"
            autofocus
            style="
                width: 520px;
                max-width: 100%;
                height: 56px;
                background: #ffffff;
                border: 2px solid #d1d5db;
                border-radius: 8px;
                font-size: 16px;
                padding: 14px 16px;
                pointer-events: auto;
                cursor: text;
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                transition: border-color 0.2s;
            "
            onfocus="this.style.borderColor='#3b82f6'; this.style.outline='2px solid #dbeafe';"
            onblur="this.style.borderColor='#d1d5db'; this.style.outline='none';"
        />
        '''
        self.email_input = ui.html(email_html)
        
        # MOT DE PASSE - Input HTML natif (compatible PyInstaller)
        ui.label('Mot de passe').classes('text-sm font-medium text-gray-700 mt-3')
        password_html = '''
        <input 
            type="password" 
            id="password_input_native" 
            placeholder="••••••••"
            style="
                width: 520px;
                max-width: 100%;
                height: 56px;
                background: #ffffff;
                border: 2px solid #d1d5db;
                border-radius: 8px;
                font-size: 16px;
                padding: 14px 16px;
                pointer-events: auto;
                cursor: text;
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                transition: border-color 0.2s;
            "
            onfocus="this.style.borderColor='#3b82f6'; this.style.outline='2px solid #dbeafe';"
            onblur="this.style.borderColor='#d1d5db'; this.style.outline='none';"
        />
        '''
        self.password_input = ui.html(password_html)
        
        # Checkbox "Se souvenir de moi" (mode login uniquement)
        if self.mode == 'login':
            with ui.row().classes('w-full items-center mt-2 gap-2'):
                self.remember_me_checkbox = ui.checkbox('Se souvenir de moi', value=True) \
                    .classes('text-sm') \
                    .props('dense')
                ui.label('(rester connecté jusqu\'à déconnexion manuelle)') \
                    .classes('text-xs text-gray-500')
        
        # Confirmation mot de passe (signup uniquement) - HTML natif aussi
        if self.mode == 'signup':
            ui.label('Confirmer le mot de passe').classes('text-sm font-medium text-gray-700 mt-3')
            password_confirm_html = '''
            <input 
                type="password" 
                id="password_confirm_input_native" 
                placeholder="••••••••"
                style="
                    width: 520px;
                    max-width: 100%;
                    height: 56px;
                    background: #ffffff;
                    border: 2px solid #d1d5db;
                    border-radius: 8px;
                    font-size: 16px;
                    padding: 14px 16px;
                    pointer-events: auto;
                    cursor: text;
                    box-sizing: border-box;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    transition: border-color 0.2s;
                "
                onfocus="this.style.borderColor='#3b82f6'; this.style.outline='2px solid #dbeafe';"
                onblur="this.style.borderColor='#d1d5db'; this.style.outline='none';"
            />
            '''
            self.password_confirm_input = ui.html(password_confirm_html) \
                .on('keydown.enter', lambda: self._handle_submit())
            
            # Indication sur le mot de passe
            ui.label('Le mot de passe doit contenir au moins 6 caractères').classes('text-xs text-gray-500')
    
    def _switch_mode(self, mode: str):
        """Change le mode du dialogue (login/signup)"""
        self.mode = mode
        self._render_content()
    
    def _validate_email(self, email: str) -> bool:
        """Valide le format de l'email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    async def _validate_form(self) -> tuple[bool, str]:
        """Valide le formulaire et retourne (valide, message_erreur)"""
        # Récupération via JavaScript des valeurs des inputs HTML natifs
        try:
            email = await ui.run_javascript('document.getElementById("email_input_native").value', timeout=1.0) or ""
            password = await ui.run_javascript('document.getElementById("password_input_native").value', timeout=1.0) or ""
            email = str(email).strip()
            password = str(password)
        except Exception as e:
            logger.error(f"Erreur lecture champs: {e}")
            return False, "Erreur de lecture des champs"
        
        if not email:
            return False, "L'email est requis"
        
        if not self._validate_email(email):
            return False, "Format d'email invalide"
        
        if not password:
            return False, "Le mot de passe est requis"
        
        if len(password) < 6:
            return False, "Le mot de passe doit contenir au moins 6 caractères"
        
        # Validations supplémentaires pour signup
        if self.mode == 'signup':
            try:
                password_confirm = await ui.run_javascript('document.getElementById("password_confirm_input_native").value', timeout=1.0) or ""
                password_confirm = str(password_confirm)
            except Exception as e:
                logger.error(f"Erreur lecture confirmation: {e}")
                return False, "Erreur de lecture de la confirmation"
            
            if not password_confirm:
                return False, "La confirmation du mot de passe est requise"
            
            if password != password_confirm:
                return False, "Les mots de passe ne correspondent pas"
        
        return True, ""
    
    async def _handle_login(self):
        """Gère la connexion"""
        # Réinitialiser l'erreur
        self.error_label.text = ''
        
        # Valider le formulaire
        valid, error = await self._validate_form()
        if not valid:
            self.error_label.text = error
            return
        
        # Désactiver le bouton
        self.submit_button.props('loading')
        
        try:
            # Récupérer les valeurs via JavaScript
            email = await ui.run_javascript('document.getElementById("email_input_native").value', timeout=1.0) or ""
            password = await ui.run_javascript('document.getElementById("password_input_native").value', timeout=1.0) or ""
            email = str(email).strip()
            password = str(password)
            
            # Récupérer l'état de la checkbox "Se souvenir de moi"
            remember_me = self.remember_me_checkbox.value if self.remember_me_checkbox else True
            
            # Passer remember_me à sign_in
            success, message = await self.auth_service.sign_in(email, password, remember_me)
            
            if success:
                # Appeler le callback de succès (qui gérera la fermeture du dialogue)
                if self.on_success:
                    await self.on_success()
            else:
                self.error_label.text = message
        
        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {e}")
            self.error_label.text = f"Erreur: {str(e)}"
        
        finally:
            self.submit_button.props(remove='loading')
    
    async def _handle_signup(self):
        """Gère la création de compte"""
        # Réinitialiser l'erreur
        self.error_label.text = ''
        
        # Valider le formulaire
        valid, error = await self._validate_form()
        if not valid:
            self.error_label.text = error
            return
        
        # Désactiver le bouton
        self.submit_button.props('loading')
        
        try:
            # Récupérer les valeurs via JavaScript
            email = await ui.run_javascript('document.getElementById("email_input_native").value', timeout=1.0) or ""
            password = await ui.run_javascript('document.getElementById("password_input_native").value', timeout=1.0) or ""
            email = str(email).strip()
            password = str(password)
            name = self.name_input.value.strip() if self.name_input else ''
            
            metadata = {}
            if name:
                metadata['name'] = name
            
            success, message = await self.auth_service.sign_up(email, password, metadata)
            
            if success:
                # Tenter de se connecter automatiquement
                success_login, _ = await self.auth_service.sign_in(email, password)
                
                if success_login:
                    # Appeler le callback de succès (qui gérera la fermeture)
                    if self.on_success:
                        await self.on_success()
                else:
                    # Afficher un message et passer en mode login
                    self.error_label.text = "Compte créé ! Veuillez vous connecter."
                    self._switch_mode('login')
            else:
                self.error_label.text = message
        
        except Exception as e:
            logger.error(f"Erreur lors de la création de compte: {e}")
            self.error_label.text = f"Erreur: {str(e)}"
        
        finally:
            self.submit_button.props(remove='loading')
    
    async def _handle_submit(self):
        """Gère la soumission du formulaire (Enter)"""
        if self.mode == 'login':
            await self._handle_login()
        else:
            await self._handle_signup()
    
    async def _show_reset_password(self):
        """Affiche le dialogue de réinitialisation de mot de passe"""
        reset_dialog = ui.dialog()
        # Forcer un z-index élevé pour apparaître au-dessus du dialogue de login
        reset_dialog._props['style'] = 'z-index: 100000 !important;'
        
        with reset_dialog, ui.card().classes('p-6').style('z-index: 100001 !important;'):
            ui.label('Réinitialiser le mot de passe').classes('text-lg font-semibold')
            ui.label('Entrez votre email pour recevoir un lien de réinitialisation').classes('text-sm text-gray-600 mb-4')
            
            reset_email = ui.input('Email') \
                .classes('w-full') \
                .props('outlined dense type=email')
            
            error_msg = ui.label('').classes('text-red-500 text-sm')
            success_msg = ui.label('').classes('text-green-500 text-sm')
            
            async def send_reset():
                error_msg.text = ''
                success_msg.text = ''
                
                email = reset_email.value.strip()
                if not email or not self._validate_email(email):
                    error_msg.text = "Email invalide"
                    return
                
                success, message = await self.auth_service.reset_password(email)
                if success:
                    success_msg.text = message
                else:
                    error_msg.text = message
            
            with ui.row().classes('w-full gap-2 mt-4'):
                ui.button('Annuler', on_click=reset_dialog.close) \
                    .props('flat')
                ui.button('Envoyer', on_click=send_reset) \
                    .props('color=primary')
        
        reset_dialog.open()


def show_auth_dialog(on_success: Optional[Callable] = None):
    """
    Affiche le dialogue d'authentification
    
    Args:
        on_success: Callback appelé après authentification réussie
    """
    dialog = AuthDialog(on_success)
    dialog.show()

