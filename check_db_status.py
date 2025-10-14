"""Vérification rapide de l'état de la base de données."""
import sys
import os
from pathlib import Path

# Fix encodage
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from database.telegram_db import get_telegram_db

print("📊 ÉTAT DE LA BASE DE DONNÉES")
print("=" * 60)

db = get_telegram_db()
stats = db.get_stats()

print(f"Conversations : {stats['conversations_count']}")
print(f"Messages : {stats['messages_count']}")
print(f"Photos : {stats['photos_count']}")
print(f"Taille : {stats['db_size_mb']:.2f} MB")
print()

# Lister quelques conversations
cursor = db.conn.execute("SELECT entity_id, title, session_id, type FROM conversations LIMIT 10")
rows = cursor.fetchall()

if rows:
    print("📝 Premières conversations :")
    for row in rows:
        print(f"   - {row['title']} (type: {row['type']}, session: {row['session_id'][:10]}...)")
else:
    print("❌ AUCUNE CONVERSATION DANS LA DB !")

