"""
AutoTele - Application de planification Telegram
Interface simple avec NiceGUI
"""
import sys
import asyncio
from pathlib import Path
from typing import Optional

# Ajouter le répertoire src au path
sys.path.insert(0, str(Path(__file__).parent))

from nicegui import ui
from utils.logger import get_logger
from core.telegram_manager import TelegramManager

logger = get_logger()


class AutoTeleApp:
    """Application principale AutoTele"""
    
    def __init__(self):
        self.current_page = 'comptes'
        self.content_area = None
        self.telegram_manager = TelegramManager()
        self.temp_phone = None
        self.temp_session_id = None
        self.verification_dialog_instance = None
    
    async def load_existing_sessions(self):
        """Charge les sessions existantes au démarrage"""
        try:
            # Charger les sessions avec la méthode async qui fait tout
            await self.telegram_manager.load_existing_sessions()
            
            # Compter les comptes chargés
            nb_accounts = len(self.telegram_manager.list_accounts())
            
            # Rafraîchir la page des comptes pour afficher les sessions
            if nb_accounts > 0:
                self.show_page('comptes')
        except Exception as e:
            logger.error(f"Erreur chargement sessions: {e}")
    
    def create_sidebar(self):
        """Crée le menu latéral gauche"""
        with ui.column().classes('w-64 h-screen bg-gray-100 p-4 gap-2'):
            # Logo/Titre
            ui.label('🚀 AutoTele').classes('text-2xl font-bold mb-4')
            ui.separator()
            
            # Menu items
            ui.button('📱 Compte Telegram', on_click=lambda: self.show_page('comptes')).props('flat align=left').classes('w-full')
            ui.button('✉️ Nouveau Messages', on_click=lambda: self.show_page('nouveau')).props('flat align=left').classes('w-full')
            ui.button('📤 Envoi en cours', on_click=lambda: self.show_page('envoi')).props('flat align=left').classes('w-full')
            ui.button('📅 Messages Programmé', on_click=lambda: self.show_page('programme')).props('flat align=left').classes('w-full')
            
            ui.space()
            
            # Footer
            with ui.row().classes('items-center gap-2'):
                ui.label('Version 2.0').classes('text-xs text-gray-500')
    
    def show_page(self, page_name: str):
        """Affiche une page spécifique"""
        self.current_page = page_name
        
        if self.content_area:
            self.content_area.clear()
            
            with self.content_area:
                if page_name == 'comptes':
                    self.page_comptes()
                elif page_name == 'nouveau':
                    self.page_nouveau()
                elif page_name == 'envoi':
                    self.page_envoi()
                elif page_name == 'programme':
                    self.page_programme()
            
            # Forcer le rafraîchissement de NiceGUI
            self.content_area.update()
    
    def page_comptes(self):
        """Page de gestion des comptes Telegram"""
        with ui.column().classes('w-full gap-4 p-6'):
            ui.label('📱 Compte Telegram').classes('text-3xl font-bold')
            ui.separator()
            
            # Liste des comptes
            accounts = self.telegram_manager.list_accounts()
            
            if accounts:
                for account in accounts:
                    with ui.card().classes('w-full p-4'):
                        with ui.row().classes('w-full items-center gap-4'):
                            status_icon = '🟢' if account.get('is_connected', False) else '🔴'
                            ui.label(f"{status_icon} {account.get('account_name', 'Sans nom')}").classes('text-lg font-bold')
                            ui.label(f"({account.get('phone', 'N/A')})").classes('text-gray-600')
                            ui.space()
                            
                            # Boutons d'action
                            with ui.row().classes('gap-2'):
                                if not account.get('is_connected', False):
                                    ui.button('🔄 Se reconnecter', on_click=lambda a=account: self.reconnect_account(a)).props('flat color=orange')
                                ui.button('🗑️ Supprimer', on_click=lambda a=account: self.delete_account(a)).props('flat color=red')
            else:
                with ui.card().classes('w-full p-6'):
                    ui.label('Aucun compte configuré').classes('text-gray-600')
                    ui.label('Cliquez sur "Ajouter un compte" pour commencer').classes('text-sm text-gray-500 mt-2')
            
            # Bouton ajouter
            ui.button('➕ Ajouter un compte', on_click=self.add_account_dialog).props('color=primary size=lg').classes('w-full')
            
            # Bouton de secours pour le popup de vérification
            if self.temp_phone and self.temp_session_id:
                ui.button('🔐 Ouvrir popup de vérification', on_click=self.create_verification_dialog).props('color=accent size=lg').classes('w-full mt-2')
    
    async def add_account_dialog(self):
        """Dialogue pour ajouter un compte"""
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6'):
            ui.label('➕ Ajouter un compte Telegram').classes('text-2xl font-bold mb-4')
            
            with ui.column().classes('w-full gap-4'):
                ui.label('Numéro de téléphone').classes('font-medium')
                phone_input = ui.input(placeholder='+33612345678').classes('w-full')
                
                ui.label('Nom du compte (optionnel)').classes('font-medium')
                name_input = ui.input(placeholder='Ex: Mon Compte Pro').classes('w-full')
                
                with ui.card().classes('bg-blue-50 p-3'):
                    ui.label('✅ Simple : Entrez votre numéro, recevez le code, connectez-vous !').classes('text-sm text-blue-800')
                
                async def submit():
                    name = name_input.value.strip()
                    phone = phone_input.value.strip()
                    
                    if not phone:
                        ui.notify('Veuillez entrer un numéro de téléphone', type='warning')
                        return
                    
                    if not phone.startswith('+'):
                        ui.notify('Le numéro doit commencer par + (ex: +33612345678)', type='warning')
                        return
                    
                    # Si pas de nom, utiliser le numéro comme nom
                    if not name:
                        name = f"Compte {phone}"
                    
                    try:
                        ui.notify('Envoi du code de vérification...', type='info')
                        
                        # Ajouter le compte et envoyer le code
                        success, message, session_id = await self.telegram_manager.add_account(phone, name)
                        
                        if success:
                            self.temp_phone = phone
                            self.temp_session_id = session_id
                            ui.notify('Code envoyé ! Vérifiez votre Telegram', type='positive')
                            
                            # Créer le dialog de vérification dans le même contexte
                            verification_dialog = ui.dialog().props('persistent')
                            
                            with verification_dialog, ui.card().classes('w-96 p-6'):
                                ui.label('🔐 Vérification').classes('text-2xl font-bold mb-4')
                                
                                with ui.column().classes('w-full gap-4'):
                                    ui.label(f'Compte: {phone}').classes('text-gray-600')
                                    
                                    ui.label('Code de vérification').classes('font-medium')
                                    code_input = ui.input(placeholder='12345').classes('w-full')
                                    
                                    ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                                    password_input = ui.input(placeholder='Laissez vide si pas de 2FA', password=True, password_toggle_button=True).classes('w-full')
                                    
                                    with ui.card().classes('bg-yellow-50 p-3'):
                                        ui.label('⚠️ Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram').classes('text-sm text-yellow-800')
                                    
                                    async def verify():
                                        code = code_input.value.strip()
                                        password = password_input.value.strip() if password_input.value else None
                                        
                                        if not code:
                                            ui.notify('Veuillez entrer le code de vérification', type='warning')
                                            return
                                        
                                        try:
                                            ui.notify('Vérification en cours...', type='info')
                                            
                                            success, error = await self.telegram_manager.verify_account(session_id, code, password)
                                            
                                            if success:
                                                verification_dialog.close()
                                                dialog.close()
                                                ui.notify('✅ Compte ajouté avec succès !', type='positive')
                                                self.temp_phone = None
                                                self.temp_session_id = None
                                                # Rafraîchir après un court délai
                                                ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
                                            else:
                                                ui.notify(f'❌ {error}', type='negative')
                                        
                                        except Exception as e:
                                            logger.error(f"Erreur vérification: {e}")
                                            ui.notify(f'Erreur: {e}', type='negative')
                                    
                                    with ui.row().classes('w-full justify-end gap-2 mt-4'):
                                        ui.button('Annuler', on_click=verification_dialog.close).props('flat')
                                        ui.button('Vérifier', on_click=verify).props('color=primary')
                            
                            verification_dialog.open()
                        else:
                            ui.notify(f'Erreur: {message}', type='negative')
                    
                    except Exception as e:
                        logger.error(f"Erreur ajout compte: {e}")
                        ui.notify(f'Erreur: {e}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat')
                    ui.button('Continuer', on_click=submit).props('color=primary')
        
        dialog.open()
    
    def open_verification_popup(self):
        """Ouvre le popup de vérification"""
        if self.verification_dialog_instance:
            self.verification_dialog_instance.close()
        self.create_verification_dialog()
    
    def create_verification_dialog(self):
        """Crée et ouvre le dialogue de vérification"""
        dialog = ui.dialog().props('persistent')
        self.verification_dialog_instance = dialog
        
        with dialog, ui.card().classes('w-96 p-6'):
            ui.label('🔐 Vérification').classes('text-2xl font-bold mb-4')
            
            with ui.column().classes('w-full gap-4'):
                ui.label(f'Compte: {self.temp_phone}').classes('text-gray-600')
                
                ui.label('Code de vérification').classes('font-medium')
                code_input = ui.input(placeholder='12345').classes('w-full')
                
                ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                password_input = ui.input(placeholder='Laissez vide si pas de 2FA', password=True, password_toggle_button=True).classes('w-full')
                
                with ui.card().classes('bg-yellow-50 p-3'):
                    ui.label('⚠️ Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram').classes('text-sm text-yellow-800')
                
                async def verify():
                    code = code_input.value.strip()
                    password = password_input.value.strip() if password_input.value else None
                    
                    if not code:
                        ui.notify('Veuillez entrer le code de vérification', type='warning')
                        return
                    
                    try:
                        ui.notify('Vérification en cours...', type='info')
                        
                        success, error = await self.telegram_manager.verify_account(self.temp_session_id, code, password)
                        
                        if success:
                            logger.info(f"Vérification réussie pour {self.temp_phone}")
                            dialog.close()
                            ui.notify('✅ Compte ajouté avec succès !', type='positive')
                            self.temp_phone = None
                            self.temp_session_id = None
                            # Rafraîchir après un court délai pour s'assurer que tout est à jour
                            ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
                        else:
                            ui.notify(f'❌ {error}', type='negative')
                    
                    except Exception as e:
                        logger.error(f"Erreur vérification: {e}")
                        ui.notify(f'Erreur: {e}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat')
                    ui.button('Vérifier', on_click=verify).props('color=primary')
        
        dialog.open()
    
    async def reconnect_account(self, account):
        """Reconnecte un compte non autorisé"""
        session_id = account.get('session_id')
        phone = account.get('phone')
        
        try:
            # Renvoyer le code
            ui.notify('Envoi du nouveau code de vérification...', type='info')
            success, message = await self.telegram_manager.resend_code(session_id)
            
            if success:
                # Stocker les infos temporaires
                self.temp_phone = phone
                self.temp_session_id = session_id
                
                ui.notify('Code envoyé ! Vérifiez votre Telegram', type='positive')
                
                # Créer le dialog de vérification
                verification_dialog = ui.dialog().props('persistent')
                
                with verification_dialog, ui.card().classes('w-96 p-6'):
                    ui.label('🔄 Reconnexion').classes('text-2xl font-bold mb-4')
                    
                    with ui.column().classes('w-full gap-4'):
                        ui.label(f'Compte: {phone}').classes('text-gray-600')
                        
                        ui.label('Code de vérification').classes('font-medium')
                        code_input = ui.input(placeholder='12345').classes('w-full')
                        
                        ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                        password_input = ui.input(placeholder='Laissez vide si pas de 2FA', password=True, password_toggle_button=True).classes('w-full')
                        
                        with ui.card().classes('bg-orange-50 p-3'):
                            ui.label('⚠️ Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram').classes('text-sm text-orange-800')
                        
                        async def verify():
                            code = code_input.value.strip()
                            password = password_input.value.strip() if password_input.value else None
                            
                            if not code:
                                ui.notify('Veuillez entrer le code de vérification', type='warning')
                                return
                            
                            try:
                                ui.notify('Vérification en cours...', type='info')
                                
                                success, error = await self.telegram_manager.verify_account(session_id, code, password)
                                
                                if success:
                                    verification_dialog.close()
                                    ui.notify('✅ Compte reconnecté avec succès !', type='positive')
                                    self.temp_phone = None
                                    self.temp_session_id = None
                                    # Rafraîchir après un court délai
                                    ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
                                else:
                                    ui.notify(f'❌ {error}', type='negative')
                            
                            except Exception as e:
                                logger.error(f"Erreur vérification reconnexion: {e}")
                                ui.notify(f'Erreur: {e}', type='negative')
                        
                        with ui.row().classes('w-full justify-end gap-2 mt-4'):
                            ui.button('Annuler', on_click=verification_dialog.close).props('flat')
                            ui.button('Vérifier', on_click=verify).props('color=primary')
                
                verification_dialog.open()
            else:
                ui.notify(f'Erreur: {message}', type='negative')
                
        except Exception as e:
            logger.error(f"Erreur reconnexion compte: {e}")
            ui.notify(f'Erreur: {e}', type='negative')
    
    async def delete_account(self, account):
        """Supprime un compte"""
        session_id = account.get('session_id')
        phone = account.get('phone')
        
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6'):
            ui.label('⚠️ Supprimer le compte ?').classes('text-xl font-bold text-red-600 mb-4')
            ui.label(f'Compte: {account.get("account_name")} ({phone})').classes('text-gray-700')
            ui.label('Cette action est irréversible.').classes('text-sm text-gray-500 mt-2')
            
            async def confirm():
                try:
                    await self.telegram_manager.remove_account(session_id)
                    dialog.close()
                    ui.notify('✅ Compte supprimé', type='positive')
                    # Rafraîchir après un court délai
                    ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
                except Exception as e:
                    ui.notify(f'Erreur: {e}', type='negative')
            
            with ui.row().classes('w-full justify-end gap-2 mt-4'):
                ui.button('Annuler', on_click=dialog.close).props('flat')
                ui.button('Supprimer', on_click=confirm).props('color=red')
        
        dialog.open()
    
    def page_nouveau(self):
        """Page nouveau message"""
        with ui.column().classes('w-full gap-4 p-6'):
            ui.label('✉️ Nouveau Messages').classes('text-3xl font-bold')
            ui.separator()
            
            with ui.card().classes('w-full p-6'):
                ui.label('Créer un nouveau message').classes('text-lg')
                ui.label('Composez et planifiez vos messages Telegram.').classes('text-gray-600')
    
    def page_envoi(self):
        """Page envois en cours"""
        with ui.column().classes('w-full gap-4 p-6'):
            ui.label('📤 Envoi en cours').classes('text-3xl font-bold')
            ui.separator()
            
            with ui.card().classes('w-full p-6'):
                ui.label('Messages en cours d\'envoi').classes('text-lg')
                ui.label('Aucun envoi en cours pour le moment.').classes('text-gray-600')
    
    def page_programme(self):
        """Page messages programmés"""
        with ui.column().classes('w-full gap-4 p-6'):
            ui.label('📅 Messages Programmé').classes('text-3xl font-bold')
            ui.separator()
            
            with ui.card().classes('w-full p-6'):
                ui.label('Vos messages programmés').classes('text-lg')
                ui.label('Aucun message programmé pour le moment.').classes('text-gray-600')


def main():
    """Point d'entrée principal de l'application"""
    
    app = AutoTeleApp()
    
    @ui.page('/')
    def index():
        """Page d'accueil avec menu latéral"""
        with ui.row().classes('w-full h-screen').style('margin: 0; padding: 0;'):
            # Menu latéral
            app.create_sidebar()
            
            # Zone de contenu
            app.content_area = ui.column().classes('flex-1 overflow-auto')
            
            # Charger la page par défaut
            app.show_page('comptes')
            
            # Charger les sessions existantes après que l'UI soit prête
            ui.timer(0.1, lambda: asyncio.create_task(app.load_existing_sessions()), once=True)
    
    # Lancer l'application en mode desktop
    ui.run(
        title='AutoTele - Planificateur Telegram',
        host='127.0.0.1',
        port=8080,
        reload=False,
        show=False,
        native=True,
        window_size=(1400, 900),
        dark=False,
    )


if __name__ == '__main__':
    main()
