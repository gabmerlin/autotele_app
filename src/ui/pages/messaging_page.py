"""
Page de messagerie en temps réel.
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Set
from nicegui import ui

from core.telegram.manager import TelegramManager
from services.messaging_service import MessagingService
from ui.components.svg_icons import svg
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
            'show_groups': False,  # Afficher ou non les groupes
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
        
        # Charger immédiatement depuis le cache si disponible
        self._load_conversations_from_cache_immediately()
        
        # Charger les conversations en arrière-plan
        asyncio.create_task(self._load_conversations())
        
        # Rafraîchissement automatique toutes les 300 secondes (5 min)
        # Cela réduit drastiquement la charge
        self.refresh_timer = ui.timer(300, lambda: asyncio.create_task(self._refresh_conversations()))
    
    def _load_conversations_from_cache_immediately(self) -> None:
        """Charge immédiatement les conversations depuis le cache sans délai."""
        try:
            # Charger depuis le cache même s'il est ancien (jusqu'à 24h)
            conversations_by_account = MessagingService.load_conversations_cache()
            
            if conversations_by_account:
                # Convertir les strings datetime en objets datetime
                for session_id, conversations in conversations_by_account.items():
                    for conv in conversations:
                        if conv.get('last_message_date') and isinstance(conv['last_message_date'], str):
                            try:
                                from datetime import datetime
                                conv['last_message_date'] = datetime.fromisoformat(conv['last_message_date'])
                            except:
                                conv['last_message_date'] = None
                
                # Fusionner et afficher immédiatement
                self._merge_and_display_conversations(conversations_by_account)
                
        except Exception as e:
            logger.error(f"Erreur chargement cache immédiat: {e}")
    
    async def _toggle_groups_display(self) -> None:
        """Ajoute ou supprime les groupes de l'affichage sans perdre les conversations existantes."""
        try:
            if self.state['show_groups']:
                # Mode "avec groupes" - ajouter les groupes aux conversations existantes
                await self._add_groups_to_conversations()
            else:
                # Mode "sans groupes" - supprimer les groupes des conversations
                self._remove_groups_from_conversations()
            
            # Réappliquer les filtres et mettre à jour l'affichage
            self._apply_filters()
            
        except Exception as e:
            logger.error(f"Erreur toggle groupes: {e}")
            notify('Erreur lors du changement d\'affichage des groupes', type='negative')
    
    async def _add_groups_to_conversations(self) -> None:
        """Ajoute les groupes aux conversations existantes."""
        try:
            # Afficher une notification de chargement
            notify('Chargement des groupes...', type='info')
            
            # Charger seulement les groupes pour les comptes sélectionnés
            conversations_by_account = {}
            
            for session_id in self.state['selected_accounts']:
                account = self.telegram_manager.get_account(session_id)
                if account and account.is_connected:
                    # Charger uniquement les groupes (pas les utilisateurs)
                    groups_only = await MessagingService.get_conversations(
                        account, 
                        limit=10,
                        include_groups=True,
                        groups_only=True  # Seulement les groupes
                    )
                    
                    if groups_only:
                        conversations_by_account[session_id] = groups_only
            
            if conversations_by_account:
                # Fusionner avec les conversations existantes
                self._merge_groups_with_existing_conversations(conversations_by_account)
                notify('Groupes ajoutés à la liste', type='positive')
            else:
                notify('Aucun groupe trouvé', type='warning')
                
        except Exception as e:
            logger.error(f"Erreur ajout groupes: {e}")
            notify('Erreur lors du chargement des groupes', type='negative')
    
    def _merge_groups_with_existing_conversations(self, new_groups_by_account: dict) -> None:
        """Fusionne les nouveaux groupes avec les conversations existantes en respectant le compte maître."""
        # Récupérer le compte maître
        from core.session_manager import SessionManager
        session_mgr = SessionManager()
        master_account_id = session_mgr.get_master_account()
        
        # Créer le mapping des noms de comptes
        account_names = {}
        for session_id in self.state['selected_accounts']:
            account = self.telegram_manager.get_account(session_id)
            if account:
                account_names[session_id] = account.account_name
        
        # Utiliser la logique de fusion existante pour les nouveaux groupes
        merged_groups = MessagingService.merge_conversations_from_accounts(
            new_groups_by_account,
            master_account_id=master_account_id if master_account_id in self.state['selected_accounts'] else None,
            account_names=account_names
        )
        
        # Créer un mapping des conversations existantes par ID
        existing_conversations = {conv['entity_id']: conv for conv in self.state['all_conversations']}
        
        # Ajouter les nouveaux groupes fusionnés qui ne sont pas déjà présents
        for group in merged_groups:
            group_id = group['entity_id']
            if group_id not in existing_conversations:
                # Ajouter le session_id au groupe
                account_name = group.get('account_name')
                if account_name:
                    # Trouver le session_id correspondant au nom du compte
                    for session_id, name in account_names.items():
                        if name == account_name:
                            group['session_id'] = session_id
                            break
                
                self.state['all_conversations'].append(group)
        
        # Trier par date de dernier message (plus récent en premier)
        self.state['all_conversations'].sort(
            key=lambda x: x.get('last_message_date') or datetime.min, 
            reverse=True
        )
    
    def _remove_groups_from_conversations(self) -> None:
        """Supprime les groupes des conversations (garde seulement les utilisateurs)."""
        # Compter les groupes avant suppression
        groups_count = len([
            conv for conv in self.state['all_conversations']
            if conv.get('type') in ['group', 'supergroup', 'channel']
        ])
        
        # Filtrer pour garder seulement les conversations d'utilisateurs
        self.state['all_conversations'] = [
            conv for conv in self.state['all_conversations']
            if conv.get('type') == 'user'
        ]
        
        # Notifier le nombre de groupes supprimés
        if groups_count > 0:
            notify(f'{groups_count} groupe(s) masqué(s)', type='info')
    
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
            
            # Sélecteur de comptes
            with ui.row().classes('items-center gap-3 w-full'):
                ui.label('Comptes:').classes('font-semibold').style('color: var(--text-primary);')
                
                self.accounts_selector_container = ui.row().classes('gap-2 flex-wrap flex-1')
                self._render_accounts_selector()
                
                # Bouton rafraîchir
                with ui.button(
                    on_click=lambda: asyncio.create_task(self._load_conversations())
                ).props('outline dense').classes('text-blue-500'):
                    with ui.row().classes('items-center gap-1'):
                        ui.html(svg('sync', 18, '#3b82f6'))
                        ui.label('Rafraîchir')
    
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
                    
                    # Style amélioré pour mieux distinguer les comptes
                    if is_selected:
                        style = (
                            'background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); '
                            'color: white; '
                            'font-weight: bold; '
                            'border: 2px solid #1d4ed8; '
                            'box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3); '
                            'transform: scale(1.05);'
                        )
                        icon = '✓ '
                    else:
                        style = (
                            'background: #f3f4f6; '
                            'color: #6b7280; '
                            'font-weight: normal; '
                            'border: 2px solid #e5e7eb; '
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
            # Barre de recherche et filtres
            with ui.column().classes('w-full p-4 gap-2').style('border-bottom: 1px solid var(--border);'):
                self.search_input = ui.input(
                    placeholder='Rechercher...',
                    on_change=self._on_search_conversations
                ).classes('w-full').props('dense outlined')
                
                # Case à cocher pour afficher les groupes
                async def toggle_groups(e):
                    self.state['show_groups'] = e.value
                    # Ajouter/supprimer les groupes sans perdre les conversations existantes
                    await self._toggle_groups_display()
                
                ui.checkbox(
                    'Afficher les groupes',
                    value=self.state['show_groups'],
                    on_change=toggle_groups
                ).classes('text-sm').style('color: var(--text-primary);')
            
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
            
            # Gérer Entrée pour envoyer (Shift+Entrée pour nouvelle ligne)
            self.message_input.on('keydown.enter', self._handle_keydown)
            
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
                    notify('Message envoyé', type='positive')
                    
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
                with ui.button(
                    on_click=send_message
                ).props('color=primary').classes('px-6'):
                    with ui.row().classes('items-center gap-1'):
                        ui.html(svg('send', 18, 'white'))
                        ui.label('Envoyer')
                
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
                            icon_name = 'person' if conv['type'] == 'user' else 'group' if conv['type'] == 'group' else 'campaign'
                            ui.html(svg(icon_name, 40, 'var(--text-secondary)'))
                    except Exception as e:
                        # Fallback vers icône en cas d'erreur
                        icon_name = 'person' if conv['type'] == 'user' else 'group' if conv['type'] == 'group' else 'campaign'
                        ui.html(svg(icon_name, 40, 'var(--text-secondary)'))
                else:
                    # Pas de photo, afficher l'icône SVG
                    icon_name = 'person' if conv['type'] == 'user' else 'group' if conv['type'] == 'group' else 'campaign'
                    ui.html(svg(icon_name, 40, 'var(--text-secondary)'))
                
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
                    ui.html(svg('mail_outline', 60, 'var(--text-secondary)'))
                    ui.label('Aucune conversation').classes('text-lg').style('color: var(--text-secondary);')
            else:
                for conv in conversations:
                    self._render_conversation_item(conv)
    
    def _update_conversation_selection(self) -> None:
        """Met à jour seulement la sélection visuelle des conversations (sans re-render)."""
        if not self.conversations_container:
            return
        
        # Cette méthode peut être appelée pour mettre à jour juste les styles de sélection
        # sans re-render toute la liste
        pass
    
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
            
            # Mettre à jour seulement l'en-tête (pas toute la liste)
            self._update_conversation_header()
            
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
                            icon_name = 'person' if conv['type'] == 'user' else 'group' if conv['type'] == 'group' else 'campaign'
                            ui.html(svg(icon_name, 28, 'var(--text-secondary)'))
                    except Exception as e:
                        # Fallback vers icône SVG en cas d'erreur
                        icon_name = 'person' if conv['type'] == 'user' else 'group' if conv['type'] == 'group' else 'campaign'
                        ui.html(svg(icon_name, 28, 'var(--text-secondary)'))
                else:
                    # Pas de photo, afficher l'icône SVG
                    icon_name = 'person' if conv['type'] == 'user' else 'group' if conv['type'] == 'group' else 'campaign'
                    ui.html(svg(icon_name, 28, 'var(--text-secondary)'))
                
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
                    prefix = ''
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
                        ui.html(svg('chat', 60, 'var(--text-secondary)'))
                        ui.label('Aucun message').classes('text-lg').style('color: var(--text-secondary);')
                else:
                    with ui.column().classes('w-full h-full items-center justify-center gap-3'):
                        ui.html(svg('arrow_back', 60, 'var(--text-secondary)'))
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
                            with ui.row().classes('items-center gap-1'):
                                ui.html(svg('photo', 18, 'var(--text-secondary)'))
                                ui.label('Photo (fichier manquant)').classes('text-sm italic').style('color: var(--text-secondary);')
                    except Exception as e:
                        with ui.row().classes('items-center gap-1'):
                            ui.html(svg('photo', 18, 'var(--text-secondary)'))
                            ui.label('Photo (erreur d\'affichage)').classes('text-sm italic').style('color: var(--text-secondary);')
                
                # Afficher les autres types de médias
                elif media_type == 'MessageMediaDocument':
                    with ui.row().classes('items-center gap-1'):
                        ui.html(svg('attach_file', 18, 'var(--accent)'))
                        ui.label('Document').classes('text-sm').style('color: var(--accent);')
                    if media_caption:
                        ui.label(media_caption).classes('text-xs italic').style('color: var(--text-secondary);')
                elif media_type == 'MessageMediaVideo':
                    with ui.row().classes('items-center gap-1'):
                        ui.html(svg('videocam', 18, 'var(--accent)'))
                        ui.label('Vidéo').classes('text-sm').style('color: var(--accent);')
                elif media_type == 'MessageMediaAudio':
                    with ui.row().classes('items-center gap-1'):
                        ui.html(svg('audiotrack', 18, 'var(--accent)'))
                        ui.label('Audio').classes('text-sm').style('color: var(--accent);')
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
        Charge les conversations avec cache persistant.
        
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
            return
        
        # Vérifier le cache persistant (durée étendue pour plus de rapidité)
        if not force and MessagingService.is_cache_valid(max_age_minutes=120):  # 2 heures au lieu de 30 min
            conversations_by_account = MessagingService.load_conversations_cache()
            
            if conversations_by_account:
                # Convertir les strings datetime en objets datetime
                for session_id, conversations in conversations_by_account.items():
                    for conv in conversations:
                        if conv.get('last_message_date') and isinstance(conv['last_message_date'], str):
                            try:
                                from datetime import datetime
                                conv['last_message_date'] = datetime.fromisoformat(conv['last_message_date'])
                            except:
                                conv['last_message_date'] = None
                
                # Fusionner et afficher immédiatement
                self._merge_and_display_conversations(conversations_by_account)
                
                # Recharger en arrière-plan pour mettre à jour
                asyncio.create_task(self._background_refresh_conversations())
                return
        
        # Chargement depuis l'API
        self._is_loading_conversations = True
        
        try:
            # Ne pas afficher la notification si c'est un rafraîchissement automatique
            if not hasattr(self, '_is_refreshing'):
                notify('Chargement des conversations...', type='info')
            
            conversations_by_account = {}
            
            # Charger les conversations en parallèle
            tasks = []
            accounts_map = {}
            
            for session_id in self.state['selected_accounts']:
                account = self.telegram_manager.get_account(session_id)
                if account and account.is_connected:
                    # Limite réduite pour un chargement plus rapide
                    limit = 20 if not self.state['show_groups'] else 10
                    task = MessagingService.get_conversations(
                        account, 
                        limit=limit,
                        include_groups=self.state['show_groups']
                    )
                    tasks.append(task)
                    accounts_map[len(tasks) - 1] = session_id
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for idx, result in enumerate(results):
                    if not isinstance(result, Exception):
                        session_id = accounts_map[idx]
                        conversations_by_account[session_id] = result
                
                # Sauvegarder dans le cache
                MessagingService.save_conversations_cache(conversations_by_account)
            
            # Fusionner et afficher
            self._merge_and_display_conversations(conversations_by_account)
            
        except Exception as e:
            logger.error(f"Erreur chargement conversations: {e}")
            # Ne pas afficher de notification d'erreur en rafraîchissement automatique
            if not hasattr(self, '_is_refreshing'):
                notify('Erreur lors du chargement', type='negative')
        finally:
            self._is_loading_conversations = False
    
    def _merge_and_display_conversations(self, conversations_by_account: dict) -> None:
        """Fusionne et affiche les conversations."""
        # Récupérer le compte maître
        from core.session_manager import SessionManager
        session_mgr = SessionManager()
        master_account_id = session_mgr.get_master_account()
        
        # Créer le mapping des noms
        account_names = {}
        account_names_to_session = {}
        for session_id in self.state['selected_accounts']:
            account = self.telegram_manager.get_account(session_id)
            if account:
                account_names[session_id] = account.account_name
                account_names_to_session[account.account_name] = session_id
        
        # Fusionner
        filtered_conversations_by_account = {
            session_id: convs for session_id, convs in conversations_by_account.items()
            if session_id in self.state['selected_accounts']
        }
        
        all_convs = MessagingService.merge_conversations_from_accounts(
            filtered_conversations_by_account,
            master_account_id=master_account_id if master_account_id in self.state['selected_accounts'] else None,
            account_names=account_names
        )
        
        # Ajouter session_id et s'assurer que account_name est défini
        for conv in all_convs:
            account_name = conv.get('account_name')
            
            # Si account_name n'est pas défini, essayer de le récupérer depuis session_id
            if not account_name:
                session_id = conv.get('session_id')
                if session_id and session_id in account_names:
                    account_name = account_names[session_id]
                    conv['account_name'] = account_name
            
            # Assigner le session_id
            if account_name and account_name in account_names_to_session:
                conv['session_id'] = account_names_to_session[account_name]
            else:
                # Fallback : chercher par session_id si account_name n'est pas trouvé
                conv['session_id'] = account_name if account_name else None
        
        self.state['all_conversations'] = all_convs
        self._apply_filters()
        
        if not hasattr(self, '_is_refreshing'):
            notify(f'{len(all_convs)} conversation(s) chargée(s)', type='positive')
    
    async def _load_messages(self, chat_id: int, account_session_id: str) -> None:
        """Charge les messages d'une conversation."""
        try:
            account = self.telegram_manager.get_account(account_session_id)
            if not account or not account.is_connected:
                notify('Compte non connecté', type='negative')
                return
            
            # Charger seulement 10 messages pour plus de rapidité
            messages = await MessagingService.get_messages(account, chat_id, limit=10)
            
            self.state['messages'] = messages
            self._update_messages_display()
            
            # Faire défiler vers le bas (une seule tentative)
            ui.timer(0.3, lambda: self._scroll_to_bottom(), once=True)
            
            # Marquer comme lu
            await MessagingService.mark_as_read(account, chat_id)
            
        except Exception as e:
            logger.error(f"Erreur chargement messages: {e}")
            notify('Erreur lors du chargement des messages', type='negative')
    
    async def _background_refresh_conversations(self) -> None:
        """Rafraîchit les conversations en arrière-plan sans bloquer l'UI."""
        try:
            # Attendre un peu pour laisser l'UI se charger
            await asyncio.sleep(1)
            
            conversations_by_account = {}
            
            # Charger les conversations en parallèle avec limite réduite
            tasks = []
            accounts_map = {}
            
            for session_id in self.state['selected_accounts']:
                account = self.telegram_manager.get_account(session_id)
                if account and account.is_connected:
                    # Limite encore plus réduite pour le rafraîchissement en arrière-plan
                    limit = 15 if not self.state['show_groups'] else 8
                    task = MessagingService.get_conversations(
                        account, 
                        limit=limit,
                        include_groups=self.state['show_groups']
                    )
                    tasks.append(task)
                    accounts_map[len(tasks) - 1] = session_id
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for idx, result in enumerate(results):
                    if not isinstance(result, Exception):
                        session_id = accounts_map[idx]
                        conversations_by_account[session_id] = result
                
                # Sauvegarder dans le cache
                MessagingService.save_conversations_cache(conversations_by_account)
                
                # Mettre à jour l'affichage si nécessaire
                if conversations_by_account:
                    self._merge_and_display_conversations(conversations_by_account)
                    
        except Exception as e:
            logger.error(f"Erreur rafraîchissement arrière-plan: {e}")
    
    async def _refresh_conversations(self) -> None:
        """Rafraîchit les conversations automatiquement."""
        if self.state['selected_accounts']:
            import time
            current_time = time.time()
            
            # Éviter les rafraîchissements trop fréquents (throttling)
            if current_time - self._last_refresh_time < 30:
                return
            
            self._last_refresh_time = current_time
            self._is_refreshing = True
            await self._load_conversations(force=False)  # Utilise le cache si valide
            self._is_refreshing = False
    
    def _on_search_conversations(self, e) -> None:
        """Filtre les conversations par recherche."""
        self._current_search_text = e.value  # Sauvegarder le texte de recherche
        self._apply_filters()
    
    def _apply_filters(self) -> None:
        """Applique le filtre de recherche aux conversations."""
        search_text = getattr(self, '_current_search_text', '')
        
        # Restaurer le texte de recherche dans l'input si nécessaire
        if search_text and self.search_input:
            self.search_input.value = search_text
        
        # Commencer avec toutes les conversations (déjà filtrées par type au chargement)
        filtered = self.state['all_conversations'].copy()
        
        # Filtrer par recherche
        if search_text:
            filtered = [
                conv for conv in filtered
                if search_text.lower() in conv['title'].lower()
            ]
        
        self.state['filtered_conversations'] = filtered
        
        # Garder la conversation sélectionnée si elle est toujours visible
        if self.state.get('selected_conversation'):
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
    
    async def _handle_keydown(self, e) -> None:
        """Gère l'envoi de message avec la touche Entrée (Shift+Entrée pour nouvelle ligne)."""
        # Si Shift est pressé, laisser le comportement par défaut (nouvelle ligne)
        if e.args.get('shiftKey', False):
            return
        
        # Vérifications de base
        if not self.state['selected_conversation']:
            notify('Sélectionnez une conversation', type='warning')
            return
        
        if not self.message_input.value or not self.message_input.value.strip():
            notify('Le message ne peut pas être vide', type='warning')
            return
        
        message = self.message_input.value.strip()
        
        # Vider immédiatement pour éviter les doublons
        self.message_input.value = ''
        
        # Trouver le compte
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
        try:
            success = await MessagingService.send_message(
                account,
                conv['entity_id'],
                message
            )
            
            if success:
                notify('Message envoyé', type='positive')
                self._add_sent_message_to_display(message)
                await self._load_messages(conv['entity_id'], account_session_id)
            else:
                notify('Erreur lors de l\'envoi', type='negative')
        except Exception as ex:
            logger.error(f"Erreur envoi message: {ex}")
            notify('Erreur lors de l\'envoi', type='negative')
    
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

