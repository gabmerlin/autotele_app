#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de protection avec PyArmor pour AutoTele.
Obfusque les fichiers critiques de l'application.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_pyarmor_obfuscate(file_path, output_dir):
    """Exécute PyArmor sur un fichier"""
    try:
        cmd = [
            sys.executable, "-m", "pyarmor", "obfuscate",
            "--output", str(output_dir),
            str(file_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if result.returncode == 0:
            return True, "OK"
        else:
            return False, result.stderr
            
    except Exception as e:
        return False, str(e)

def main():
    """Fonction principale de protection"""
    print("=" * 60)
    print("PROTECTION AVEC PYARMOR")
    print("=" * 60)
    
    # Vérifier PyArmor
    try:
        result = subprocess.run([sys.executable, "-m", "pyarmor", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(result.stdout.strip())
        else:
            print("PyArmor non installé ou erreur")
            return False
    except:
        print("PyArmor non disponible")
        return False
    
    # Fichiers à protéger
    files_to_protect = [
        "src/utils/embedded_config.py",
        "src/utils/config.py", 
        "src/utils/anti_debug.py",
        "src/main.py"
    ]
    
    # Créer le dossier de sauvegarde
    backup_dir = Path("src_backup")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    
    # Créer le dossier protégé
    protected_dir = Path("src_protected")
    if protected_dir.exists():
        shutil.rmtree(protected_dir)
    
    print("\nSauvegarde des fichiers originaux...")
    shutil.copytree("src", backup_dir)
    print(f"  -> Sauvegarde créée dans {backup_dir}")
    
    print("\nObfuscation des fichiers critiques avec PyArmor...")
    shutil.copytree("src", protected_dir)
    
    success_count = 0
    for file_path in files_to_protect:
        if Path(file_path).exists():
            print(f"  -> Obfuscation de {file_path}...")
            success, message = run_pyarmor_obfuscate(file_path, protected_dir)
            
            if success:
                print(f"     [OK] {message}")
                success_count += 1
            else:
                print(f"     ERREUR: {message}")
                print("     On garde le fichier original")
        else:
            print(f"  -> Fichier non trouvé: {file_path}")
    
    if success_count > 0:
        print(f"\n[SUCCESS] {success_count} fichier(s) protégé(s) avec succès")
        
        # Remplacer les fichiers originaux par les versions protégées
        print("\nRemplacement des fichiers par les versions protégées...")
        for file_path in files_to_protect:
            protected_file = protected_dir / file_path
            original_file = Path(file_path)
            
            if protected_file.exists():
                shutil.copy2(protected_file, original_file)
                print(f"  -> {file_path} remplacé")
        
        print("\n[SUCCESS] Protection PyArmor terminée")
        return True
    else:
        print("\n[ERROR] Aucun fichier n'a pu être protégé")
        
        # Restaurer les fichiers originaux
        print("\nRestauration des fichiers originaux...")
        shutil.rmtree("src")
        shutil.move(backup_dir, "src")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Erreur inattendue: {e}")
        
        # Restaurer les fichiers originaux en cas d'erreur
        backup_dir = Path("src_backup")
        if backup_dir.exists():
            print("\nRestauration des fichiers originaux...")
            if Path("src").exists():
                shutil.rmtree("src")
            shutil.move(backup_dir, "src")
        
        sys.exit(1)
