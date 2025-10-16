"""
Page de messagerie en temps réel - Version optimisée avec SQLite.
Chargement instantané comme Telegram officiel.
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Set
from nicegui import ui

from core.telegram.manager import TelegramManager
from services.messaging_service import get_messaging_service
from services.realtime_updates import get_realtime_updates
from services.user_search_service import UserSearchService
from ui.components.svg_icons import svg
from utils.logger import get_logger
from utils.notification_manager import notify
from utils.constants import ICON_MESSAGE
from utils.country_flags import get_country_flag_from_phone

logger = get_logger()


class MessagingPage:
    """Page de messagerie Telegram optimisée avec SQLite."""
    
    def __init__(self, telegram_manager: TelegramManager):
        """
        Initialise la page de messagerie.
        
        Args:
            telegram_manager: Gestionnaire de comptes Telegram
        """
        self.telegram_manager = telegram_manager
        self.messaging_service = get_messaging_service()
        self.realtime_updates = get_realtime_updates()
        
        # État de l'application
        self.state = {
            'selected_accounts': [],
            'all_conversations': [],
            'filtered_conversations': [],
            'selected_conversation': None,
            'messages': [],
            'show_groups': False,
            'show_unread_only': False,  # Nouveau filtre pour messages non lus
            'username_search_result': None,
            'is_searching_username': False,
        }
        
        # Conteneurs UI
        self.accounts_selector_container: Optional[ui.column] = None
        self.conversations_container: Optional[ui.column] = None
        self.messages_container: Optional[ui.column] = None
        self.conversation_header: Optional[ui.row] = None
        self.message_input: Optional[ui.textarea] = None
        self.search_input: Optional[ui.input] = None
        
        # Cache pour optimisation
        self._photo_exists_cache: Dict[str, bool] = {}
        self._conversation_items: Dict[str, any] = {}  # Mapping conversation_id -> UI element
        
        # Flags
        self._is_loading = False
        self._current_search_text = ''
    
    def render(self) -> None:
        """Rend la page de messagerie."""
        with ui.column().classes('w-full h-full gap-0 p-0').style(
            'height: calc(100vh - 0px); overflow: hidden;'
        ):
            # En-tête
            self._render_header()
            
            # Layout principal
            with ui.row().classes('w-full flex-1 gap-0').style(
                'height: calc(100vh - 120px); overflow: hidden;'
            ):
                # Colonne gauche : Conversations
                self._render_conversations_list()
                
                # Colonne droite : Messages
                self._render_messages_area()
        
        # Charger immédiatement depuis SQLite avec le contexte UI
        ui.timer(0.1, lambda: asyncio.create_task(self._load_conversations_instant()), once=True)
        
        # Setup handlers temps réel
        self._setup_realtime_handlers()
    
    async def _load_conversations_instant(self):
        """Charge les conversations instantanément depuis SQLite."""
        try:
            if not self.state['selected_accounts']:
                # Sélectionner tous les comptes connectés par défaut
                accounts = self.telegram_manager.list_accounts()
                connected = [acc for acc in accounts if acc.get('is_connected', False)]
                self.state['selected_accounts'] = [acc['session_id'] for acc in connected]
                self._render_accounts_selector()
            
            if not self.state['selected_accounts']:
                return
            
            # 1. Charger depuis SQLite selon la préférence show_groups
            conversations = await self.messaging_service.get_conversations_fast(
                self.state['selected_accounts'],
                include_groups=self.state['show_groups'],  # Respecter le choix de l'utilisateur
                limit=999,  # Charger TOUTES les conversations
                telegram_manager=self.telegram_manager
            )
            
            # 2. SI VIDE (premier lancement), forcer une sync immédiate
            if not conversations:
                logger.info("Base de données vide - Synchronisation initiale avec Telegram...")
                conversations = await self.messaging_service.get_conversations_fast(
                    self.state['selected_accounts'],
                    include_groups=self.state['show_groups'],  # Respecter le choix
                    limit=999,  # Charger TOUTES les conversations
                    force_sync=True,  # Force la sync
                    telegram_manager=self.telegram_manager  # IMPORTANT: Passer le manager
                )
            
            # 3. Fusionner avec les noms de comptes
            self._merge_and_display_conversations(conversations)
            
            # 4. Télécharger les photos de profil en arrière-plan
            if conversations:
                asyncio.create_task(self._download_profile_photos_background(conversations[:50]))
            
        except Exception as e:
            logger.error(f"Erreur chargement conversations: {e}")
    
    async def _download_photos_background_old(self):
        """Méthode désactivée temporairement."""
        pass
    
    async def _download_photos_background(self):
        """Version simplifiée du téléchargement de photos."""
        pass  # Désactivé temporairement
    
    def _on_photo_downloaded(self, entity_id: int, photo_path: str):
        """
        Callback appelé quand une photo est téléchargée.
        
        Args:
            entity_id: ID de l'entité
            photo_path: Chemin de la photo
        """
        try:
            # Mettre à jour silencieusement dans les données
            for conv in self.state['all_conversations']:
                if conv['entity_id'] == entity_id:
                    conv['profile_photo'] = photo_path
                    conv['has_photo'] = True
                    # Mettre à jour le cache
                    self._photo_exists_cache[photo_path] = True
                    break
            
            # Si c'est la conversation sélectionnée, mettre à jour l'en-tête seulement
            if self.state['selected_conversation'] and self.state['selected_conversation']['entity_id'] == entity_id:
                self.state['selected_conversation']['profile_photo'] = photo_path
                self.state['selected_conversation']['has_photo'] = True
                self._update_conversation_header()
            
            # NE PAS re-render toute la liste (évite le flickering)
            # Les photos apparaîtront au prochain rafraîchissement naturel
                
        except Exception as e:
            logger.error(f"Erreur callback photo: {e}")
    
    def _setup_realtime_handlers(self):
        """Configure les handlers pour updates en temps réel."""
        # Register UI callbacks
        self.realtime_updates.register_ui_callback('new_message', self._on_new_message)
        self.realtime_updates.register_ui_callback('messages_read', self._on_messages_read)
        
        # Setup handlers pour chaque compte connecté
        for session_id in self.state['selected_accounts']:
            account = self.telegram_manager.get_account(session_id)
            if account and account.is_connected:
                self.realtime_updates.setup_handlers(account)
    
    def _on_new_message(self, msg_dict: Dict, chat_id: int):
        """
        Callback pour nouveau message reçu.
        
        Args:
            msg_dict: Dictionnaire du message
            chat_id: ID du chat
        """
        try:
            # Si c'est la conversation actuelle, ajouter le message
            if self.state['selected_conversation'] and self.state['selected_conversation']['entity_id'] == chat_id:
                self.state['messages'].append(msg_dict)
                # Ne pas update display depuis callback (problème de slot)
                # L'UI sera mise à jour au prochain rafraîchissement
            
            # Mettre à jour la liste des conversations silencieusement
            self._reload_conversations_silent()
        
        except Exception as e:
            logger.error(f"Erreur traitement nouveau message UI: {e}")
    
    def _on_messages_read(self, chat_id: int):
        """
        Callback pour messages lus.
        
        Args:
            chat_id: ID du chat
        """
        try:
            # Mettre à jour unread_count dans la liste
            for conv in self.state['all_conversations']:
                if conv['entity_id'] == chat_id:
                    conv['unread_count'] = 0
                    break
            
            self._update_conversations_list()
        
        except Exception as e:
            logger.error(f"Erreur traitement messages lus UI: {e}")
    
    def _reload_conversations_silent(self):
        """Recharge les conversations sans notification."""
        asyncio.create_task(self._load_conversations_instant())
    
    def _render_header(self) -> None:
        """Rend l'en-tête avec sélecteur de comptes."""
        with ui.column().classes('w-full p-6 gap-4').style(
            'background: var(--bg-primary); border-bottom: 1px solid var(--border);'
        ):
            # Titre
            with ui.row().classes('items-center gap-3'):
                ui.html(svg('chat', 40, 'var(--primary)'))
                ui.label('Messagerie').classes('text-3xl font-bold').style(
                    'color: var(--text-primary);'
                )
                
                # Indicateur de performance
                ui.label('⚡ Chargement instantané (SQLite)').classes('text-sm px-3 py-1 rounded-full').style(
                    'background: #10b981; color: white; font-weight: bold;'
                )
            
            # Sélecteur de comptes
            with ui.row().classes('items-center gap-3 w-full'):
                ui.label('Comptes:').classes('font-semibold').style('color: var(--text-primary);')
                
                self.accounts_selector_container = ui.row().classes('gap-2 flex-wrap flex-1')
                self._render_accounts_selector()
                
                # Bouton rafraîchir (sync avec Telegram)
                with ui.button(
                    on_click=lambda: asyncio.create_task(self._force_sync())
                ).props('outline dense').classes('text-blue-500'):
                    with ui.row().classes('items-center gap-1'):
                        ui.html(svg('sync', 18, '#3b82f6'))
                        ui.label('Synchroniser')
    
    async def _force_sync(self):
        """Force la synchronisation avec Telegram."""
        try:
            notify('Synchronisation avec Telegram...', type='info')
            
            conversations = await self.messaging_service.get_conversations_fast(
                self.state['selected_accounts'],
                include_groups=self.state['show_groups'],
                limit=999,  # Charger TOUTES
                force_sync=True,
                telegram_manager=self.telegram_manager
            )
            
            self._merge_and_display_conversations(conversations)
            
            notify('Synchronisation terminée', type='positive')
        except Exception as e:
            logger.error(f"Erreur sync: {e}")
            notify(f'Erreur synchronisation: {e}', type='negative')
    
    def _render_accounts_selector(self) -> None:
        """Rend le sélecteur de comptes."""
        if not self.accounts_selector_container:
            return
        
        self.accounts_selector_container.clear()
        
        accounts = self.telegram_manager.list_accounts()
        connected_accounts = [acc for acc in accounts if acc.get('is_connected', False)]
        
        # Par défaut, tous les comptes sont sélectionnés
        if not self.state['selected_accounts']:
            self.state['selected_accounts'] = [acc['session_id'] for acc in connected_accounts]
        
        with self.accounts_selector_container:
            if not connected_accounts:
                ui.label('Aucun compte connecté').classes('text-sm text-red-500')
            else:
                for account in connected_accounts:
                    session_id = account['session_id']
                    is_selected = session_id in self.state['selected_accounts']
                    
                    def make_toggle(sid: str):
                        async def toggle():
                            if sid in self.state['selected_accounts']:
                                self.state['selected_accounts'].remove(sid)
                            else:
                                self.state['selected_accounts'].append(sid)
                            
                            self._render_accounts_selector()
                            await self._load_conversations_instant()
                        return toggle
                    
                    if is_selected:
                        style = (
                            'background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); '
                            'color: white; font-weight: bold; '
                            'border: 2px solid #1d4ed8; '
                            'box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3); '
                            'transform: scale(1.05);'
                        )
                        icon = '✓ '
                    else:
                        style = (
                            'background: #f3f4f6; color: #6b7280; '
                            'font-weight: normal; border: 2px solid #e5e7eb; '
                            'opacity: 0.7;'
                        )
                        icon = ''
                    
                    ui.button(
                        f"{icon}{account['account_name']}",
                        on_click=make_toggle(session_id)
                    ).props('dense').style(style).classes('transition-all duration-200')
    
    def _render_conversations_list(self) -> None:
        """Rend la liste des conversations."""
        with ui.column().classes('gap-0').style(
            'width: 380px; height: 100%; background: var(--bg-primary); '
            'border-right: 1px solid var(--border); overflow: hidden;'
        ):
            # Barre de recherche
            with ui.column().classes('w-full p-4 gap-2').style('border-bottom: 1px solid var(--border);'):
                self.search_input = ui.input(
                    placeholder='Rechercher ou @username...',
                    on_change=self._on_search_conversations
                ).classes('w-full').props('dense outlined')
                
                # Checkbox groupes
                async def toggle_groups(e):
                    self.state['show_groups'] = e.value
                    
                    # Recharger les conversations avec le nouveau filtre
                    conversations = await self.messaging_service.get_conversations_fast(
                        self.state['selected_accounts'],
                        include_groups=self.state['show_groups'],
                        limit=999,  # Charger TOUTES
                        force_sync=True,  # Force sync pour charger les groupes si besoin
                        telegram_manager=self.telegram_manager
                    )
                    
                    self._merge_and_display_conversations(conversations)
                    
                    # Réappliquer les filtres de recherche si nécessaire
                    if self._current_search_text:
                        self._apply_filters()
                    
                    # Ne pas retélécharger les photos à chaque toggle
                
                ui.checkbox(
                    'Afficher les groupes',
                    value=self.state['show_groups'],
                    on_change=toggle_groups
                ).classes('text-sm').style('color: var(--text-primary);')
            
                # Checkbox messages non lus uniquement
                def toggle_unread_only(e):
                    self.state['show_unread_only'] = e.value
                    # Réappliquer les filtres
                    self._apply_filters()
                
                ui.checkbox(
                    'Messages non lus seulement',
                    value=self.state['show_unread_only'],
                    on_change=toggle_unread_only
                ).classes('text-sm').style('color: var(--text-primary);')
            
            # Liste
            self.conversations_container = ui.column().classes('w-full gap-0 flex-1').style(
                'overflow-y: auto; overflow-x: hidden;'
            )
            self._update_conversations_list()
    
    def _render_messages_area(self) -> None:
        """Rend la zone des messages."""
        with ui.column().classes('flex-1 gap-0').style(
            'height: 100%; background: var(--bg-secondary); overflow: hidden;'
        ):
            # En-tête avec drapeau
            self.conversation_header = ui.row().classes('w-full p-4 gap-3 items-center').style(
                'background: var(--bg-primary); border-bottom: 1px solid var(--border); min-height: 70px;'
            )
            self._update_conversation_header()
            
            # Messages
            self.messages_container = ui.column().classes('flex-1 w-full p-4 gap-3 messages-scroll-container').style(
                'overflow-y: auto; overflow-x: hidden; background: #f5f5f5;'
            )
            self._update_messages_display()
            
            # Saisie
            self._render_message_input()
    
    def _render_message_input(self) -> None:
        """Rend la zone de saisie."""
        with ui.row().classes('w-full p-4 gap-2 items-end').style(
            'background: var(--bg-primary); border-top: 1px solid var(--border);'
        ):
            self.message_input = ui.textarea(
                placeholder='Écrivez votre message...'
            ).classes('flex-1').props('outlined dense rows=2')
            
            self.message_input.on('keydown.enter', self._handle_keydown)
            
            async def send_message():
                if not self.state['selected_conversation']:
                    notify('Sélectionnez une conversation', type='warning')
                    return
                
                if not self.message_input.value or not self.message_input.value.strip():
                    notify('Le message ne peut pas être vide', type='warning')
                    return
                
                message = self.message_input.value.strip()
                conv = self.state['selected_conversation']
                account_session_id = conv.get('session_id')
                
                if not account_session_id:
                    notify('Impossible de déterminer le compte', type='negative')
                    return
                
                account = self.telegram_manager.get_account(account_session_id)
                if not account or not account.is_connected:
                    notify('Compte non connecté', type='negative')
                    return
                
                # Envoyer via le service
                success = await self.messaging_service.send_message(
                    account,
                    conv['entity_id'],
                    message
                )
                
                if success:
                    notify('Message envoyé', type='positive')
                    self.message_input.value = ''
                    
                    # Recharger les messages
                    await self._load_messages(conv['entity_id'], account_session_id)
                else:
                    notify('Erreur lors de l\'envoi', type='negative')
            
            with ui.column().classes('gap-1 items-end'):
                with ui.button(on_click=send_message).props('color=primary').classes('px-6'):
                    with ui.row().classes('items-center gap-1'):
                        ui.html(svg('send', 18, 'white'))
                        ui.label('Envoyer')
                
                ui.label('Entrée = Envoyer • Shift+Entrée = Nouvelle ligne').classes('text-xs').style(
                    'color: var(--text-secondary); opacity: 0.7;'
                )
    
    def _update_conversation_header(self) -> None:
        """Met à jour l'en-tête avec drapeau du pays."""
        if not self.conversation_header:
            return
        
        self.conversation_header.clear()
        
        with self.conversation_header:
            if self.state['selected_conversation']:
                conv = self.state['selected_conversation']
                
                # Avatar
                photo_path = conv.get('profile_photo')
                if photo_path and self._photo_exists(photo_path):
                    ui.image(photo_path).style('width: 50px; height: 50px; border-radius: 50%; object-fit: cover;')
                else:
                    icon_name = 'person' if conv['type'] == 'user' else 'group' if conv['type'] == 'group' else 'campaign'
                    ui.html(svg(icon_name, 40, 'var(--text-secondary)'))
                
                # Infos
                with ui.column().classes('gap-1 flex-1'):
                    ui.label(conv['title']).classes('text-xl font-bold').style('color: var(--text-primary);')
                    display_name = conv.get('account_name', 'Inconnu')
                    ui.label(f"Compte: {display_name}").classes('text-sm').style('color: var(--text-secondary);')
                
                # DRAPEAU DU PAYS (à droite)
                if conv['type'] == 'user':
                    phone = conv.get('phone')
                    if phone:
                        flag = get_country_flag_from_phone(phone)
                        if flag:
                            with ui.column().classes('items-center gap-0'):
                                ui.label(flag).classes('text-4xl')
                                # Afficher aussi le code pays pour debug
                                from utils.country_flags import get_country_code_from_phone
                                country_code = get_country_code_from_phone(phone)
                                if country_code:
                                    ui.label(country_code).classes('text-xs').style('color: var(--text-secondary);')
            else:
                        # Pas de numéro disponible
                        ui.label('🌐').classes('text-3xl').style('opacity: 0.3;').props('title="Numéro non disponible"')
            else:
                ui.label('Sélectionnez une conversation').classes('text-lg').style('color: var(--text-secondary);')
    
    def _update_conversations_list(self) -> None:
        """Met à jour la liste des conversations."""
        if not self.conversations_container:
            return
        
        try:
        self.conversations_container.clear()
        except Exception as e:
            # Le client UI peut être fermé, ignorer silencieusement
            logger.debug(f"Impossible de clear conversations_container: {e}")
            return
        
        conversations = self.state.get('filtered_conversations') or self.state.get('all_conversations', [])
        
        try:
        with self.conversations_container:
            if not conversations:
                with ui.column().classes('w-full p-8 items-center gap-3'):
                    ui.html(svg('mail_outline', 60, 'var(--text-secondary)'))
                    ui.label('Aucune conversation').classes('text-lg').style('color: var(--text-secondary);')
                else:
                    for conv in conversations:
                        self._render_conversation_item(conv)
        except Exception as e:
            # Le client UI peut être fermé, ignorer silencieusement
            logger.debug(f"Impossible de render conversations: {e}")
    
    def _render_conversation_item(self, conv: Dict) -> None:
        """Rend un élément de conversation."""
        conv_unique_id = f"{conv.get('session_id')}_{conv['entity_id']}"
        selected_unique_id = None
        if self.state['selected_conversation']:
            selected_unique_id = f"{self.state['selected_conversation'].get('session_id')}_{self.state['selected_conversation']['entity_id']}"
        
        is_selected = conv_unique_id == selected_unique_id
        style = 'background: rgba(30, 58, 138, 0.1);' if is_selected else ''
        
        async def select_conversation():
            self.state['selected_conversation'] = conv
            self._update_conversation_header()
            await self._load_messages(conv['entity_id'], conv.get('session_id'))
        
        with ui.card().classes('w-full p-3 cursor-pointer').style(
            f'{style} border: none; border-bottom: 1px solid var(--border); border-radius: 0; '
            'cursor: pointer; transition: background 0.2s;'
        ).on('click', select_conversation):
            with ui.row().classes('w-full items-start gap-3'):
                # Avatar
                photo_path = conv.get('profile_photo')
                if photo_path and self._photo_exists(photo_path):
                    ui.image(photo_path).style('width: 40px; height: 40px; border-radius: 50%; object-fit: cover;')
                        else:
                    icon_name = 'person' if conv['type'] == 'user' else 'group' if conv['type'] == 'group' else 'campaign'
                    ui.html(svg(icon_name, 28, 'var(--text-secondary)'))
                
                # Contenu
                with ui.column().classes('flex-1 gap-1 min-w-0'):
                    with ui.row().classes('w-full items-center gap-2 justify-between'):
                        ui.label(conv['title']).classes('font-bold text-sm').style(
                            'color: var(--text-primary); white-space: nowrap; '
                            'overflow: hidden; text-overflow: ellipsis; max-width: 200px;'
                        )
                        
                        if conv.get('unread_count', 0) > 0:
                            ui.label(str(conv['unread_count'])).classes(
                                'px-2 py-1 rounded-full text-xs font-bold bg-blue-500 text-white'
                            )
                    
                    # Dernier message
                    last_msg = conv.get('last_message', '')
                    ui.label(last_msg).classes('text-xs').style(
                        'color: var(--text-secondary); white-space: nowrap; '
                        'overflow: hidden; text-overflow: ellipsis;'
                    )
                    
                    # Date + compte
                    with ui.row().classes('items-center gap-2'):
                        if conv.get('last_message_date'):
                            date_str = self._format_date(conv['last_message_date'])
                            ui.label(date_str).classes('text-xs').style('color: var(--text-secondary);')
                        
                        display_name = conv.get('account_name', 'Inconnu')
                        ui.label(f"• {display_name}").classes('text-xs').style('color: var(--accent);')
    
    def _update_messages_display(self) -> None:
        """Met à jour l'affichage des messages."""
        if not self.messages_container:
            return
        
        self.messages_container.clear()
        
        with self.messages_container:
            messages = self.state.get('messages', [])
            
            if not messages:
                if self.state['selected_conversation']:
                    with ui.column().classes('w-full h-full items-center justify-center gap-3'):
                        ui.html(svg('chat', 60, 'var(--text-secondary)'))
                        ui.label('Aucun message').classes('text-lg').style('color: var(--text-secondary);')
                else:
                    with ui.column().classes('w-full h-full items-center justify-center gap-3'):
                        ui.html(svg('arrow_back', 60, 'var(--text-secondary)'))
                        ui.label('Sélectionnez une conversation').classes('text-lg').style('color: var(--text-secondary);')
            else:
                # Container avec padding et espacement pour les messages
                with ui.column().classes('w-full p-4 gap-2').style('min-height: 100%; display: flex; flex-direction: column;'):
                for msg in messages:
                    self._render_message_bubble(msg)
    
    def _render_message_bubble(self, msg: Dict) -> None:
        """Rend une bulle de message avec la mise en page exacte de Telegram officiel."""
        is_from_me = msg.get('from_me', False)
        sender_name = msg.get('sender_name', '')
        
        # Container principal avec positionnement Telegram
        if is_from_me:
            # Mes messages à droite - clairement séparés
            main_container = ui.row().classes('justify-end mb-3 w-full')
            bubble_style = 'background: #dcf8c6; max-width: 70%; margin-left: auto;'
        else:
            # Messages reçus à gauche avec photo - clairement séparés
            main_container = ui.row().classes('justify-start mb-3 w-full')
            bubble_style = 'background: white; max-width: 70%; margin-right: auto;'
        
        with main_container:
            # Photo de profil (seulement pour messages reçus)
            if not is_from_me:
                profile_photo_container = ui.column().classes('items-center mr-2')
                with profile_photo_container:
                    # Photo de profil en bas (comme Telegram)
                    profile_photo = self._get_profile_photo(msg.get('sender_id'), msg.get('session_id'))
                    if profile_photo:
                        ui.image(profile_photo).classes('w-8 h-8 rounded-full').style('margin-top: 20px;')
                    else:
                        ui.avatar().classes('w-8 h-8').style('margin-top: 20px; background: #ddd;')
            
            # Container de la bulle
            if is_from_me:
                bubble_classes = 'p-3'
                bubble_style_final = f'{bubble_style} border-radius: 18px 18px 4px 18px; border: 1px solid #b8e6b8; box-shadow: 0 1px 2px rgba(0,0,0,0.1); position: relative;'
            else:
                bubble_classes = 'p-3'
                bubble_style_final = f'{bubble_style} border-radius: 4px 18px 18px 18px; border: 1px solid #e0e0e0; box-shadow: 0 1px 2px rgba(0,0,0,0.1); position: relative;'
            
            with ui.card().classes(bubble_classes).style(bubble_style_final):
                # Menu contextuel sur mes messages (clic droit)
                if is_from_me:
                    with ui.context_menu():
                        ui.menu_item('🗑️ Supprimer ce message', on_click=lambda: asyncio.create_task(
                            self._delete_message(msg)
                        ))
                
                # Nom expéditeur + badge vérifié (comme Telegram)
                if not is_from_me and sender_name:
                    with ui.row().classes('items-center gap-1 mb-1'):
                        ui.label(sender_name).classes('text-sm font-medium').style('color: #0088cc;')
                        # Badge vérifié (pour comptes officiels)
                        if self._is_verified_account(sender_name):
                            ui.html('''
                                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                                    <circle cx="8" cy="8" r="7" fill="#0088cc"/>
                                    <path d="M6 8l1.5 1.5L10 6" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                                </svg>
                            ''')
                
                # Texte avec formatage Telegram
            if msg.get('text'):
                    self._render_message_text(msg['text'])
            
                # Média (LAZY LOADING)
            if msg.get('has_media'):
                    self._render_message_media(msg)
                
                # Footer avec réactions, vues et horodatage
                self._render_message_footer(msg)
    
    def _render_message_text(self, text: str) -> None:
        """Rend le texte d'un message avec formatage Telegram (liens, gras, retours à la ligne, etc.)."""
        import re
        
        # Convertir les liens en HTML cliquables
        def linkify_text(content):
            # Pattern pour détecter les URLs
            url_pattern = r'(https?://[^\s<>"{}|\\^`\[\]]+)'
            
            parts = re.split(url_pattern, content)
            result = []
            
            for part in parts:
                if re.match(url_pattern, part):
                    # C'est un lien
                    result.append(f'<a href="{part}" target="_blank" style="color: #0088cc; text-decoration: none;">{part}</a>')
                else:
                    # Texte normal - convertir **gras** en HTML
                    formatted = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', part)
                    # Convertir les retours à la ligne en <br>
                    formatted = formatted.replace('\n', '<br>')
                    result.append(formatted)
            
            return ''.join(result)
        
        formatted_text = linkify_text(text)
        ui.html(formatted_text).classes('text-sm').style('color: #000; line-height: 1.4; word-wrap: break-word; white-space: pre-wrap;')
    
    def _render_message_media(self, msg: Dict) -> None:
        """Rend les médias d'un message avec lazy loading et gestion des différents types."""
                media_type = msg.get('media_type', '')
                media_data = msg.get('media_data')
                media_caption = msg.get('media_caption', '')
                
        # Si déjà téléchargé
        if media_data and self._photo_exists(media_data):
            if media_type == 'MessageMediaPhoto':
                ui.image(media_data).style('max-width: 500px; max-height: 400px; border-radius: 8px; cursor: pointer; margin-top: 4px;')
                if media_caption:
                    ui.label(media_caption).classes('text-sm mt-1').style('color: #666; font-style: italic;')
            else:
                # Autres types de médias
                self._render_media_preview(media_type, media_data, media_caption)
        else:
            # Pas encore téléchargé - Afficher bouton avec type spécifique
            self._render_media_download_button(msg, media_type)
    
    def _render_media_preview(self, media_type: str, media_path: str, caption: str = ''):
        """Affiche un aperçu du média téléchargé."""
        media_style = 'background: #f5f5f5; padding: 12px; border-radius: 8px; margin-top: 4px;'
        
        with ui.row().classes('items-center gap-3').style(media_style):
            # Icône selon le type
            if 'audio' in media_type.lower() or media_path.endswith(('.mp3', '.wav', '.ogg')):
                ui.html(svg('audiotrack', 24, '#0088cc'))
                media_label = '[Audio]'
            elif 'video' in media_type.lower() or media_path.endswith(('.mp4', '.avi', '.mov')):
                ui.html(svg('play_circle', 24, '#0088cc'))
                media_label = '[Vidéo]'
            elif media_path.endswith(('.pdf', '.doc', '.docx')):
                ui.html(svg('description', 24, '#0088cc'))
                media_label = '[Document]'
            else:
                ui.html(svg('attach_file', 24, '#0088cc'))
                media_label = '[Fichier]'
            
            # Informations du fichier
            with ui.column():
                ui.label(media_label).classes('text-sm font-medium').style('color: #0088cc;')
                if caption:
                    ui.label(caption).classes('text-xs').style('color: #666;')
                
                # Nom du fichier
                file_name = os.path.basename(media_path)
                ui.label(file_name).classes('text-xs').style('color: #888;')
    
    def _render_media_download_button(self, msg: Dict, media_type: str):
        """Affiche un bouton de téléchargement avec type spécifique."""
        # Déterminer le type de média
        if 'audio' in media_type.lower():
            icon = 'audiotrack'
            label = 'Télécharger audio'
        elif 'video' in media_type.lower():
            icon = 'play_circle'
            label = 'Télécharger vidéo'
        elif 'document' in media_type.lower():
            icon = 'description'
            label = 'Télécharger document'
        else:
            icon = 'download'
            label = 'Télécharger média'
        
        async def download_media():
            account_session_id = self.state['selected_conversation'].get('session_id')
            account = self.telegram_manager.get_account(account_session_id)
            if account:
                try:
                    notify('Téléchargement...', type='info')
                    path = await self.messaging_service.download_message_media(
                        account,
                        msg.get('chat_id') if 'chat_id' in msg else self.state['selected_conversation']['entity_id'],
                        msg['id'],
                        account_session_id
                    )
                    if path:
                        notify('Téléchargement terminé', type='positive')
                        # Recharger les messages
                        await self._load_messages(
                            self.state['selected_conversation']['entity_id'],
                            account_session_id
                        )
                        else:
                        notify('Échec du téléchargement', type='negative')
                    except Exception as e:
                    logger.error(f"Erreur téléchargement média: {e}")
                    notify('Erreur téléchargement', type='negative')
        
        with ui.button(on_click=download_media).props('outline dense').classes('mt-2'):
            with ui.row().classes('items-center gap-2'):
                ui.html(svg(icon, 18, '#0088cc'))
                ui.label(label).classes('text-sm')
    
    def _render_message_footer(self, msg: Dict) -> None:
        """Rend le footer d'un message (réactions, vues, horodatage) comme Telegram."""
        # Container du footer
        with ui.row().classes('items-center justify-between mt-2').style('font-size: 11px; color: #999;'):
            # Réactions et vues (gauche)
            with ui.row().classes('items-center gap-2'):
                # Réactions (simulées pour l'instant)
                reactions = msg.get('reactions', []) or []
                if reactions:
                        with ui.row().classes('items-center gap-1'):
                        for reaction in reactions:
                            ui.label(reaction['emoji']).classes('text-xs')
                            ui.label(str(reaction['count'])).classes('text-xs')
                
                # Vues (pour groupes)
                views = msg.get('views', 0) or 0
                if views > 0:
                    with ui.row().classes('items-center gap-1'):
                        ui.html('''
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none">
                                <path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z" fill="currentColor"/>
                            </svg>
                        ''')
                        ui.label(str(views)).classes('text-xs')
            
            # Horodatage (droite)
            if msg.get('date'):
                msg_date = msg['date']
                if hasattr(msg_date, 'tzinfo') and msg_date.tzinfo is not None:
                    msg_date = msg_date.replace(tzinfo=None)
                
                date_str = msg_date.strftime('%H:%M')
                edited_marker = ' (modifié)' if msg.get('edited') else ''
                
                ui.label(f'{date_str}{edited_marker}').classes('text-xs').style('color: #999;')
    
    def _get_profile_photo(self, sender_id: int, session_id: str) -> Optional[str]:
        """Récupère la photo de profil d'un expéditeur."""
        if not sender_id or not session_id:
            return None
        
        try:
            # Chercher dans le cache des photos
            from utils.profile_photo_cache import ProfilePhotoCache
            photo_cache = ProfilePhotoCache()
            
            # Utiliser directement sender_id comme entity_id
            photo_path = photo_cache.get_photo_path(sender_id)
            if photo_path and os.path.exists(photo_path):
                return photo_path
            
            # Si pas en cache, déclencher un téléchargement en arrière-plan
            asyncio.create_task(self._download_profile_photo_background(sender_id, session_id))
                
        except Exception as e:
            logger.debug(f"Erreur récupération photo profil: {e}")
        
        return None
    
    async def _download_profile_photo_background(self, sender_id: int, session_id: str):
        """Télécharge une photo de profil en arrière-plan."""
        try:
            account = self.telegram_manager.get_account(session_id)
            if not account or not account.is_connected:
                return
        
            from utils.profile_photo_cache import ProfilePhotoCache
            photo_cache = ProfilePhotoCache()
            
            # Récupérer l'entité
            entity = await account.client.get_entity(sender_id)
            if entity:
                # Télécharger la photo
                photo_path = await photo_cache.download_photo(
                    account.client,
                    entity,
                    sender_id
                )
                
                if photo_path:
                    logger.debug(f"Photo de profil téléchargée pour {sender_id}: {photo_path}")
                    # Mettre à jour l'affichage si c'est la conversation sélectionnée
                    if (self.state.get('selected_conversation') and 
                        self.state['selected_conversation'].get('entity_id') == sender_id):
                        self._update_conversation_header()
                        
        except Exception as e:
            logger.debug(f"Erreur téléchargement photo profil {sender_id}: {e}")
    
    async def _download_profile_photos_background(self, conversations: List[Dict]):
        """Télécharge les photos de profil des conversations en arrière-plan."""
        try:
            from utils.profile_photo_cache import ProfilePhotoCache
            photo_cache = ProfilePhotoCache()
            
            # Traiter les 50 premières conversations
            for conv in conversations:
                try:
                    entity_id = conv.get('entity_id')
                    session_id = conv.get('session_id')
                    
                    if not entity_id or not session_id:
                        continue
                    
                    # Vérifier si déjà en cache
                    if photo_cache.has_photo(entity_id):
                        continue
                    
                    # Récupérer le compte
                    account = self.telegram_manager.get_account(session_id)
                    if not account or not account.is_connected:
                        continue
                    
                    # Récupérer l'entité et télécharger la photo
                    entity = await account.client.get_entity(entity_id)
                    if entity:
                        await photo_cache.download_photo(
                            account.client,
                            entity,
                            entity_id
                        )
                        
                        # Petite pause pour éviter de surcharger
                        await asyncio.sleep(0.1)
                        
                except Exception as e:
                    logger.debug(f"Erreur téléchargement photo {entity_id}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Erreur téléchargement photos arrière-plan: {e}")
    
    def _is_verified_account(self, sender_name: str) -> bool:
        """Détermine si un compte est vérifié (officiel)."""
        # Liste des comptes officiels Telegram
        verified_accounts = [
            'Telegram', 'Telegram Tips', 'Telegram Support',
            'Telegram Premium', 'Telegram Bot', 'BotFather',
            'SpamBot', 'GIF', 'Music', 'Stickers'
        ]
        
        # Vérifier si c'est un compte officiel
        if sender_name in verified_accounts:
            return True
        
        # Vérifier si c'est un bot officiel (souvent se terminent par "Bot")
        if sender_name.endswith('Bot') and len(sender_name) > 3:
            return True
        
        # Vérifier les comptes avec badge bleu (canaux/groupes officiels)
        official_keywords = ['official', 'channel', 'news', 'support', 'help']
        sender_lower = sender_name.lower()
        
        for keyword in official_keywords:
            if keyword in sender_lower:
                return True
        
        return False
    
    async def _load_messages(self, chat_id: int, account_session_id: str) -> None:
        """Charge les messages d'une conversation."""
        try:
            account = self.telegram_manager.get_account(account_session_id)
            if not account or not account.is_connected:
                ui.notify('Compte non connecté', type='negative')
                return
            
            # Charger via le service (SQLite en priorité)
            messages = await self.messaging_service.get_messages_fast(
                account,
                chat_id,
                account_session_id,
                limit=200  # Plus de messages (au lieu de 50)
            )
            
            self.state['messages'] = messages
            self._update_messages_display()
            
            ui.timer(0.3, lambda: self._scroll_to_bottom(), once=True)
            
            # Marquer comme lu
            await self.messaging_service.mark_as_read(account, chat_id)
            
        except Exception as e:
            logger.error(f"Erreur chargement messages: {e}")
            ui.notify('Erreur lors du chargement des messages', type='negative')
    
    def _merge_and_display_conversations(self, conversations: List[Dict]):
        """
        Fusionne et affiche les conversations.
        
        Supprime les doublons : si un groupe existe sur plusieurs comptes,
        ne garde que celui du compte maître.
        """
        from core.session_manager import SessionManager
        session_mgr = SessionManager()
        master_account_id = session_mgr.get_master_account()
        
        # Créer mapping des noms
        account_names = {}
        account_names_to_session = {}
            for session_id in self.state['selected_accounts']:
                account = self.telegram_manager.get_account(session_id)
            if account:
                account_names[session_id] = account.account_name
                account_names_to_session[account.account_name] = session_id
        
        # Organiser les conversations par compte
        conversations_by_account = {}
        for conv in conversations:
            session_id = conv.get('session_id')
            if session_id:
                if session_id not in conversations_by_account:
                    conversations_by_account[session_id] = []
                conversations_by_account[session_id].append(conv)
        
        # Fusionner en supprimant les doublons (priorité au compte maître)
        merged_conversations = self.messaging_service.merge_conversations_from_accounts(
            conversations_by_account,
            master_account_id=master_account_id if master_account_id in self.state['selected_accounts'] else None,
            account_names=account_names
        )
        
        # Ajouter session_id à chaque conversation
        for conv in merged_conversations:
            account_name = conv.get('account_name')
            if account_name and account_name in account_names_to_session:
                conv['session_id'] = account_names_to_session[account_name]
        
        self.state['all_conversations'] = merged_conversations
        self._apply_filters()
    
    def _on_search_conversations(self, e) -> None:
        """Filtre les conversations par recherche."""
        search_text = e.value
        self._current_search_text = search_text
        
        # Recherche @username
        if search_text and search_text.startswith('@'):
            if len(search_text.lstrip('@')) >= 5:
                asyncio.create_task(self._search_username(search_text))
            else:
                self.state['username_search_result'] = None
                self._apply_filters()
        else:
            self.state['username_search_result'] = None
            self._apply_filters()
    
    async def _search_username(self, username: str) -> None:
        """Recherche un utilisateur par @username."""
        clean_username = username.lstrip('@').strip()
        
        if len(clean_username) < 5:
            return
        
        if not self.state['selected_accounts']:
            return
        
        if self.state['is_searching_username']:
            return
        
        self.state['is_searching_username'] = True
        
        try:
            await asyncio.sleep(0.5)
            
            if self._current_search_text != username:
                return
            
            account_id = self.state['selected_accounts'][0]
            account = self.telegram_manager.get_account(account_id)
            
            if not account or not account.is_connected:
                return
            
            result = await UserSearchService.search_by_username(account, username)
            
            if result:
                result['session_id'] = account_id
                result['account_name'] = account.account_name
                
                # Ajouter à la liste si pas déjà présent
                entity_id = result['entity_id']
                already_exists = any(conv['entity_id'] == entity_id for conv in self.state['all_conversations'])
                
                if not already_exists:
                    self.state['all_conversations'].insert(0, result)
                
                self.state['username_search_result'] = result
                self._apply_filters()
            else:
                self.state['username_search_result'] = None
                
        except Exception as e:
            logger.error(f"Erreur recherche username: {e}")
            self.state['username_search_result'] = None
            
        finally:
            self.state['is_searching_username'] = False
    
    def _apply_filters(self) -> None:
        """Applique les filtres de recherche."""
        search_text = self._current_search_text
        
        if search_text and self.search_input:
            self.search_input.value = search_text
        
        # Recherche @username
        if search_text and search_text.startswith('@') and self.state.get('username_search_result'):
            self.state['filtered_conversations'] = [self.state['username_search_result']]
        else:
            # Commencer avec les conversations actuelles
            filtered = self.state['all_conversations'].copy()
            
            # Appliquer le filtre de texte (recherche dans le titre)
            if search_text and not search_text.startswith('@'):
                search_lower = search_text.lower()
                filtered = [
                    conv for conv in filtered
                    if search_lower in conv['title'].lower()
                ]
            
            # Filtre messages non lus seulement
            if self.state['show_unread_only']:
                filtered = [
                    conv for conv in filtered
                    if conv.get('unread_count', 0) > 0
                ]
            
            self.state['filtered_conversations'] = filtered
        
        self._update_conversations_list()
    
    async def _handle_keydown(self, e) -> None:
        """Gère l'envoi avec Entrée."""
        if e.args.get('shiftKey', False):
            return
        
        if not self.state['selected_conversation']:
            notify('Sélectionnez une conversation', type='warning')
            return
        
        if not self.message_input.value or not self.message_input.value.strip():
            notify('Le message ne peut pas être vide', type='warning')
            return
        
        message = self.message_input.value.strip()
        self.message_input.value = ''
        
        conv = self.state['selected_conversation']
        account_session_id = conv.get('session_id')
        
        if not account_session_id:
            notify('Impossible de déterminer le compte', type='negative')
            return
        
        account = self.telegram_manager.get_account(account_session_id)
        if not account or not account.is_connected:
            notify('Compte non connecté', type='negative')
            return
        
        try:
            success = await self.messaging_service.send_message(
                account,
                conv['entity_id'],
                message
            )
            
            if success:
                notify('Message envoyé', type='positive')
                await self._load_messages(conv['entity_id'], account_session_id)
            else:
                notify('Erreur lors de l\'envoi', type='negative')
        except Exception as ex:
            logger.error(f"Erreur envoi message: {ex}")
            notify('Erreur lors de l\'envoi', type='negative')
    
    async def _delete_message(self, msg: Dict):
        """
        Supprime un message (seulement mes messages).
        
        Args:
            msg: Dictionnaire du message à supprimer
        """
        try:
            if not self.state['selected_conversation']:
                notify('Aucune conversation sélectionnée', type='warning')
                return
            
            # Vérifier que c'est bien mon message
            if not msg.get('from_me', False):
                notify('Vous ne pouvez supprimer que vos propres messages', type='warning')
                return
            
            # Confirmation
            chat_id = self.state['selected_conversation']['entity_id']
            message_id = msg['id']
            session_id = self.state['selected_conversation'].get('session_id')
            
            if not session_id:
                notify('Impossible de déterminer le compte', type='negative')
                return
            
            account = self.telegram_manager.get_account(session_id)
            if not account or not account.is_connected:
                notify('Compte non connecté', type='negative')
                return
            
            # Supprimer le message via Telegram
            try:
                await account.client.delete_messages(chat_id, [message_id])
                
                # Supprimer de la DB
                self.messaging_service.db.conn.execute("""
                    DELETE FROM messages
                    WHERE id = ? AND chat_id = ? AND session_id = ?
                """, (message_id, chat_id, session_id))
                
                # Supprimer de l'état local
                self.state['messages'] = [
                    m for m in self.state['messages']
                    if m['id'] != message_id
                ]
                
                # Re-render les messages
                self._update_messages_display()
                
                notify('Message supprimé', type='positive')
                
            except Exception as e:
                logger.error(f"Erreur suppression message: {e}")
                notify('Impossible de supprimer le message', type='negative')
        
        except Exception as e:
            logger.error(f"Erreur suppression message: {e}")
            notify('Erreur lors de la suppression', type='negative')
    
    def _scroll_to_bottom(self) -> None:
        """Fait défiler vers le bas."""
        ui.run_javascript('''
            (function scrollToBottom() {
                const container = document.querySelector('.messages-scroll-container');
                if (container) {
                    container.scrollTop = container.scrollHeight + 10000;
                    container.scrollTo(0, container.scrollHeight + 10000);
                    setTimeout(() => {
                        container.scrollTop = container.scrollHeight + 10000;
                        container.scrollTo(0, container.scrollHeight + 10000);
                    }, 150);
                }
            })();
        ''')
    
    def _photo_exists(self, photo_path: str) -> bool:
        """
        Vérifie si une photo existe (avec cache persistent).
        
        Args:
            photo_path: Chemin de la photo
            
        Returns:
            bool: True si la photo existe
        """
        if not photo_path:
            return False
            
        # Cache en mémoire d'abord
        if photo_path in self._photo_exists_cache:
            return self._photo_exists_cache[photo_path]
        
        # Vérifier sur disque
        import os
        exists = os.path.exists(photo_path)
        
        # Mettre en cache (persistent pendant la session)
        self._photo_exists_cache[photo_path] = exists
        
        return exists
    
    @staticmethod
    def _format_date(date: datetime) -> str:
        """Formate une date."""
        if not date:
            return ""
        
        try:
            if date.tzinfo is not None:
                date = date.replace(tzinfo=None)
            
            now = datetime.now()
            if now.tzinfo is not None:
                now = now.replace(tzinfo=None)
            
            diff = now - date
            
            if diff.days == 0:
                return date.strftime('%H:%M')
            elif diff.days == 1:
                return 'Hier'
            elif diff.days < 7:
                days = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche']
                return days[date.weekday()]
            else:
                return date.strftime('%d/%m/%Y')
        except Exception:
            return ""
