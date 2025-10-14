"""
Base de données SQLite locale pour stocker conversations, messages et métadonnées.
Inspiré de l'architecture de Telegram officiel pour des performances optimales.
"""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

from utils.logger import get_logger

logger = get_logger()


class TelegramDatabase:
    """
    Base de données locale pour stocker toutes les données Telegram.
    
    Architecture similaire au vrai Telegram :
    - Stockage permanent des conversations
    - Historique complet des messages
    - Cache des photos de profil
    - Métadonnées optimisées pour recherche rapide
    """
    
    def __init__(self, db_path: str = "temp/telegram.db"):
        """
        Initialise la base de données.
        
        Args:
            db_path: Chemin vers le fichier de base de données
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Connexion avec optimisations SQLite
        self.conn = sqlite3.connect(
            str(self.db_path),
            check_same_thread=False,  # Pour utilisation async
            timeout=30.0  # Timeout de 30 secondes pour éviter "database is locked"
        )
        
        # Optimisations SQLite
        self.conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        self.conn.execute("PRAGMA synchronous=NORMAL")  # Performance vs sécurité
        self.conn.execute("PRAGMA temp_store=MEMORY")  # Temp en mémoire
        self.conn.execute("PRAGMA mmap_size=30000000000")  # Memory-mapped I/O
        
        self.conn.row_factory = sqlite3.Row  # Accès par nom de colonne
        
        self._create_tables()
        self._create_indexes()
        
        logger.info(f"Base de données initialisée : {self.db_path}")
    
    @contextmanager
    def transaction(self):
        """Context manager pour transactions."""
        cursor = self.conn.cursor()
        try:
            cursor.execute("BEGIN")
            yield cursor
            cursor.execute("COMMIT")
        except Exception:
            cursor.execute("ROLLBACK")
            raise
        finally:
            cursor.close()
    
    def _create_tables(self):
        """Crée les tables nécessaires."""
        
        # Table des conversations
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                entity_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                title TEXT NOT NULL,
                type TEXT NOT NULL,
                username TEXT,
                last_message TEXT,
                last_message_date TIMESTAMP,
                last_message_from_me BOOLEAN DEFAULT 0,
                unread_count INTEGER DEFAULT 0,
                pinned BOOLEAN DEFAULT 0,
                archived BOOLEAN DEFAULT 0,
                profile_photo_path TEXT,
                has_photo BOOLEAN DEFAULT 0,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (entity_id, session_id)
            )
        """)
        
        # Table des messages
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                session_id TEXT NOT NULL,
                text TEXT,
                sender_id INTEGER,
                sender_name TEXT,
                date TIMESTAMP NOT NULL,
                from_me BOOLEAN DEFAULT 0,
                has_media BOOLEAN DEFAULT 0,
                media_type TEXT,
                media_path TEXT,
                media_caption TEXT,
                reply_to INTEGER,
                edited BOOLEAN DEFAULT 0,
                views INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (id, chat_id, session_id),
                FOREIGN KEY (chat_id, session_id) REFERENCES conversations(entity_id, session_id)
            )
        """)
        
        # Table des photos de profil (cache)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS profile_photos (
                entity_id INTEGER PRIMARY KEY,
                photo_path TEXT NOT NULL,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table des métadonnées (pour tracking)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        logger.debug("Tables créées avec succès")
    
    def _create_indexes(self):
        """Crée les index pour optimiser les performances."""
        
        # Index pour conversations
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_session 
            ON conversations(session_id)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_type 
            ON conversations(type)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_date 
            ON conversations(last_message_date DESC)
        """)
        
        # Index pour messages
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_chat 
            ON messages(chat_id, session_id, date DESC)
        """)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_date 
            ON messages(date DESC)
        """)
        
        # Index pour recherche full-text (titre de conversation)
        self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_conversations_title 
            ON conversations(title COLLATE NOCASE)
        """)
        
        self.conn.commit()
        logger.debug("Index créés avec succès")
    
    # ==================== CONVERSATIONS ====================
    
    def save_conversations(self, session_id: str, conversations: List[Dict]) -> int:
        """
        Sauvegarde ou met à jour les conversations.
        
        Args:
            session_id: ID de la session
            conversations: Liste des conversations à sauvegarder
            
        Returns:
            int: Nombre de conversations sauvegardées
        """
        if not conversations:
            return 0
        
        count = 0
        
        for conv in conversations:
            try:
                # Convertir datetime en string ISO pour SQLite
                last_msg_date = conv.get('last_message_date')
                if last_msg_date and isinstance(last_msg_date, datetime):
                    last_msg_date = last_msg_date.isoformat()
                
                self.conn.execute("""
                    INSERT OR REPLACE INTO conversations (
                        entity_id, session_id, title, type, username,
                        last_message, last_message_date, last_message_from_me,
                        unread_count, pinned, archived,
                        profile_photo_path, has_photo, phone, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    conv['entity_id'],
                    session_id,
                    conv.get('title', 'Sans nom'),
                    conv.get('type', 'user'),
                    conv.get('username'),
                    conv.get('last_message', ''),
                    last_msg_date,
                    conv.get('last_message_from_me', False),
                    conv.get('unread_count', 0),
                    conv.get('pinned', False),
                    conv.get('archived', False),
                    conv.get('profile_photo'),
                    conv.get('has_photo', False),
                    conv.get('phone')
                ))
                count += 1
            except Exception as e:
                logger.error(f"Erreur sauvegarde conversation {conv.get('title')}: {e}")
        
        self.conn.commit()
        logger.debug(f"Sauvegardé {count} conversations pour session {session_id}")
        return count
    
    def get_conversations(
        self,
        session_ids: List[str],
        include_groups: bool = False,
        limit: Optional[int] = None
    ) -> List[Dict]:
        """
        Récupère les conversations depuis la base de données.
        
        Charge aussi les photos de profil depuis le cache si disponibles.
        
        Args:
            session_ids: Liste des IDs de session
            include_groups: Inclure les groupes/canaux
            limit: Limite de résultats
            
        Returns:
            List[Dict]: Liste des conversations avec photos
        """
        if not session_ids:
            return []
        
        # Validation de limit pour éviter les injections SQL
        if limit is not None:
            if not isinstance(limit, int) or limit < 0:
                logger.warning(f"Limite invalide ignorée: {limit}")
                limit = None
        
        # Construire la requête avec LEFT JOIN sur profile_photos
        placeholders = ','.join('?' * len(session_ids))
        
        query = f"""
            SELECT 
                c.entity_id, c.session_id, c.title, c.type, c.username,
                c.last_message, c.last_message_date, c.last_message_from_me,
                c.unread_count, c.pinned, c.archived,
                c.profile_photo_path, c.has_photo, c.phone,
                p.photo_path as cached_photo_path
            FROM conversations c
            LEFT JOIN profile_photos p ON c.entity_id = p.entity_id
            WHERE c.session_id IN ({placeholders})
        """
        
        params = list(session_ids)
        
        # Filtrer par type si nécessaire (sécurisé avec paramètre)
        if not include_groups:
            query += " AND c.type = ?"
            params.append('user')
        
        # Tri par date
        query += " ORDER BY c.last_message_date DESC"
        
        # Limite (sécurisé avec paramètre)
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()
        
        conversations = []
        for row in rows:
            # Convertir Row en dict
            conv = dict(row)
            
            # Convertir les dates ISO en datetime
            if conv.get('last_message_date'):
                try:
                    conv['last_message_date'] = datetime.fromisoformat(conv['last_message_date'])
                except:
                    conv['last_message_date'] = None
            
            # Utiliser le cache de photo en priorité
            cached_photo = conv.pop('cached_photo_path', None)
            db_photo = conv.pop('profile_photo_path', None)
            
            # Priorité : cache > db_photo
            photo_path = cached_photo or db_photo
            
            # Vérifier que le fichier existe vraiment
            if photo_path:
                import os
                if os.path.exists(photo_path):
                    conv['profile_photo'] = photo_path
                    conv['has_photo'] = True
                else:
                    conv['profile_photo'] = None
                    conv['has_photo'] = False
            else:
                conv['profile_photo'] = None
            
            conversations.append(conv)
        
        logger.debug(f"Récupéré {len(conversations)} conversations depuis DB (avec photos)")
        return conversations
    
    def get_conversation_by_id(self, entity_id: int, session_id: str) -> Optional[Dict]:
        """
        Récupère une conversation spécifique.
        
        Args:
            entity_id: ID de l'entité
            session_id: ID de la session
            
        Returns:
            Optional[Dict]: Conversation ou None
        """
        cursor = self.conn.execute("""
            SELECT 
                entity_id, session_id, title, type, username,
                last_message, last_message_date, last_message_from_me,
                unread_count, pinned, archived,
                profile_photo_path, has_photo, phone
            FROM conversations
            WHERE entity_id = ? AND session_id = ?
        """, (entity_id, session_id))
        
        row = cursor.fetchone()
        if not row:
            return None
        
        conv = dict(row)
        
        # Convertir date
        if conv.get('last_message_date'):
            try:
                conv['last_message_date'] = datetime.fromisoformat(conv['last_message_date'])
            except:
                conv['last_message_date'] = None
        
        conv['profile_photo'] = conv.pop('profile_photo_path', None)
        return conv
    
    def update_conversation_last_message(
        self,
        entity_id: int,
        session_id: str,
        message_text: str,
        message_date: datetime,
        from_me: bool = False
    ):
        """
        Met à jour le dernier message d'une conversation.
        
        Args:
            entity_id: ID de l'entité
            session_id: ID de la session
            message_text: Texte du message
            message_date: Date du message
            from_me: Message envoyé par moi
        """
        self.conn.execute("""
            UPDATE conversations
            SET last_message = ?,
                last_message_date = ?,
                last_message_from_me = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE entity_id = ? AND session_id = ?
        """, (message_text, message_date.isoformat(), from_me, entity_id, session_id))
    
    # ==================== MESSAGES ====================
    
    def save_messages(self, session_id: str, chat_id: int, messages: List[Dict]) -> int:
        """
        Sauvegarde les messages d'une conversation.
        
        Args:
            session_id: ID de la session
            chat_id: ID du chat
            messages: Liste des messages
            
        Returns:
            int: Nombre de messages sauvegardés
        """
        if not messages:
            return 0
        
        count = 0
        
        for msg in messages:
            try:
                # Convertir datetime
                msg_date = msg.get('date')
                if msg_date and isinstance(msg_date, datetime):
                    msg_date = msg_date.isoformat()
                
                self.conn.execute("""
                    INSERT OR REPLACE INTO messages (
                        id, chat_id, session_id, text, sender_id, sender_name,
                        date, from_me, has_media, media_type, media_path,
                        media_caption, reply_to, edited, views
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    msg['id'],
                    chat_id,
                    session_id,
                    msg.get('text', ''),
                    msg.get('sender_id'),
                    msg.get('sender_name', 'Inconnu'),
                    msg_date,
                    msg.get('from_me', False),
                    msg.get('has_media', False),
                    msg.get('media_type'),
                    msg.get('media_data'),  # media_path dans la DB
                    msg.get('media_caption', ''),
                    msg.get('reply_to'),
                    msg.get('edited', False),
                    msg.get('views')
                ))
                count += 1
            except Exception as e:
                logger.error(f"Erreur sauvegarde message {msg.get('id')}: {e}")
        
        self.conn.commit()
        logger.debug(f"Sauvegardé {count} messages pour chat {chat_id}")
        return count
    
    def get_messages(
        self,
        chat_id: int,
        session_id: str,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """
        Récupère les messages d'une conversation.
        
        Args:
            chat_id: ID du chat
            session_id: ID de la session
            limit: Nombre maximum de messages
            offset: Décalage pour pagination
            
        Returns:
            List[Dict]: Liste des messages
        """
        cursor = self.conn.execute("""
            SELECT 
                id, text, sender_id, sender_name, date, from_me,
                has_media, media_type, media_path, media_caption,
                reply_to, edited, views
            FROM messages
            WHERE chat_id = ? AND session_id = ?
            ORDER BY date ASC
            LIMIT ? OFFSET ?
        """, (chat_id, session_id, limit, offset))
        
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            msg = dict(row)
            
            # Convertir date
            if msg.get('date'):
                try:
                    msg['date'] = datetime.fromisoformat(msg['date'])
                except:
                    msg['date'] = None
            
            # Renommer media_path en media_data pour compatibilité
            msg['media_data'] = msg.pop('media_path', None)
            
            messages.append(msg)
        
        logger.debug(f"Récupéré {len(messages)} messages pour chat {chat_id}")
        return messages
    
    def get_message_count(self, chat_id: int, session_id: str) -> int:
        """
        Compte le nombre de messages d'une conversation.
        
        Args:
            chat_id: ID du chat
            session_id: ID de la session
            
        Returns:
            int: Nombre de messages
        """
        cursor = self.conn.execute("""
            SELECT COUNT(*) FROM messages
            WHERE chat_id = ? AND session_id = ?
        """, (chat_id, session_id))
        
        return cursor.fetchone()[0]
    
    # ==================== PHOTOS DE PROFIL ====================
    
    def save_profile_photo(self, entity_id: int, photo_path: str):
        """
        Sauvegarde le chemin d'une photo de profil.
        
        Args:
            entity_id: ID de l'entité
            photo_path: Chemin vers la photo
        """
        self.conn.execute("""
            INSERT OR REPLACE INTO profile_photos (entity_id, photo_path, downloaded_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (entity_id, photo_path))
        
        logger.debug(f"Photo de profil sauvegardée pour entity {entity_id}")
    
    def get_profile_photo(self, entity_id: int) -> Optional[str]:
        """
        Récupère le chemin d'une photo de profil.
        
        Args:
            entity_id: ID de l'entité
            
        Returns:
            Optional[str]: Chemin vers la photo ou None
        """
        cursor = self.conn.execute("""
            SELECT photo_path FROM profile_photos
            WHERE entity_id = ?
        """, (entity_id,))
        
        row = cursor.fetchone()
        return row['photo_path'] if row else None
    
    def has_profile_photo(self, entity_id: int) -> bool:
        """
        Vérifie si une photo de profil existe en cache.
        
        Args:
            entity_id: ID de l'entité
            
        Returns:
            bool: True si la photo existe
        """
        cursor = self.conn.execute("""
            SELECT 1 FROM profile_photos
            WHERE entity_id = ?
        """, (entity_id,))
        
        return cursor.fetchone() is not None
    
    # ==================== MÉTADONNÉES ====================
    
    def set_metadata(self, key: str, value: str):
        """
        Sauvegarde une métadonnée.
        
        Args:
            key: Clé
            value: Valeur
        """
        self.conn.execute("""
            INSERT OR REPLACE INTO metadata (key, value, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
    
    def get_metadata(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Récupère une métadonnée.
        
        Args:
            key: Clé
            default: Valeur par défaut
            
        Returns:
            Optional[str]: Valeur ou défaut
        """
        cursor = self.conn.execute("""
            SELECT value FROM metadata WHERE key = ?
        """, (key,))
        
        row = cursor.fetchone()
        return row['value'] if row else default
    
    def get_last_sync_time(self, session_id: str) -> Optional[datetime]:
        """
        Récupère le timestamp de la dernière synchronisation.
        
        Args:
            session_id: ID de la session
            
        Returns:
            Optional[datetime]: Timestamp ou None
        """
        value = self.get_metadata(f"last_sync_{session_id}")
        if value:
            try:
                return datetime.fromisoformat(value)
            except:
                return None
        return None
    
    def set_last_sync_time(self, session_id: str, timestamp: datetime):
        """
        Définit le timestamp de la dernière synchronisation.
        
        Args:
            session_id: ID de la session
            timestamp: Timestamp
        """
        self.set_metadata(f"last_sync_{session_id}", timestamp.isoformat())
    
    # ==================== UTILITAIRES ====================
    
    def vacuum(self):
        """Optimise la base de données (libère l'espace)."""
        self.conn.execute("VACUUM")
        logger.info("Base de données optimisée (VACUUM)")
    
    def get_stats(self) -> Dict:
        """
        Récupère les statistiques de la base de données.
        
        Returns:
            Dict: Statistiques
        """
        stats = {}
        
        # Nombre de conversations
        cursor = self.conn.execute("SELECT COUNT(*) FROM conversations")
        stats['conversations_count'] = cursor.fetchone()[0]
        
        # Nombre de messages
        cursor = self.conn.execute("SELECT COUNT(*) FROM messages")
        stats['messages_count'] = cursor.fetchone()[0]
        
        # Nombre de photos
        cursor = self.conn.execute("SELECT COUNT(*) FROM profile_photos")
        stats['photos_count'] = cursor.fetchone()[0]
        
        # Taille de la DB
        stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024) if self.db_path.exists() else 0
        
        return stats
    
    def close(self):
        """Ferme la connexion à la base de données."""
        if self.conn:
            self.conn.close()
            logger.info("Connexion à la base de données fermée")


# Instance globale (singleton)
_db_instance = None


def get_telegram_db() -> TelegramDatabase:
    """
    Récupère l'instance globale de la base de données.
    
    Returns:
        TelegramDatabase: Instance de la base de données
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = TelegramDatabase()
    return _db_instance

