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

block_cipher = None

a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Fichiers statiques UI
        ('src\\ui\\static\\material-icons.css', 'ui\\static'),
        
        # Configuration par défaut
        ('config\\app_config.json', 'config'),
        ('config\\credentials.example', 'config'),
        
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
        'pywebview',
        'dotenv',
        
        # === MODULES INTERNES ===
        'src',
        'src.core',
        'src.core.telegram',
        'src.services',
        'src.ui',
        'src.ui.components',
        'src.ui.dialogs',
        'src.ui.managers',
        'src.ui.pages',
        'src.database',
        'src.utils',
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
    upx=True,  # Compression UPX pour réduire la taille
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
)

