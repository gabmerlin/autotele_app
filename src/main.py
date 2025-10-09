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
from pages.accounts_page import AccountsPage
from pages.new_message_page import NewMessagePage
from pages.scheduled_messages_page import ScheduledMessagesPage

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
        
        # Pages refactorisées
        self.accounts_page = AccountsPage(self.telegram_manager, self)
        self.new_message_page = NewMessagePage(self.telegram_manager)
        self.scheduled_messages_page = ScheduledMessagesPage(self.telegram_manager)
    
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
        with ui.column().classes('w-64 h-screen app-sidebar p-6 gap-3'):
            # Logo/Titre
            with ui.row().classes('items-center gap-3 mb-6'):
                ui.label('▸').classes('text-3xl').style('color: #60a5fa;')
                ui.label('AutoTele').classes('text-2xl sidebar-title')
            
            ui.separator().style('background: rgba(255, 255, 255, 0.1); height: 1px; border: none;')
            
            # Menu items avec icônes professionnelles
            with ui.column().classes('gap-2 mt-4'):
                ui.button('⚙  Comptes', on_click=lambda: self.show_page('comptes')).props('flat align=left').classes('w-full sidebar-btn text-white')
                ui.button('✎  Nouveau Message', on_click=lambda: self.show_page('nouveau')).props('flat align=left').classes('w-full sidebar-btn text-white')
                ui.button('⏱  Messages Programmés', on_click=lambda: self.show_page('programme')).props('flat align=left').classes('w-full sidebar-btn text-white')
            
            ui.space()
            
            # Footer
            with ui.column().classes('gap-1'):
                ui.label('Version 2.0').classes('text-xs').style('color: rgba(255, 255, 255, 0.5);')
                ui.label('Pro Edition').classes('text-xs font-semibold').style('color: #60a5fa;')
    
    def show_page(self, page_name: str):
        """Affiche une page spécifique"""
        self.current_page = page_name
        
        if self.content_area:
            self.content_area.clear()
            
            with self.content_area:
                if page_name == 'comptes':
                    self.page_comptes()
                elif page_name == 'nouveau':
                    # Utiliser la page refactorisée
                    self.new_message_page.render()
                elif page_name == 'programme':
                    # Utiliser la page refactorisée
                    self.scheduled_messages_page.render()
            
            # Forcer le rafraîchissement de NiceGUI
            self.content_area.update()
    
    def page_comptes(self):
        """Page de gestion des comptes Telegram"""
        with ui.column().classes('w-full gap-6 p-8'):
            # En-tête avec style professionnel
            with ui.row().classes('items-center gap-3 mb-2'):
                ui.label('⚙').classes('text-4xl').style('color: var(--primary);')
                ui.label('Comptes Telegram').classes('text-3xl font-bold').style('color: var(--text-primary);')
            ui.label('Gérez vos comptes Telegram connectés').classes('text-sm').style('color: var(--text-secondary);')
            
            ui.separator().style('background: var(--border); height: 1px; border: none; margin: 16px 0;')
            
            # Liste des comptes
            accounts = self.telegram_manager.list_accounts()
            
            if accounts:
                with ui.column().classes('gap-3'):
                    for account in accounts:
                        is_connected = account.get('is_connected', False)
                        with ui.card().classes('w-full p-5 card-modern'):
                            with ui.row().classes('w-full items-center gap-4'):
                                # Status badge moderne
                                status_class = 'status-online' if is_connected else 'status-offline'
                                ui.html(f'<span class="status-badge {status_class}"></span>', sanitize=False)
                                
                                # Infos compte
                                with ui.column().classes('gap-1 flex-1'):
                                    ui.label(account.get('account_name', 'Sans nom')).classes('text-lg font-semibold').style('color: var(--text-primary);')
                                    ui.label(account.get('phone', 'N/A')).classes('text-sm').style('color: var(--text-secondary);')
                                
                                # Boutons d'action
                                with ui.row().classes('gap-2'):
                                    if not is_connected:
                                        ui.button('↻ Reconnecter', on_click=lambda a=account: self.reconnect_account(a)).props('flat dense').style('color: var(--warning);')
                                    ui.button('⚙ Paramètres', on_click=lambda a=account: self.account_settings_dialog(a)).props('flat dense').style('color: var(--accent);')
                                    ui.button('✕ Supprimer', on_click=lambda a=account: self.delete_account(a)).props('flat dense').style('color: var(--danger);')
            else:
                with ui.card().classes('w-full p-8 card-modern text-center'):
                    ui.label('●').classes('text-5xl mb-3').style('color: var(--secondary); opacity: 0.3;')
                    ui.label('Aucun compte configuré').classes('text-lg font-semibold mb-2').style('color: var(--text-secondary);')
                    ui.label('Ajoutez votre premier compte Telegram pour commencer').classes('text-sm').style('color: var(--text-secondary); opacity: 0.7;')
            
            # Bouton ajouter moderne
            ui.button('＋ Ajouter un compte', on_click=self.add_account_dialog).props('size=lg').classes('w-full btn-primary mt-4').style('padding: 16px; font-size: 16px;')
            
            # Bouton de secours pour le popup de vérification
            if self.temp_phone and self.temp_session_id:
                ui.button('🔐 Ouvrir popup de vérification', on_click=self.create_verification_dialog).props('color=accent size=lg').classes('w-full mt-2')
    
    async def add_account_dialog(self):
        """Dialogue pour ajouter un compte"""
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6 card-modern'):
            ui.label('＋ Ajouter un compte').classes('text-2xl font-bold mb-4').style('color: var(--text-primary);')
            
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
                            
                            with verification_dialog, ui.card().classes('w-96 p-6 card-modern'):
                                ui.label('✓ Vérification').classes('text-2xl font-bold mb-4').style('color: var(--text-primary);')
                                
                                with ui.column().classes('w-full gap-4'):
                                    ui.label(f'Compte: {phone}').classes('text-gray-600')
                                    
                                    ui.label('Code de vérification').classes('font-medium')
                                    code_input = ui.input(placeholder='12345').classes('w-full')
                                    
                                    ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                                    password_input = ui.input(placeholder='Laissez vide si pas de 2FA', password=True, password_toggle_button=True).classes('w-full')
                                    
                                    with ui.card().classes('p-3').style('background: #fef3c7; border-left: 3px solid var(--warning);'):
                                        ui.label('⚠ Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram').classes('text-sm').style('color: #92400e;')
                                    
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
                                        ui.button('Annuler', on_click=verification_dialog.close).props('flat').style('color: var(--secondary);')
                                        ui.button('✓ Vérifier', on_click=verify).classes('btn-primary')
                            
                            verification_dialog.open()
                        else:
                            ui.notify(f'Erreur: {message}', type='negative')
                    
                    except Exception as e:
                        logger.error(f"Erreur ajout compte: {e}")
                        ui.notify(f'Erreur: {e}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat').style('color: var(--secondary);')
                    ui.button('→ Continuer', on_click=submit).classes('btn-primary')
        
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
        
        with dialog, ui.card().classes('w-96 p-6 card-modern'):
            ui.label('✓ Vérification').classes('text-2xl font-bold mb-4').style('color: var(--text-primary);')
            
            with ui.column().classes('w-full gap-4'):
                ui.label(f'Compte: {self.temp_phone}').classes('text-gray-600')
                
                ui.label('Code de vérification').classes('font-medium')
                code_input = ui.input(placeholder='12345').classes('w-full')
                
                ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                password_input = ui.input(placeholder='Laissez vide si pas de 2FA', password=True, password_toggle_button=True).classes('w-full')
                
                with ui.card().classes('p-3').style('background: #fef3c7; border-left: 3px solid var(--warning);'):
                    ui.label('⚠ Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram').classes('text-sm').style('color: #92400e;')
                
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
                    ui.button('Annuler', on_click=dialog.close).props('flat').style('color: var(--secondary);')
                    ui.button('✓ Vérifier', on_click=verify).classes('btn-primary')
        
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
                
                with verification_dialog, ui.card().classes('w-96 p-6 card-modern'):
                    ui.label('↻ Reconnexion').classes('text-2xl font-bold mb-4').style('color: var(--text-primary);')
                    
                    with ui.column().classes('w-full gap-4'):
                        ui.label(f'Compte: {phone}').classes('text-gray-600')
                        
                        ui.label('Code de vérification').classes('font-medium')
                        code_input = ui.input(placeholder='12345').classes('w-full')
                        
                        ui.label('Mot de passe 2FA (si activé)').classes('font-medium')
                        password_input = ui.input(placeholder='Laissez vide si pas de 2FA', password=True, password_toggle_button=True).classes('w-full')
                        
                        with ui.card().classes('p-3').style('background: #fef3c7; border-left: 3px solid var(--warning);'):
                            ui.label('⚠ Le mot de passe 2FA n\'est requis que si vous l\'avez activé sur Telegram').classes('text-sm').style('color: #92400e;')
                        
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
                            ui.button('Annuler', on_click=verification_dialog.close).props('flat').style('color: var(--secondary);')
                            ui.button('✓ Vérifier', on_click=verify).classes('btn-primary')
                
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
        
        with ui.dialog() as dialog, ui.card().classes('w-96 p-6 card-modern'):
            ui.label('⚠ Supprimer le compte ?').classes('text-xl font-bold mb-4').style('color: var(--danger);')
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
                ui.button('Annuler', on_click=dialog.close).props('flat').style('color: var(--secondary);')
                ui.button('✕ Supprimer', on_click=confirm).props('color=red')
        
        dialog.open()
    
    async def account_settings_dialog(self, account):
        """Dialogue des paramètres du compte"""
        from core.session_manager import SessionManager
        session_manager = SessionManager()
        session_id = account.get('session_id')
        
        # Charger les paramètres actuels
        settings = session_manager.get_account_settings(session_id)
        
        with ui.dialog() as dialog, ui.card().classes('w-[600px] p-6 card-modern'):
            ui.label('⚙ Paramètres du compte').classes('text-2xl font-bold mb-4').style('color: var(--text-primary);')
            ui.label(f"{account.get('account_name')} ({account.get('phone')})").classes('text-gray-600 mb-4')
            
            with ui.column().classes('w-full gap-4'):
                # Nom du compte
                ui.label('Nom du compte').classes('font-medium')
                name_input = ui.input(value=account.get('account_name', '')).classes('w-full')
                
                # Message par défaut
                ui.label('Message par défaut').classes('font-medium')
                message_input = ui.textarea(value=settings.get('default_message', '')).classes('w-full').props('rows=4')
                
                # Horaires prédéfinis
                ui.label('Horaires prédéfinis').classes('font-medium')
                
                # Liste des horaires (mutable)
                schedules_list = settings.get('default_schedules', []).copy()
                
                # Container pour la liste
                schedules_container = ui.column().classes('w-full gap-2')
                
                def render_schedules():
                    """Affiche la liste des horaires"""
                    schedules_container.clear()
                    with schedules_container:
                        if schedules_list:
                            for schedule in sorted(schedules_list):
                                with ui.card().classes('w-full p-2 bg-gray-50'):
                                    with ui.row().classes('w-full items-center gap-2'):
                                        ui.label(f'🕐 {schedule}').classes('flex-1')
                                        
                                        def make_delete_handler(s):
                                            def delete():
                                                schedules_list.remove(s)
                                                render_schedules()
                                            return delete
                                        
                                        ui.button('🗑️', on_click=make_delete_handler(schedule)).props('flat dense color=red size=sm')
                        else:
                            ui.label('Aucun horaire prédéfini').classes('text-gray-500 text-sm')
                
                # Ajouter un horaire
                with ui.row().classes('w-full gap-2 items-end'):
                    with ui.column().classes('flex-1'):
                        ui.label('Ajouter un horaire (HH:MM)').classes('text-sm text-gray-600')
                        time_input = ui.input(placeholder='09:00').classes('w-full')
                    
                    def add_time():
                        time_str = time_input.value.strip()
                        if not time_str:
                            ui.notify('Veuillez entrer une heure', type='warning')
                            return
                        
                        # Valider le format HH:MM
                        if ':' not in time_str or len(time_str.split(':')) != 2:
                            ui.notify('Format invalide (utilisez HH:MM)', type='warning')
                            return
                        
                        try:
                            h, m = time_str.split(':')
                            h, m = int(h), int(m)
                            if not (0 <= h <= 23) or not (0 <= m <= 59):
                                raise ValueError()
                            
                            formatted = f'{h:02d}:{m:02d}'
                            
                            if formatted in schedules_list:
                                ui.notify('Cet horaire existe déjà', type='warning')
                                return
                            
                            schedules_list.append(formatted)
                            schedules_list.sort()
                            time_input.value = ''
                            render_schedules()
                            ui.notify(f'✅ {formatted} ajouté', type='positive')
                            
                        except:
                            ui.notify('Heure invalide (ex: 09:00)', type='warning')
                    
                    ui.button('➕ Ajouter', on_click=add_time).props('color=primary')
                
                # Afficher la liste initiale
                render_schedules()
                
                with ui.card().classes('bg-blue-50 p-3 mt-2'):
                    ui.label('💡 Les horaires prédéfinis seront automatiquement proposés lors de la création de messages').classes('text-sm text-blue-800')
                
                async def save():
                    try:
                        # Sauvegarder le nom
                        new_name = name_input.value.strip()
                        if new_name:
                            session_manager.update_account_name(session_id, new_name)
                        
                        # Sauvegarder les paramètres
                        new_message = message_input.value.strip()
                        
                        # Utiliser la liste des horaires
                        session_manager.update_account_settings(
                            session_id,
                            default_message=new_message,
                            default_schedules=schedules_list
                        )
                        
                        dialog.close()
                        ui.notify('✅ Paramètres sauvegardés !', type='positive')
                        # Rafraîchir la page
                        ui.timer(0.2, lambda: self.show_page('comptes'), once=True)
                        
                    except Exception as e:
                        logger.error(f"Erreur sauvegarde paramètres: {e}")
                        ui.notify(f'Erreur: {e}', type='negative')
                
                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Annuler', on_click=dialog.close).props('flat').style('color: var(--secondary);')
                    ui.button('💾 Sauvegarder', on_click=save).classes('btn-primary')
        
        dialog.open()
    


