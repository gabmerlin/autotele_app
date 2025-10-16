# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de configuration PyInstaller pour AutoTele.

Compilation:
    pyinstaller autotele.spec --clean

Résultat:
    dist/AutoTele.exe
"""

import os
from pathlib import Path
import nicegui

block_cipher = None

# Trouver le chemin de NiceGUI
nicegui_path = os.path.dirname(nicegui.__file__)

# Chemin absolu vers le dossier src (CRITIQUE pour que PyInstaller trouve les modules)
src_path = os.path.abspath('src')

a = Analysis(
    ['src\\main.py'],
    pathex=[src_path],  # Chemin ABSOLU - permet à PyInstaller de trouver ui, utils, etc.
    binaries=[],
    datas=[
        # Fichiers statiques NiceGUI (CRITIQUE pour PyInstaller)
        (os.path.join(nicegui_path, 'static'), 'nicegui/static'),
        (os.path.join(nicegui_path, 'templates'), 'nicegui/templates'),
        
        # Fichiers statiques UI
        ('src\\ui\\static\\material-icons.css', 'ui\\static'),
        
        # __init__.py files (CRITIQUE pour la structure des packages)
        ('src\\__init__.py', '.'),
        ('src\\ui\\__init__.py', 'ui'),
        ('src\\ui\\app.py', 'ui'),
        ('src\\ui\\components\\__init__.py', 'ui\\components'),
        ('src\\ui\\components\\auth_dialog.py', 'ui\\components'),
        ('src\\ui\\components\\payment_dialog.py', 'ui\\components'),
        ('src\\ui\\components\\styles.py', 'ui\\components'),
        ('src\\ui\\components\\svg_icons.py', 'ui\\components'),
        ('src\\ui\\dialogs\\__init__.py', 'ui\\dialogs'),
        ('src\\ui\\dialogs\\account_dialogs.py', 'ui\\dialogs'),
        ('src\\ui\\managers\\__init__.py', 'ui\\managers'),
        ('src\\ui\\managers\\auth_manager.py', 'ui\\managers'),
        ('src\\ui\\managers\\ui_manager.py', 'ui\\managers'),
        ('src\\ui\\pages\\__init__.py', 'ui\\pages'),
        ('src\\ui\\pages\\accounts_page.py', 'ui\\pages'),
        ('src\\ui\\pages\\messaging_page.py', 'ui\\pages'),
        ('src\\ui\\pages\\new_message_page.py', 'ui\\pages'),
        ('src\\ui\\pages\\scheduled_messages_page.py', 'ui\\pages'),
        ('src\\ui\\pages\\sending_tasks_page.py', 'ui\\pages'),
        ('src\\core\\__init__.py', 'core'),
        ('src\\core\\telegram\\__init__.py', 'core\\telegram'),
        ('src\\services\\__init__.py', 'services'),
        ('src\\database\\__init__.py', 'database'),
        ('src\\utils\\__init__.py', 'utils'),
        
        # Configuration par défaut
        ('config\\app_config.json', 'config'),
        ('config\\credentials.example', 'config'),
        
        # CORRECTION : S'assurer que le dossier temp/photos existe
        # Créer un fichier .gitkeep pour forcer la création du dossier
        ('temp\\.gitkeep', 'temp'),
        
        # IMPORTANT: .env n'est PAS inclus (contient les secrets)
        # L'utilisateur devra créer son .env après installation
    ],
    hiddenimports=[
        # === NICEGUI ET DÉPENDANCES WEB ===
        'nicegui',
        'nicegui.elements',
        'fastapi',
        'fastapi.applications',
        'uvicorn',
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'starlette',
        'starlette.applications',
        'starlette.routing',
        'starlette.middleware',
        'starlette.middleware.cors',
        'starlette.responses',
        
        # === TELEGRAM ===
        'telethon',
        'telethon.tl',
        'telethon.tl.types',
        'telethon.tl.functions',
        'telethon.tl.functions.messages',
        'telethon.tl.functions.account',
        'telethon.tl.functions.photos',
        'telethon.errors',
        'telethon.sessions',
        
        # === CRYPTOGRAPHIE ===
        'cryptography',
        'cryptography.fernet',
        'cryptography.hazmat',
        'cryptography.hazmat.primitives',
        'cryptography.hazmat.primitives.hashes',
        'cryptography.hazmat.primitives.kdf',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.backends',
        'cryptography.hazmat.backends.openssl',
        
        # === PYWIN32 (WINDOWS) ===
        'win32api',
        'win32con',
        'win32gui',
        'win32security',
        'ntsecuritycon',
        'pywintypes',
        
        # === AUTRES DÉPENDANCES ===
        'aiofiles',
        'dateutil',
        'dateutil.parser',
        'requests',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'supabase',
        'webview',  # pywebview
        'dotenv',
        
        # === MODULES INTERNES ===
        'core',
        'core.telegram',
        'services',
        'ui',
        'ui.components',
        'ui.components.auth_dialog',
        'ui.components.payment_dialog',
        'ui.components.styles',
        'ui.components.svg_icons',
        'ui.dialogs',
        'ui.dialogs.account_dialogs',
        'ui.managers',
        'ui.managers.auth_manager',
        'ui.managers.ui_manager',
        'ui.pages',
        'ui.pages.accounts_page',
        'ui.pages.messaging_page',
        'ui.pages.new_message_page',
        'ui.pages.scheduled_messages_page',
        'ui.pages.sending_tasks_page',
        'database',
        'utils',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Bibliothèques non nécessaires (réduction de taille)
        'matplotlib',
        'scipy',
        'numpy',
        'pandas',
        'pytest',
        'tkinter',
        '_tkinter',
        'sphinx',
        'IPython',
        'jupyter',
        # Modules de sécurité qui déclenchent les antivirus (désactivés temporairement)
        'utils.anti_debug',
        'psutil',  # Utilisé uniquement par anti_debug
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='AutoTele',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Désactivé pour réduire les faux positifs antivirus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Pas de console (application GUI pure)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Logo de l'application (si existe)
    icon='assets\\icon.ico' if os.path.exists('assets\\icon.ico') else None,
    # Métadonnées Windows (propriétés de l'exe)
    version_file='version_info.txt',
    # Forcer l'utilisation de l'icône pour les raccourcis Windows
    uac_admin=False,
)

