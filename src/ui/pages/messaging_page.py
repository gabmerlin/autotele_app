"""
Page de messagerie en temps réel.
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Set
from nicegui import ui

from core.telegram.manager import TelegramManager
from services.messaging_service import MessagingService
from utils.logger import get_logger
from utils.notification_manager import notify
from utils.constants import ICON_MESSAGE

logger = get_logger()


class MessagingPage:
    """Page de messagerie Telegram."""
    
    def __init__(self, telegram_manager: TelegramManager):
        """
        Initialise la page de messagerie.
        
        Args:
            telegram_manager: Gestionnaire de comptes Telegram
        """
        self.telegram_manager = telegram_manager
        
        # État de l'application
        self.state = {
            'selected_accounts': [],  # Liste des session_ids sélectionnés
            'all_conversations': [],  # Toutes les conversations de tous les comptes
            'filtered_conversations': [],  # Conversations après recherche
            'selected_conversation': None,  # Conversation actuellement affichée
            'messages': [],  # Messages de la conversation sélectionnée
            'current_account_for_reply': None,  # Compte utilisé pour répondre
        }
        
        # Conteneurs UI
        self.accounts_selector_container: Optional[ui.column] = None
        self.conversations_container: Optional[ui.column] = None
        self.messages_container: Optional[ui.column] = None
        self.conversation_header: Optional[ui.row] = None
        self.message_input: Optional[ui.textarea] = None
        self.search_input: Optional[ui.input] = None
        
        # Timer pour rafraîchissement automatique
        self.refresh_timer = None
        
        # Flags d'optimisation
        self._is_loading_conversations = False
        self._last_refresh_time = 0
        self._conversations_cache_time = 0
        self._cache_duration = 60  # Cache de 60 secondes pour améliorer les performances
    
    def render(self) -> None:
        """Rend la page de messagerie."""
        with ui.column().classes('w-full h-full gap-0 p-0').style(
            'height: calc(100vh - 0px); overflow: hidden;'
        ):
            # En-tête avec sélecteur de comptes
            self._render_header()
            
            # Layout principal : 2 colonnes (liste conversations | messages)
            with ui.row().classes('w-full flex-1 gap-0').style(
                'height: calc(100vh - 120px); overflow: hidden;'
            ):
                # Colonne gauche : Liste des conversations
                self._render_conversations_list()
                
                # Colonne droite : Messages de la conversation sélectionnée
                self._render_messages_area()
        
        # Charger les conversations au démarrage
        ui.timer(0.5, lambda: asyncio.create_task(self._load_conversations()), once=True)
        
        # Rafraîchissement automatique toutes les 60 secondes (au lieu de 10)
        # Cela réduit drastiquement la charge
        self.refresh_timer = ui.timer(60, lambda: asyncio.create_task(self._refresh_conversations()))
    
    def _render_header(self) -> None:
        """Rend l'en-tête avec sélecteur de comptes."""
        with ui.column().classes('w-full p-6 gap-4').style(
            'background: var(--bg-primary); border-bottom: 1px solid var(--border);'
        ):
            # Titre
            with ui.row().classes('items-center gap-3'):
                ui.label('💬').classes('text-4xl')
                ui.label('Messagerie').classes('text-3xl font-bold').style(
                    'color: var(--text-primary);'
                )
            
            # Sélecteur de comptes
            with ui.row().classes('items-center gap-3 w-full'):
                ui.label('Comptes:').classes('font-semibold').style('color: var(--text-primary);')
                
                self.accounts_selector_container = ui.row().classes('gap-2 flex-wrap flex-1')
                self._render_accounts_selector()
                
                # Bouton rafraîchir
                ui.button(
                    '🔄 Rafraîchir',
                    on_click=lambda: asyncio.create_task(self._load_conversations())
                ).props('outline dense').classes('text-blue-500')
    
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
                            await self._load_conversations()
                        return toggle
                    
                    style = 'background: var(--primary); color: white;' if is_selected else 'background: var(--bg-secondary); color: var(--text-secondary);'
                    
                    ui.button(
                        f"{'✓ ' if is_selected else ''}{account['account_name']}",
                        on_click=make_toggle(session_id)
                    ).props('dense').style(style)
    
    def _render_conversations_list(self) -> None:
        """Rend la liste des conversations."""
        with ui.column().classes('gap-0').style(
            'width: 380px; height: 100%; background: var(--bg-primary); '
            'border-right: 1px solid var(--border); overflow: hidden;'
        ):
            # Barre de recherche
            with ui.row().classes('w-full p-4 gap-2').style('border-bottom: 1px solid var(--border);'):
                self.search_input = ui.input(
                    placeholder='🔍 Rechercher...',
                    on_change=self._on_search_conversations
                ).classes('flex-1').props('dense outlined')
            
            # Liste des conversations
            self.conversations_container = ui.column().classes('w-full gap-0 flex-1').style(
                'overflow-y: auto; overflow-x: hidden;'
            )
            self._update_conversations_list()
    
    def _render_messages_area(self) -> None:
        """Rend la zone des messages."""
        with ui.column().classes('flex-1 gap-0').style(
            'height: 100%; background: var(--bg-secondary); overflow: hidden;'
        ):
            # En-tête de la conversation
            self.conversation_header = ui.row().classes('w-full p-4 gap-3 items-center').style(
                'background: var(--bg-primary); border-bottom: 1px solid var(--border); min-height: 70px;'
            )
            self._update_conversation_header()
            
            # Zone des messages avec classe unique pour le scroll
            self.messages_container = ui.column().classes('flex-1 w-full p-4 gap-3 messages-scroll-container').style(
                'overflow-y: auto; overflow-x: hidden; background: #f5f5f5;'
            )
            self._update_messages_display()
            
            # Zone de saisie
            self._render_message_input()
    
    def _render_message_input(self) -> None:
        """Rend la zone de saisie de message."""
        with ui.row().classes('w-full p-4 gap-2 items-end').style(
            'background: var(--bg-primary); border-top: 1px solid var(--border);'
        ):
            self.message_input = ui.textarea(
                placeholder='Écrivez votre message...'
            ).classes('flex-1').props('outlined dense rows=2')
            
            # Gérer les événements clavier
            self.message_input.on('keydown', self._handle_keydown)
            
            async def send_message():
                if not self.state['selected_conversation']:
                    notify('Sélectionnez une conversation', type='warning')
                    return
                
                if not self.message_input.value or not self.message_input.value.strip():
                    notify('Le message ne peut pas être vide', type='warning')
                    return
                
                message = self.message_input.value.strip()
                
                # Trouver le compte associé à cette conversation
                conv = self.state['selected_conversation']
                account_session_id = conv.get('session_id')
                
                if not account_session_id:
                    notify('Impossible de déterminer le compte', type='negative')
                    return
                
                account = self.telegram_manager.get_account(account_session_id)
                if not account or not account.is_connected:
                    notify('Compte non connecté', type='negative')
                    return
                
                # Envoyer le message
                success = await MessagingService.send_message(
                    account,
                    conv['entity_id'],
                    message
                )
                
                if success:
                    notify('✓ Message envoyé', type='positive')
                    
                    # Ajouter le message envoyé immédiatement à l'affichage
                    self._add_sent_message_to_display(message)
                    
                    self.message_input.value = ''
                    
                    # Rafraîchir les messages pour s'assurer qu'on a la version complète
                    await self._load_messages(conv['entity_id'], account_session_id)
                    
                    # Rafraîchir aussi la liste des conversations pour mettre à jour le dernier message
                    await self._load_conversations(force=True)  # Force le rechargement après envoi
                else:
                    notify('Erreur lors de l\'envoi', type='negative')
            
            with ui.column().classes('gap-1 items-end'):
                ui.button(
                    '📤 Envoyer',
                    on_click=send_message
                ).props('color=primary').classes('px-6')
                
                # Indicateur des raccourcis clavier
                ui.label('Entrée = Envoyer • Shift+Entrée = Nouvelle ligne').classes('text-xs').style(
                    'color: var(--text-secondary); opacity: 0.7;'
                )
    
    def _update_conversation_header(self) -> None:
        """Met à jour l'en-tête de la conversation."""
        if not self.conversation_header:
            return
        
        self.conversation_header.clear()
        
        with self.conversation_header:
            if self.state['selected_conversation']:
                conv = self.state['selected_conversation']
                
                # Avatar / Photo de profil
                if conv.get('profile_photo') and conv.get('has_photo'):
                    try:
                        import os
                        if os.path.exists(conv['profile_photo']):
                            ui.image(conv['profile_photo']).style('width: 50px; height: 50px; border-radius: 50%; object-fit: cover;')
                        else:
                            # Fallback vers icône
                            icon = '👤' if conv['type'] == 'user' else '👥' if conv['type'] == 'group' else '📢'
                            ui.label(icon).classes('text-3xl')
                    except Exception as e:
                        # Fallback vers icône en cas d'erreur
                        icon = '👤' if conv['type'] == 'user' else '👥' if conv['type'] == 'group' else '📢'
                        ui.label(icon).classes('text-3xl')
                else:
                    # Pas de photo, afficher l'icône
                    icon = '👤' if conv['type'] == 'user' else '👥' if conv['type'] == 'group' else '📢'
                    ui.label(icon).classes('text-3xl')
                
                # Infos
                with ui.column().classes('gap-1 flex-1'):
                    ui.label(conv['title']).classes('text-xl font-bold').style('color: var(--text-primary);')
                    # Afficher le nom du compte (déjà le bon nom depuis merge_conversations_from_accounts)
                    display_name = conv.get('account_name', 'Inconnu')
                    ui.label(f"Compte: {display_name}").classes('text-sm').style(
                        'color: var(--text-secondary);'
                    )
            else:
                ui.label('Sélectionnez une conversation').classes('text-lg').style(
                    'color: var(--text-secondary);'
                )
    
    def _update_conversations_list(self) -> None:
        """Met à jour la liste des conversations."""
        if not self.conversations_container:
            return
        
        self.conversations_container.clear()
        
        conversations = self.state.get('filtered_conversations') or self.state.get('all_conversations', [])
        
        with self.conversations_container:
            if not conversations:
                with ui.column().classes('w-full p-8 items-center gap-3'):
                    ui.label('📭').classes('text-5xl').style('opacity: 0.3;')
                    ui.label('Aucune conversation').classes('text-lg').style('color: var(--text-secondary);')
            else:
                for conv in conversations:
                    self._render_conversation_item(conv)
    
    def _render_conversation_item(self, conv: Dict) -> None:
        """Rend un élément de conversation."""
        # Créer un ID unique pour cette conversation (session_id + entity_id)
        conv_unique_id = f"{conv.get('account_name')}_{conv['entity_id']}"
        selected_unique_id = None
        if self.state['selected_conversation']:
            selected_unique_id = f"{self.state['selected_conversation'].get('account_name')}_{self.state['selected_conversation']['entity_id']}"
        
        is_selected = conv_unique_id == selected_unique_id
        
        style = 'background: rgba(30, 58, 138, 0.1);' if is_selected else ''
        hover_style = 'cursor: pointer; transition: background 0.2s;'
        
        async def select_conversation():
            # Marquer comme sélectionnée
            self.state['selected_conversation'] = conv
            self._update_conversation_header()
            self._update_conversations_list()
            
            # Charger les messages - utiliser le session_id stocké
            account_session_id = conv.get('session_id')
            await self._load_messages(conv['entity_id'], account_session_id)
        
        with ui.card().classes('w-full p-3 cursor-pointer').style(
            f'{style} border: none; border-bottom: 1px solid var(--border); '
            f'border-radius: 0; {hover_style}'
        ).on('click', select_conversation):
            with ui.row().classes('w-full items-start gap-3'):
                # Avatar / Photo de profil
                if conv.get('profile_photo') and conv.get('has_photo'):
                    try:
                        import os
                        if os.path.exists(conv['profile_photo']):
                            ui.image(conv['profile_photo']).style('width: 40px; height: 40px; border-radius: 50%; object-fit: cover;')
                        else:
                            # Fallback vers icône
                            icon = '👤' if conv['type'] == 'user' else '👥' if conv['type'] == 'group' else '📢'
                            ui.label(icon).classes('text-2xl')
                    except Exception as e:
                        # Fallback vers icône en cas d'erreur
                        icon = '👤' if conv['type'] == 'user' else '👥' if conv['type'] == 'group' else '📢'
                        ui.label(icon).classes('text-2xl')
                else:
                    # Pas de photo, afficher l'icône
                    icon = '👤' if conv['type'] == 'user' else '👥' if conv['type'] == 'group' else '📢'
                    ui.label(icon).classes('text-2xl')
                
                # Contenu
                with ui.column().classes('flex-1 gap-1 min-w-0'):
                    # Première ligne : titre + badge non lu
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
                    prefix = '✓ ' if conv.get('last_message_from_me') else ''
                    ui.label(f"{prefix}{last_msg}").classes('text-xs').style(
                        'color: var(--text-secondary); white-space: nowrap; '
                        'overflow: hidden; text-overflow: ellipsis;'
                    )
                    
                    # Date + compte
                    with ui.row().classes('items-center gap-2'):
                        if conv.get('last_message_date'):
                            date_str = self._format_date(conv['last_message_date'])
                            ui.label(date_str).classes('text-xs').style('color: var(--text-secondary);')
                        
                        # Afficher le nom du compte (déjà le bon nom depuis merge_conversations_from_accounts)
                        display_name = conv.get('account_name', 'Inconnu')
                        ui.label(f"• {display_name}").classes('text-xs').style(
                            'color: var(--accent);'
                        )
    
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
                        ui.label('💬').classes('text-5xl').style('opacity: 0.3;')
                        ui.label('Aucun message').classes('text-lg').style('color: var(--text-secondary);')
                else:
                    with ui.column().classes('w-full h-full items-center justify-center gap-3'):
                        ui.label('👈').classes('text-5xl').style('opacity: 0.3;')
                        ui.label('Sélectionnez une conversation').classes('text-lg').style('color: var(--text-secondary);')
            else:
                for msg in messages:
                    self._render_message_bubble(msg)
    
    def _render_message_bubble(self, msg: Dict) -> None:
        """Rend une bulle de message."""
        is_from_me = msg.get('from_me', False)
        
        # Style de la bulle
        if is_from_me:
            bubble_style = 'background: #dcf8c6; align-self: flex-end; max-width: 70%;'
            text_align = 'text-right'
        else:
            bubble_style = 'background: white; align-self: flex-start; max-width: 70%;'
            text_align = 'text-left'
        
        # Créer le conteneur de la bulle
        bubble_container = ui.card().classes(f'p-3 {text_align}').style(
            f'{bubble_style} border-radius: 12px; border: 1px solid #ddd;'
        )
        
        with bubble_container:
            # Nom de l'expéditeur (si pas de moi)
            if not is_from_me and msg.get('sender_name'):
                ui.label(msg['sender_name']).classes('text-xs font-bold mb-1').style('color: #0088cc;')
            
            # Texte du message
            if msg.get('text'):
                ui.label(msg['text']).classes('text-sm').style('color: var(--text-primary); word-wrap: break-word;')
            
            # Média
            if msg.get('has_media'):
                media_type = msg.get('media_type', '')
                media_data = msg.get('media_data')
                media_caption = msg.get('media_caption', '')
                
                # Afficher l'image si c'est une photo
                if media_type == 'MessageMediaPhoto' and media_data:
                    try:
                        # Vérifier que le fichier existe
                        import os
                        if os.path.exists(media_data):
                            ui.image(media_data).style('max-width: 500px; max-height: 400px; border-radius: 12px; cursor: pointer;')
                        else:
                            ui.label('📷 Photo (fichier manquant)').classes('text-sm italic').style('color: var(--text-secondary);')
                    except Exception as e:
                        ui.label('📷 Photo (erreur d\'affichage)').classes('text-sm italic').style('color: var(--text-secondary);')
                
                # Afficher les autres types de médias
                elif media_type == 'MessageMediaDocument':
                    ui.label('📎 Document').classes('text-sm').style('color: var(--accent);')
                    if media_caption:
                        ui.label(media_caption).classes('text-xs italic').style('color: var(--text-secondary);')
                elif media_type == 'MessageMediaVideo':
                    ui.label('🎥 Vidéo').classes('text-sm').style('color: var(--accent);')
                elif media_type == 'MessageMediaAudio':
                    ui.label('🎵 Audio').classes('text-sm').style('color: var(--accent);')
                else:
                    ui.label(f'[{media_type or "Média"}]').classes('text-xs italic').style('color: var(--text-secondary);')
            
            # Date et heure
            if msg.get('date'):
                # Normaliser la date
                msg_date = msg['date']
                if hasattr(msg_date, 'tzinfo') and msg_date.tzinfo is not None:
                    msg_date = msg_date.replace(tzinfo=None)
                
                date_str = msg_date.strftime('%H:%M')
                edited_marker = ' (modifié)' if msg.get('edited') else ''
                ui.label(f"{date_str}{edited_marker}").classes('text-xs mt-1').style('color: var(--text-secondary);')
        
        # Si c'est un message envoyé récemment, faire défiler vers le bas
        if msg.get('id') == -1:  # Message temporaire
            # Faire défiler vers le bas après un court délai
            ui.timer(0.1, lambda: self._scroll_to_bottom(), once=True)
    
    async def _load_conversations(self, force: bool = False) -> None:
        """
        Charge les conversations de tous les comptes sélectionnés.
        
        Args:
            force: Force le rechargement même si le cache est valide
        """
        if not self.state['selected_accounts']:
            self.state['all_conversations'] = []
            self.state['filtered_conversations'] = []
            self._update_conversations_list()
            return
        
        # Éviter les chargements multiples simultanés
        if self._is_loading_conversations:
            logger.info("Chargement déjà en cours, ignoré")
            return
        
        # Vérifier le cache (ne pas recharger si moins de 60s pour les conversations)
        import time
        current_time = time.time()
        if not force and (current_time - self._conversations_cache_time) < self._cache_duration:
            logger.info(f"Cache valide, pas de rechargement (cache: {int(current_time - self._conversations_cache_time)}s)")
            return
        
        self._is_loading_conversations = True
        
        try:
            # Ne pas afficher la notification si c'est un rafraîchissement automatique
            if not hasattr(self, '_is_refreshing'):
                notify('Chargement des conversations...', type='info')
            
            conversations_by_account = {}
            
            # Charger les conversations en parallèle pour plus de rapidité
            import asyncio
            tasks = []
            accounts_map = {}
            
            for session_id in self.state['selected_accounts']:
                account = self.telegram_manager.get_account(session_id)
                if account and account.is_connected:
                    task = MessagingService.get_conversations(account, limit=20)  # Réduit à 20 pour plus de rapidité
                    tasks.append(task)
                    accounts_map[len(tasks) - 1] = session_id
            
            # Attendre que toutes les conversations soient chargées
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for idx, result in enumerate(results):
                    if not isinstance(result, Exception):
                        session_id = accounts_map[idx]
                        conversations_by_account[session_id] = result
            
            # Récupérer le compte maître pour filtrer les doublons
            from core.session_manager import SessionManager
            session_mgr = SessionManager()
            master_account_id = session_mgr.get_master_account()
            
            # Créer un mapping session_id -> nom du compte
            account_names = {}
            account_names_to_session = {}  # Mapping inverse nom -> session_id
            for session_id in self.state['selected_accounts']:
                account = self.telegram_manager.get_account(session_id)
                if account:
                    account_names[session_id] = account.account_name
                    account_names_to_session[account.account_name] = session_id
            
            # Fusionner toutes les conversations (avec filtrage des doublons par compte maître)
            # MAIS seulement pour les comptes sélectionnés
            filtered_conversations_by_account = {
                session_id: convs for session_id, convs in conversations_by_account.items()
                if session_id in self.state['selected_accounts']
            }
            
            all_convs = MessagingService.merge_conversations_from_accounts(
                filtered_conversations_by_account,
                master_account_id=master_account_id if master_account_id in self.state['selected_accounts'] else None,
                account_names=account_names
            )
            
            # Ajouter le session_id à chaque conversation pour faciliter la sélection
            for conv in all_convs:
                account_name = conv.get('account_name')
                conv['session_id'] = account_names_to_session.get(account_name, account_name)
            
            self.state['all_conversations'] = all_convs
            
            # Préserver le filtrage existant si il y en a un
            current_search = getattr(self, '_current_search_text', '')
            if current_search:
                self.state['filtered_conversations'] = [
                    conv for conv in all_convs
                    if current_search.lower() in conv['title'].lower()
                ]
                # Restaurer le texte de recherche dans l'input
                if self.search_input:
                    self.search_input.value = current_search
            else:
                self.state['filtered_conversations'] = all_convs.copy()
            
            self._update_conversations_list()
            
            # Mettre à jour le cache
            self._conversations_cache_time = current_time
            
            # Ne pas afficher la notification si c'est un rafraîchissement automatique
            if not hasattr(self, '_is_refreshing'):
                notify(f'✓ {len(all_convs)} conversation(s) chargée(s)', type='positive')
            
        except Exception as e:
            logger.error(f"Erreur chargement conversations: {e}")
            # Ne pas afficher de notification d'erreur en rafraîchissement automatique
            if not hasattr(self, '_is_refreshing'):
                notify('Erreur lors du chargement', type='negative')
        finally:
            self._is_loading_conversations = False
    
    async def _load_messages(self, chat_id: int, account_session_id: str) -> None:
        """Charge les messages d'une conversation."""
        try:
            account = self.telegram_manager.get_account(account_session_id)
            if not account or not account.is_connected:
                notify('Compte non connecté', type='negative')
                return
            
            # Charger seulement 30 messages au lieu de 50 pour plus de rapidité
            messages = await MessagingService.get_messages(account, chat_id, limit=20)  # Réduit à 20 pour plus de rapidité
            
            self.state['messages'] = messages
            self._update_messages_display()
            
            # Faire défiler vers le bas pour afficher les derniers messages
            # Plusieurs tentatives avec délais progressifs pour s'assurer que ça fonctionne
            ui.timer(0.2, lambda: self._scroll_to_bottom(), once=True)
            ui.timer(0.5, lambda: self._scroll_to_bottom(), once=True)
            ui.timer(0.8, lambda: self._scroll_to_bottom(), once=True)
            ui.timer(1.0, lambda: self._scroll_to_bottom(), once=True)
            
            # Marquer comme lu
            await MessagingService.mark_as_read(account, chat_id)
            
        except Exception as e:
            logger.error(f"Erreur chargement messages: {e}")
            notify('Erreur lors du chargement des messages', type='negative')
    
    async def _refresh_conversations(self) -> None:
        """Rafraîchit les conversations automatiquement."""
        if self.state['selected_accounts']:
            import time
            current_time = time.time()
            
            # Éviter les rafraîchissements trop fréquents (throttling)
            if current_time - self._last_refresh_time < 30:
                logger.info("Rafraîchissement ignoré (trop récent)")
                return
            
            self._last_refresh_time = current_time
            self._is_refreshing = True
            await self._load_conversations(force=False)  # Utilise le cache si valide
            self._is_refreshing = False
    
    def _on_search_conversations(self, e) -> None:
        """Filtre les conversations par recherche."""
        search_text = e.value
        self._current_search_text = search_text  # Sauvegarder le texte de recherche
        
        if not search_text:
            self.state['filtered_conversations'] = self.state['all_conversations'].copy()
        else:
            self.state['filtered_conversations'] = [
                conv for conv in self.state['all_conversations']
                if search_text.lower() in conv['title'].lower()
            ]
        
        # Garder la conversation sélectionnée si elle est toujours visible
        if self.state['selected_conversation']:
            selected_unique_id = f"{self.state['selected_conversation'].get('account_name')}_{self.state['selected_conversation']['entity_id']}"
            still_visible = any(
                f"{conv.get('account_name')}_{conv['entity_id']}" == selected_unique_id
                for conv in self.state['filtered_conversations']
            )
            if not still_visible:
                self.state['selected_conversation'] = None
                self._update_conversation_header()
                self._update_messages_display()
        
        self._update_conversations_list()
    
    def _handle_keydown(self, e) -> None:
        """Gère les événements clavier dans la zone de saisie."""
        # Vérifier si c'est la touche Entrée
        if e.args.get('key') == 'Enter':
            # Si Shift n'est pas pressé, envoyer le message
            if not e.args.get('shiftKey', False):
                # Empêcher le comportement par défaut (retour à la ligne) avec JavaScript
                ui.run_javascript('event.preventDefault();')
                
                # Envoyer le message
                async def send_on_enter():
                    if not self.state['selected_conversation']:
                        notify('Sélectionnez une conversation', type='warning')
                        return
                    
                    if not self.message_input.value or not self.message_input.value.strip():
                        notify('Le message ne peut pas être vide', type='warning')
                        return
                    
                    message = self.message_input.value.strip()
                    
                    # Trouver le compte associé à cette conversation
                    conv = self.state['selected_conversation']
                    account_session_id = conv.get('account_name')  # En fait c'est le session_id
                    
                    if not account_session_id:
                        notify('Impossible de déterminer le compte', type='negative')
                        return
                    
                    account = self.telegram_manager.get_account(account_session_id)
                    if not account or not account.is_connected:
                        notify('Compte non connecté', type='negative')
                        return
                    
                    # Envoyer le message
                    success = await MessagingService.send_message(
                        account,
                        conv['entity_id'],
                        message
                    )
                    
                    if success:
                        notify('✓ Message envoyé', type='positive')
                        
                        # Ajouter le message envoyé immédiatement à l'affichage
                        self._add_sent_message_to_display(message)
                        
                        self.message_input.value = ''
                        
                        # Rafraîchir les messages pour s'assurer qu'on a la version complète
                        await self._load_messages(conv['entity_id'], account_session_id)
                        
                        # Rafraîchir aussi la liste des conversations pour mettre à jour le dernier message
                        await self._load_conversations(force=True)  # Force le rechargement après envoi
                    else:
                        notify('Erreur lors de l\'envoi', type='negative')
                
                # Exécuter l'envoi
                asyncio.create_task(send_on_enter())
    
    def _scroll_to_bottom(self) -> None:
        """Fait défiler la zone des messages vers le bas."""
        # Utiliser JavaScript pour cibler spécifiquement le conteneur de messages
        ui.run_javascript('''
            (function scrollToBottom() {
                const container = document.querySelector('.messages-scroll-container');
                if (container) {
                    // Forcer le scroll en utilisant différentes méthodes
                    container.scrollTop = container.scrollHeight + 10000;
                    container.scrollTo(0, container.scrollHeight + 10000);
                    
                    // Log pour debug
                    console.log('[SCROLL] scrollHeight:', container.scrollHeight, 'scrollTop:', container.scrollTop);
                    
                    // Réessayer après un court délai
                    setTimeout(() => {
                        container.scrollTop = container.scrollHeight + 10000;
                        container.scrollTo(0, container.scrollHeight + 10000);
                        console.log('[SCROLL RETRY] scrollHeight:', container.scrollHeight, 'scrollTop:', container.scrollTop);
                    }, 150);
                } else {
                    console.error('[SCROLL ERROR] Container .messages-scroll-container not found!');
                }
            })();
        ''')
    
    def _add_sent_message_to_display(self, message_text: str) -> None:
        """Ajoute immédiatement un message envoyé à l'affichage."""
        if not self.messages_container:
            return
        
        # Créer le dictionnaire du message envoyé
        sent_message = {
            "id": -1,  # ID temporaire
            "text": message_text,
            "date": datetime.now(),
            "from_me": True,
            "sender_id": None,
            "sender_name": "Vous",
            "has_media": False,
            "media_type": None,
            "reply_to": None,
            "edited": False,
            "views": None,
        }
        
        # Ajouter à la fin de la liste des messages
        self.state['messages'].append(sent_message)
        
        # Ajouter la bulle de message à l'affichage avec le conteneur explicite
        with self.messages_container:
            self._render_message_bubble(sent_message)
    
    @staticmethod
    def _format_date(date: datetime) -> str:
        """Formate une date de manière lisible."""
        if not date:
            return ""
        
        try:
            # Normaliser les dates pour éviter les problèmes de timezone
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