def main():
    """Point d'entrée principal de l'application"""
    
    app = AutoTeleApp()
    
    @ui.page('/')
    def index():
        """Page d'accueil avec menu latéral"""
        # Ajouter les styles personnalisés globaux
        ui.add_head_html('''
            <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
            <style>
                * {
                    font-family: 'Poppins', -apple-system, BlinkMacSystemFont, sans-serif !important;
                }
                :root {
                    --primary: #1e3a8a;
                    --primary-light: #3b82f6;
                    --secondary: #64748b;
                    --accent: #0ea5e9;
                    --success: #10b981;
                    --warning: #f59e0b;
                    --danger: #ef4444;
                    --bg-primary: #ffffff;
                    --bg-secondary: #f8fafc;
                    --text-primary: #0f172a;
                    --text-secondary: #64748b;
                    --border: #e2e8f0;
                }
                .app-sidebar {
                    background: linear-gradient(180deg, #1e3a8a 0%, #1e40af 100%);
                    box-shadow: 4px 0 12px rgba(0, 0, 0, 0.08);
                }
                .sidebar-title {
                    color: #ffffff;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }
                .sidebar-btn {
                    transition: all 0.2s ease;
                    border-radius: 8px;
                    font-weight: 500;
                }
                .sidebar-btn:hover {
                    background: rgba(255, 255, 255, 0.1);
                    transform: translateX(4px);
                }
                .card-modern {
                    border-radius: 12px;
                    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
                    border: 1px solid var(--border);
                    transition: all 0.2s ease;
                }
                .card-modern:hover {
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                }
                .btn-primary {
                    background: var(--primary);
                    color: white;
                    font-weight: 600;
                    border-radius: 8px;
                    transition: all 0.2s ease;
                }
                .btn-primary:hover {
                    background: var(--primary-light);
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(30, 58, 138, 0.2);
                }
                .status-badge {
                    width: 8px;
                    height: 8px;
                    border-radius: 50%;
                    display: inline-block;
                }
                .status-online { background: var(--success); }
                .status-offline { background: var(--danger); }
            </style>
        ''')
        
        with ui.row().classes('w-full h-screen').style('margin: 0; padding: 0; background: var(--bg-secondary);'):
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
