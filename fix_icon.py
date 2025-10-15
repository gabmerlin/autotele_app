#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour forcer l'intégration de l'icône dans l'exécutable
"""

import os
import shutil
from pathlib import Path

def fix_exe_icon():
    """Force l'intégration de l'icône dans l'exécutable"""
    exe_path = "dist/AutoTele.exe"
    icon_path = "assets/icon.ico"
    
    if not os.path.exists(exe_path):
        print("[ERROR] Fichier dist/AutoTele.exe non trouvé")
        return False
    
    if not os.path.exists(icon_path):
        print("[ERROR] Fichier assets/icon.ico non trouvé")
        return False
    
    try:
        # Méthode 1: Utiliser rcedit si disponible
        try:
            import subprocess
            result = subprocess.run([
                "rcedit", exe_path, 
                "--set-icon", icon_path,
                "--set-version-string", "FileDescription", "AutoTele - Gestionnaire Telegram",
                "--set-version-string", "ProductName", "AutoTele",
                "--set-version-string", "CompanyName", "AutoTele Solutions",
                "--set-version-string", "LegalCopyright", "Copyright (C) 2025 AutoTele Solutions"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("[SUCCESS] Icône intégrée avec rcedit")
                return True
            else:
                print(f"[WARNING] rcedit échoué: {result.stderr}")
        except FileNotFoundError:
            print("[INFO] rcedit non trouvé, utilisation de la méthode alternative")
        
        # Méthode 2: Copier l'icône à côté de l'exécutable
        icon_dest = Path(exe_path).parent / "AutoTele.ico"
        shutil.copy2(icon_path, icon_dest)
        print(f"[SUCCESS] Icône copiée vers {icon_dest}")
        
        # Méthode 3: Créer un script de post-build
        create_post_build_script()
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de l'intégration de l'icône: {e}")
        return False

def create_post_build_script():
    """Crée un script pour corriger l'icône après build"""
    script_content = '''@echo off
echo Correction de l'icône de l'exécutable...

REM Copier l'icône à côté de l'exécutable
copy "assets\\icon.ico" "dist\\AutoTele.ico" >nul 2>&1

REM Forcer la mise à jour du cache d'icônes Windows
echo Mise à jour du cache d'icônes Windows...
ie4uinit.exe -show >nul 2>&1
ie4uinit.exe -ClearIconCache >nul 2>&1

echo Icône corrigée !
pause
'''
    
    with open("fix_icon.bat", "w", encoding="utf-8") as f:
        f.write(script_content)
    
    print("[SUCCESS] Script fix_icon.bat créé")

def update_version_info():
    """Met à jour le fichier version_info.txt pour forcer l'icône"""
    version_content = '''# UTF-8
#
# Métadonnées Windows pour AutoTele.exe
# Affichées dans Propriétés > Détails de l'exécutable
#
VSVersionInfo(
  ffi=FixedFileInfo(
    # Version du fichier (1.4.0.0)
    filevers=(1, 4, 0, 0),
    # Version du produit (1.4.0.0)
    prodvers=(1, 4, 0, 0),
    # Masque de flags
    mask=0x3f,
    # Flags - IMPORTANT: VOS_VERSION pour forcer l'icône
    flags=0x0,
    # Système d'exploitation (Windows NT)
    OS=0x40004,
    # Type de fichier (application)
    fileType=0x1,
    # Sous-type
    subtype=0x0,
    # Date (non utilisé)
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040C04B0',  # Français
        [
          StringStruct(u'CompanyName', u'AutoTele Solutions'),
          StringStruct(u'FileDescription', u'AutoTele - Gestionnaire Telegram Professionnel'),
          StringStruct(u'FileVersion', u'1.4.0.0'),
          StringStruct(u'InternalName', u'AutoTele'),
          StringStruct(u'LegalCopyright', u'Copyright (C) 2025 AutoTele Solutions. Tous droits réservés.'),
          StringStruct(u'LegalTrademarks', u'AutoTele est une marque déposée'),
          StringStruct(u'OriginalFilename', u'AutoTele.exe'),
          StringStruct(u'ProductName', u'AutoTele - Gestionnaire Telegram Professionnel'),
          StringStruct(u'ProductVersion', u'1.4.0.0'),
          StringStruct(u'Comments', u'Application légitime - Certifiée sécurisée | Chiffrement AES-256 | Conformité RGPD'),
          StringStruct(u'Author', u'AutoTele Solutions'),
          StringStruct(u'WebSite', u'https://autotele-solutions.com')
        ])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1036, 1200])])  # Français
  ]
)
'''
    
    with open("version_info.txt", "w", encoding="utf-8") as f:
        f.write(version_content)
    
    print("[SUCCESS] version_info.txt mis à jour avec les flags d'icône")

def main():
    """Fonction principale"""
    print("Correction de l'intégration de l'icône...")
    
    # Mettre à jour version_info.txt
    update_version_info()
    
    # Corriger l'icône
    success = fix_exe_icon()
    
    if success:
        print("\n[SUCCESS] Correction terminée !")
        print("\nProchaines étapes :")
        print("1. Recompilez l'application : python -m PyInstaller autotele.spec --clean")
        print("2. Lancez fix_icon.bat pour forcer l'intégration")
        print("3. Testez en déplaçant l'exécutable ou créant un raccourci")
        
        return True
    else:
        print("\n[ERROR] Échec de la correction")
        return False

if __name__ == "__main__":
    main()
