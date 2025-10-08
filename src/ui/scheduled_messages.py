"""
Widget pour gérer les messages programmés sur Telegram
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
import asyncio
from datetime import datetime
from ui.searchable_combobox import SearchableComboBox


class ScheduledMessagesWidget(QWidget):
    """Widget pour voir et gérer les messages programmés sur Telegram"""
    
    def __init__(self, telegram_manager):
        super().__init__()
        self.telegram_manager = telegram_manager
        self.current_account = None
        self.current_chat = None
        self.scheduled_messages = []
        self._loading_chats = False
        self._scan_in_progress = False
        self._scan_task = None
        self._cached_groups = {}  # Cache : {account_id: [(group_data, timestamp)]}
        self._cache_duration = 30  # Cache valide pendant 30 secondes (plus long)
        self._showing_all_groups = False  # Mode "tous les groupes"
        self._all_messages = []  # Messages de tous les groupes
        
        self.init_ui()
    
    def init_ui(self):
        """Initialise l'interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel("📅 Messages Programmés sur Telegram")
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Actualiser Tout")
        refresh_btn.clicked.connect(self._refresh_all)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Sélecteurs
        selectors_layout = QHBoxLayout()
        
        # Compte
        selectors_layout.addWidget(QLabel("Compte :"))
        self.account_combo = SearchableComboBox()
        self.account_combo.currentIndexChanged.connect(self._on_account_changed)
        selectors_layout.addWidget(self.account_combo, 1)
        
        # Groupe
        selectors_layout.addWidget(QLabel("Groupe :"))
        self.chat_combo = SearchableComboBox()
        self.chat_combo.currentIndexChanged.connect(self._on_chat_changed)
        selectors_layout.addWidget(self.chat_combo, 1)
        
        # Bouton "Tous les groupes"
        all_groups_btn = QPushButton("🌐 Tous les groupes")
        all_groups_btn.clicked.connect(self._show_all_groups)
        selectors_layout.addWidget(all_groups_btn)
        
        layout.addLayout(selectors_layout)
        
        # Table des messages
        self.messages_table = QTableWidget()
        self.messages_table.setColumnCount(6)
        self.messages_table.setHorizontalHeaderLabels([
            "📅 Date/Heure", "👥 Groupe", "📝 Message", "📎 Média", "🆔 ID", "Actions"
        ])
        
        header = self.messages_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Date/Heure
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Groupe
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)          # Message
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Média
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # ID
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)            # Actions
        self.messages_table.setColumnWidth(4, 150)
        
        self.messages_table.setAlternatingRowColors(True)
        self.messages_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        layout.addWidget(self.messages_table)
        
        # Boutons d'action groupée
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        delete_selected_btn = QPushButton("🗑️ Supprimer sélection")
        delete_selected_btn.clicked.connect(self._delete_selected)
        actions_layout.addWidget(delete_selected_btn)
        
        delete_all_btn = QPushButton("🗑️ Tout supprimer")
        delete_all_btn.setProperty("class", "danger")
        delete_all_btn.clicked.connect(self._delete_all)
        actions_layout.addWidget(delete_all_btn)
        
        layout.addLayout(actions_layout)
    
    def refresh_accounts(self):
        """Rafraîchit la liste des comptes"""
        # Ne rafraîchir que si la liste est vide (éviter les rechargements)
        if self.account_combo.count() > 0:
            return
        
        self.account_combo.clear()
        
        accounts = self.telegram_manager.list_accounts()
        connected_accounts = [acc for acc in accounts if acc["is_connected"]]
        
        if not connected_accounts:
            self.account_combo.addItem("Aucun compte connecté")
            return
        
        for account in connected_accounts:
            self.account_combo.addItem(
                f"{account['account_name']} ({account['phone']})",
                account["session_id"]
            )
    
    def _on_account_changed(self, index):
        """Appelé quand le compte change"""
        if index < 0 or self._loading_chats or self._scan_in_progress:
            return
        
        session_id = self.account_combo.itemData(index)
        if not session_id:
            return
        
        self.current_account = self.telegram_manager.accounts.get(session_id)
        
        # Charger les groupes (une seule fois)
        self._loading_chats = True
        QTimer.singleShot(0, lambda: asyncio.create_task(self._load_chats()))
    
    async def _load_chats(self):
        """Charge les groupes avec messages programmés (avec cache intelligent)"""
        if not self.current_account:
            return
        
        account_id = id(self.current_account)
        current_time = asyncio.get_event_loop().time()
        
        # Vérifier le cache
        if account_id in self._cached_groups:
            cached_data, cache_time = self._cached_groups[account_id]
            age = current_time - cache_time
            
            if age < self._cache_duration:
                # Cache encore valide ! Utiliser directement
                print(f"⚡ Utilisation du cache ({int(self._cache_duration - age)}s restantes)")
                self._display_cached_results(cached_data)
                self._scan_in_progress = False
                self._loading_chats = False
                return
        
        # Cache expiré ou pas de cache → scanner
        print("🔍 Scan complet (cache expiré ou inexistant)")
        
        # Annuler le scan précédent si en cours
        if self._scan_task and not self._scan_task.done():
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
            await asyncio.sleep(0.5)
        
        if self._scan_in_progress:
            return
        
        try:
            self._scan_in_progress = True
            
            self.chat_combo.clear()
            self.chat_combo.addItem("🔄 Recherche des groupes avec messages...")
            
            # Assurer la connexion
            if not self.current_account.client.is_connected():
                await self.current_account.client.connect()
            
            # Récupérer tous les dialogues
            dialogs = await self.current_account.get_dialogs()
            print(f"📋 {len(dialogs)} dialogues à scanner")
            
            # Lancer le scan en arrière-plan
            self._scan_task = asyncio.create_task(self._scan_for_scheduled(dialogs))
        
        except Exception as e:
            print(f"❌ Erreur load_chats: {e}")
            self.chat_combo.clear()
            self.chat_combo.addItem(f"❌ Erreur: {str(e)[:30]}", None)
            self._scan_in_progress = False
    
    def _display_cached_results(self, groups_with_messages):
        """Affiche les résultats depuis le cache (instantané)"""
        self.chat_combo.clear()
        self.chat_combo.addItem("-- Sélectionner un groupe --", None)
        
        if not groups_with_messages:
            self.chat_combo.addItem("✅ Aucun message programmé", None)
        else:
            for group in groups_with_messages:
                self.chat_combo.addItem(
                    f"{group['title']} ({group['count']} msg)",
                    group["id"]
                )
    
    async def _scan_for_scheduled(self, dialogs):
        """Scanne les groupes séquentiellement (fiabilité maximale)"""
        groups_with_messages = []
        start_time = asyncio.get_event_loop().time()
        
        try:
            total = len(dialogs)
            
            for i, dialog in enumerate(dialogs):
                # Mettre à jour l'UI tous les 5 groupes
                if self.chat_combo.count() > 0 and i % 5 == 0:
                    elapsed = asyncio.get_event_loop().time() - start_time
                    self.chat_combo.setItemText(0, f"🔍 Scan... {i+1}/{total} ({elapsed:.0f}s)")
                
                # Vérifier ce groupe
                count = await self._check_group(dialog)
                
                if count > 0:
                    print(f"✅ {dialog['title']}: {count} messages")
                    groups_with_messages.append({
                        "title": dialog["title"],
                        "id": dialog["id"],
                        "count": count
                    })
                
                # Micro-pause pour laisser respirer l'UI
                if i % 10 == 0:
                    await asyncio.sleep(0.05)
            
            print(f"📊 Total trouvé: {len(groups_with_messages)} groupes avec messages")
            
            # Sauvegarder dans le cache
            account_id = id(self.current_account)
            cache_time = asyncio.get_event_loop().time()
            self._cached_groups[account_id] = (groups_with_messages, cache_time)
            print(f"💾 Résultats mis en cache pour {self._cache_duration}s")
            
            # Mettre à jour le combo avec les résultats
            self._display_cached_results(groups_with_messages)
        
        except asyncio.CancelledError:
            print("⚠️ Scan annulé")
            self.chat_combo.clear()
            self.chat_combo.addItem("-- Sélectionner un groupe --", None)
        except Exception as e:
            print(f"❌ Erreur scan: {e}")
            self.chat_combo.clear()
            self.chat_combo.addItem(f"❌ Erreur: {str(e)[:30]}", None)
        finally:
            self._scan_in_progress = False
            self._loading_chats = False
    
    async def _check_group(self, dialog):
        """Vérifie un groupe individuel - ULTRA RAPIDE"""
        try:
            # Timeout ultra court pour la vitesse maximale
            scheduled = await asyncio.wait_for(
                self.current_account.client.get_messages(
                    dialog["id"],
                    scheduled=True,
                    limit=100
                ),
                timeout=1.0  # 1 seconde seulement !
            )
            count = len(scheduled) if scheduled else 0
            return count
                
        except asyncio.TimeoutError:
            # Timeout → pas de messages
            return 0
                    
        except asyncio.CancelledError:
            raise
                
        except Exception:
            # Erreur de permissions ou autre → pas de messages
            return 0
    
    
    def _on_chat_changed(self, index):
        """Appelé quand le groupe change"""
        if index <= 0:
            return
        
        chat_id = self.chat_combo.itemData(index)
        if not chat_id:
            return
        
        self.current_chat = chat_id
        self._showing_all_groups = False  # Retour au mode groupe unique
        self._load_scheduled_messages()
    
    def _show_all_groups(self):
        """Affiche tous les messages de tous les groupes"""
        if not self.current_account:
            QMessageBox.warning(
                self,
                "Attention",
                "Veuillez sélectionner un compte"
            )
            return
        
        self._showing_all_groups = True
        QTimer.singleShot(0, lambda: asyncio.create_task(self._load_all_messages()))
    
    async def _load_all_messages(self):
        """Charge tous les messages de tous les groupes"""
        try:
            if not self.current_account or not self.current_account.client:
                return
            
            # Afficher le loading
            self.messages_table.setRowCount(1)
            loading_item = QTableWidgetItem("🔄 Chargement de tous les messages...")
            loading_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.messages_table.setItem(0, 0, loading_item)
            self.messages_table.setSpan(0, 0, 1, 6)
            
            # Récupérer tous les groupes avec messages
            account_id = id(self.current_account)
            if account_id in self._cached_groups:
                groups_data, cache_time = self._cached_groups[account_id]
                current_time = asyncio.get_event_loop().time()
                age = current_time - cache_time
                
                if age < self._cache_duration:
                    # Utiliser le cache
                    groups_with_messages = groups_data
                else:
                    # Cache expiré, recharger
                    dialogs = await self.current_account.get_dialogs()
                    groups_with_messages = await self._scan_for_scheduled_groups(dialogs)
            else:
                # Pas de cache, charger
                dialogs = await self.current_account.get_dialogs()
                groups_with_messages = await self._scan_for_scheduled_groups(dialogs)
            
            # Charger les messages de chaque groupe EN PARALLÈLE
            all_messages = []
            
            async def load_group_messages(group):
                try:
                    messages = await self.current_account.client.get_messages(
                        group["id"],
                        scheduled=True,
                        limit=100
                    )
                    
                    for msg in messages:
                        # Ajouter le nom du groupe à chaque message
                        msg.group_name = group["title"]
                        msg.group_id = group["id"]
                    
                    return messages
                        
                except Exception as e:
                    print(f"⚠️ Erreur chargement messages {group['title']}: {e}")
                    return []
            
            # Lancer tous les chargements en parallèle
            print(f"🚀 Chargement parallèle de {len(groups_with_messages)} groupes...")
            results = await asyncio.gather(*[load_group_messages(group) for group in groups_with_messages], return_exceptions=True)
            
            # Collecter tous les messages
            for messages in results:
                if isinstance(messages, list):
                    all_messages.extend(messages)
            
            # Trier par date
            all_messages.sort(key=lambda x: x.date if x.date else datetime.min)
            
            self._all_messages = all_messages
            self._display_messages()
            
        except Exception as e:
            print(f"❌ Erreur load_all_messages: {e}")
            self.messages_table.setRowCount(1)
            error_item = QTableWidgetItem(f"❌ Erreur: {str(e)[:50]}")
            error_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.messages_table.setItem(0, 0, error_item)
            self.messages_table.setSpan(0, 0, 1, 6)
    
    async def _scan_for_scheduled_groups(self, dialogs):
        """Version ULTRA RAPIDE du scan pour récupérer les groupes avec messages"""
        groups_with_messages = []
        
        # Traiter TOUS les groupes en parallèle pour la vitesse maximale
        async def check_group_fast(dialog):
            try:
                count = await self._check_group(dialog)
                if count > 0:
                    return {
                        "title": dialog["title"],
                        "id": dialog["id"],
                        "count": count
                    }
                return None
            except Exception:
                return None
        
        # Lancer tous les checks en parallèle
        print(f"🚀 Scan ULTRA RAPIDE de {len(dialogs)} groupes en parallèle...")
        results = await asyncio.gather(*[check_group_fast(dialog) for dialog in dialogs], return_exceptions=True)
        
        # Collecter les résultats
        for result in results:
            if isinstance(result, dict):
                groups_with_messages.append(result)
        
        return groups_with_messages
    
    def _refresh_all(self):
        """Actualise tout : groupes + messages"""
        if not self.current_account:
            QMessageBox.warning(
                self,
                "Attention",
                "Veuillez sélectionner un compte"
            )
            return
        
        # Vérifier si un scan est en cours
        if self._scan_in_progress:
            QMessageBox.warning(
                self,
                "Analyse en cours",
                "Une analyse est déjà en cours.\nVeuillez patienter qu'elle se termine."
            )
            return
        
        # Débloquer le chargement pour permettre le refresh
        self._loading_chats = False
        
        # Recharger les groupes
        QTimer.singleShot(0, lambda: asyncio.create_task(self._load_chats()))
    
    def _load_scheduled_messages(self):
        """Charge les messages programmés"""
        if not self.current_account or not self.current_chat:
            QMessageBox.warning(
                self,
                "Attention",
                "Veuillez sélectionner un compte et un groupe"
            )
            return
        
        QTimer.singleShot(0, lambda: asyncio.create_task(self._fetch_scheduled()))
    
    async def _fetch_scheduled(self):
        """Récupère les messages programmés depuis Telegram"""
        try:
            if not self.current_account or not self.current_account.client:
                return
            
            # Récupérer les messages programmés
            scheduled = await self.current_account.client.get_messages(
                self.current_chat,
                scheduled=True,
                limit=100
            )
            
            self.scheduled_messages = scheduled
            self._display_messages()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de charger les messages programmés :\n{e}"
            )
    
    def _display_messages(self):
        """Affiche les messages dans la table"""
        # Choisir la source des messages
        if self._showing_all_groups:
            messages_to_show = self._all_messages
            print(f"DEBUG: Affichage de {len(messages_to_show)} messages (TOUS LES GROUPES)")
        else:
            messages_to_show = self.scheduled_messages
            print(f"DEBUG: Affichage de {len(messages_to_show)} messages (GROUPE UNIQUE)")
        
        # Vider complètement le tableau
        self.messages_table.clear()
        self.messages_table.setRowCount(0)
        
        if len(messages_to_show) == 0:
            self.messages_table.setRowCount(1)
            empty_text = "✅ Aucun message programmé" if not self._showing_all_groups else "✅ Aucun message programmé dans tous les groupes"
            empty_item = QTableWidgetItem(empty_text)
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.messages_table.setItem(0, 0, empty_item)
            self.messages_table.setSpan(0, 0, 1, 6)
            return
        
        # Afficher tous les messages
        self.messages_table.setRowCount(len(messages_to_show))
        
        for row, msg in enumerate(messages_to_show):
            # Date/Heure
            if msg.date:
                date_str = msg.date.strftime("%d/%m/%Y %H:%M")
            else:
                date_str = "Inconnue"
            date_item = QTableWidgetItem(date_str)
            self.messages_table.setItem(row, 0, date_item)
            
            # Groupe (seulement en mode "tous les groupes")
            if self._showing_all_groups and hasattr(msg, 'group_name'):
                group_item = QTableWidgetItem(msg.group_name)
                self.messages_table.setItem(row, 1, group_item)
                col_offset = 1
            else:
                col_offset = 0
            
            # Message
            message_text = msg.message[:80] + "..." if msg.message and len(msg.message) > 80 else (msg.message or "[Vide]")
            message_item = QTableWidgetItem(message_text)
            if msg.message:
                message_item.setToolTip(msg.message)
            self.messages_table.setItem(row, 1 + col_offset, message_item)
            
            # Média
            media_text = "✅" if msg.media else "❌"
            media_item = QTableWidgetItem(media_text)
            media_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.messages_table.setItem(row, 2 + col_offset, media_item)
            
            # ID
            id_item = QTableWidgetItem(str(msg.id))
            self.messages_table.setItem(row, 3 + col_offset, id_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 2, 5, 2)
            actions_layout.setSpacing(5)
            
            delete_btn = QPushButton("🗑️")
            delete_btn.setMaximumWidth(40)
            delete_btn.setToolTip("Supprimer ce message")
            delete_btn.clicked.connect(lambda checked, m=msg: self._delete_message(m))
            actions_layout.addWidget(delete_btn)
            
            self.messages_table.setCellWidget(row, 4 + col_offset, actions_widget)
        
        # Forcer la mise à jour du tableau
        self.messages_table.update()
        self.messages_table.repaint()
        # Tableau mis à jour
    
    def _delete_message(self, message):
        """Supprime un message spécifique"""
        group_info = ""
        if self._showing_all_groups and hasattr(message, 'group_name'):
            group_info = f"\nGroupe: {message.group_name}"
        
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Supprimer ce message programmé ?{group_info}\n\n{message.message[:100] if message.message else '[Vide]'}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Déterminer le chat_id pour la suppression
            if self._showing_all_groups and hasattr(message, 'group_id'):
                chat_id = message.group_id
            else:
                chat_id = self.current_chat
            
            QTimer.singleShot(0, lambda: asyncio.create_task(self._do_delete([message.id], chat_id)))
    
    def _delete_selected(self):
        """Supprime les messages sélectionnés"""
        selected_rows = set(item.row() for item in self.messages_table.selectedItems())
        
        if not selected_rows:
            QMessageBox.warning(self, "Attention", "Aucun message sélectionné")
            return
        
        # Choisir la source des messages selon le mode
        if self._showing_all_groups:
            messages_source = self._all_messages
        else:
            messages_source = self.scheduled_messages
        
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Supprimer {len(selected_rows)} message(s) programmé(s) ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self._showing_all_groups:
                # Mode "tous les groupes" : supprimer par groupe
                QTimer.singleShot(0, lambda: asyncio.create_task(self._delete_selected_from_all_groups(selected_rows)))
            else:
                # Mode groupe unique : suppression normale
                message_ids = [messages_source[row].id for row in selected_rows]
                QTimer.singleShot(0, lambda: asyncio.create_task(self._do_delete(message_ids)))
    
    async def _delete_selected_from_all_groups(self, selected_rows):
        """Supprime les messages sélectionnés de tous les groupes"""
        try:
            # Grouper les messages sélectionnés par chat_id
            messages_by_chat = {}
            for row in selected_rows:
                if row < len(self._all_messages):
                    msg = self._all_messages[row]
                    if hasattr(msg, 'group_id'):
                        chat_id = msg.group_id
                        if chat_id not in messages_by_chat:
                            messages_by_chat[chat_id] = []
                        messages_by_chat[chat_id].append(msg)
            
            print(f"DEBUG: Suppression sélectionnée de {len(messages_by_chat)} groupes")
            
            # Supprimer par groupe
            for chat_id, messages in messages_by_chat.items():
                message_ids = [msg.id for msg in messages]
                group_name = messages[0].group_name if hasattr(messages[0], 'group_name') else f"Chat {chat_id}"
                
                print(f"DEBUG: Suppression de {len(message_ids)} messages sélectionnés dans {group_name}")
                
                try:
                    # skip_reload=True pour éviter de recharger à chaque groupe
                    await self._do_delete(message_ids, chat_id, skip_reload=True)
                except Exception as e:
                    print(f"⚠️ Erreur suppression sélectionnée groupe {group_name}: {e}")
                    continue
            
            # Recharger la liste complète une seule fois à la fin
            print(f"DEBUG: Rechargement final des messages sélectionnés...")
            await self._load_all_messages()
            print(f"DEBUG: Rechargement terminé")
            
        except Exception as e:
            print(f"❌ Erreur delete_selected_from_all_groups: {e}")
            import traceback
            traceback.print_exc()
    
    def _delete_all(self):
        """Supprime tous les messages programmés"""
        # Choisir la source des messages selon le mode
        if self._showing_all_groups:
            messages_to_delete = self._all_messages
            mode_text = "TOUS LES GROUPES"
        else:
            messages_to_delete = self.scheduled_messages
            mode_text = "ce groupe"
        
        if not messages_to_delete:
            QMessageBox.warning(self, "Attention", "Aucun message à supprimer")
            return
        
        reply = QMessageBox.question(
            self,
            "⚠️ CONFIRMER",
            f"⚠️ ATTENTION\n\n"
            f"Supprimer TOUS les {len(messages_to_delete)} message(s) programmé(s) dans {mode_text} ?\n\n"
            f"Cette action est irréversible !",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self._showing_all_groups:
                # Mode "tous les groupes" : supprimer par groupe
                QTimer.singleShot(0, lambda: asyncio.create_task(self._delete_all_from_all_groups()))
            else:
                # Mode groupe unique : suppression normale
                message_ids = [msg.id for msg in messages_to_delete]
                QTimer.singleShot(0, lambda: asyncio.create_task(self._do_delete(message_ids)))
    
    async def _delete_all_from_all_groups(self):
        """Supprime tous les messages de tous les groupes (optimisé)"""
        try:
            # Afficher le loading
            self.messages_table.setRowCount(1)
            loading_item = QTableWidgetItem("🗑️ Suppression en cours...")
            loading_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.messages_table.setItem(0, 0, loading_item)
            self.messages_table.setSpan(0, 0, 1, 6)
            
            # Grouper les messages par chat_id
            messages_by_chat = {}
            for msg in self._all_messages:
                if hasattr(msg, 'group_id'):
                    chat_id = msg.group_id
                    if chat_id not in messages_by_chat:
                        messages_by_chat[chat_id] = []
                    messages_by_chat[chat_id].append(msg)
            
            print(f"🚀 SUPPRESSION RAPIDE de {len(messages_by_chat)} groupes")
            
            # Supprimer TOUS les groupes en parallèle
            async def delete_group_messages(chat_id, messages):
                message_ids = [msg.id for msg in messages]
                group_name = messages[0].group_name if hasattr(messages[0], 'group_name') else f"Chat {chat_id}"
                
                try:
                    await self._do_delete(message_ids, chat_id, skip_reload=True)
                    print(f"✅ Supprimé {len(message_ids)} messages dans {group_name}")
                    return True, group_name
                except Exception as e:
                    print(f"⚠️ Erreur suppression groupe {group_name}: {e}")
                    return False, group_name
            
            # Lancer toutes les suppressions en parallèle
            tasks = [delete_group_messages(chat_id, messages) for chat_id, messages in messages_by_chat.items()]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Compter les résultats
            success_count = sum(1 for result in results if isinstance(result, tuple) and result[0])
            failed_count = len(results) - success_count
            
            print(f"🚀 SUPPRESSION TERMINÉE: {success_count} groupes réussis, {failed_count} échecs")
            
            # Recharger la liste complète
            await self._load_all_messages()
            
        except Exception as e:
            print(f"❌ Erreur delete_all_from_all_groups: {e}")
            import traceback
            traceback.print_exc()
    
    async def _do_delete(self, message_ids, chat_id=None, skip_reload=False):
        """Effectue la suppression"""
        try:
            if chat_id is None:
                chat_id = self.current_chat
            
            print(f"DEBUG: Tentative de suppression de {len(message_ids)} message(s) PROGRAMMÉS dans chat {chat_id}")
            
            # S'assurer que le client est connecté
            if not self.current_account.client.is_connected():
                await self.current_account.client.connect()
            
            # Pour les messages PROGRAMMÉS, utiliser DeleteScheduledMessagesRequest
            from telethon.tl.functions.messages import DeleteScheduledMessagesRequest
            
            result = await self.current_account.client(DeleteScheduledMessagesRequest(
                peer=chat_id,
                id=message_ids
            ))
            
            print(f"DEBUG: Résultat suppression: {result}")
            
            # Recharger seulement si pas en mode batch
            if not skip_reload:
                print(f"DEBUG: Rechargement de la liste...")
                if self._showing_all_groups:
                    await self._load_all_messages()
                else:
                    await self._fetch_scheduled()
                print(f"DEBUG: Liste rechargée")
            
        except Exception as e:
            print(f"DEBUG: Erreur suppression: {e}")
            import traceback
            traceback.print_exc()

