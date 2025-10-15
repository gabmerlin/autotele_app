#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer une icône ICO correcte à partir du logo PNG
"""

from PIL import Image
import os

def create_icon():
    """Crée une icône ICO avec toutes les tailles nécessaires"""
    try:
        # Charger le logo PNG
        logo = Image.open('assets/logo.png')
        
        # Tailles d'icônes requises pour Windows
        sizes = [16, 24, 32, 48, 64, 128, 256]
        
        # Créer les différentes tailles
        icon_images = []
        for size in sizes:
            # Redimensionner en gardant les proportions
            resized = logo.resize((size, size), Image.Resampling.LANCZOS)
            
            # Convertir en RGBA si nécessaire
            if resized.mode != 'RGBA':
                resized = resized.convert('RGBA')
            
            icon_images.append(resized)
        
        # Sauvegarder en ICO
        icon_images[0].save('assets/icon.ico', format='ICO', sizes=[(img.width, img.height) for img in icon_images])
        
        print("[SUCCESS] Icône ICO créée avec succès !")
        print("Tailles incluses:", [f"{img.width}x{img.height}" for img in icon_images])
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erreur lors de la création de l'icône : {e}")
        return False

def main():
    """Fonction principale"""
    print("Création d'une icône ICO correcte...")
    
    if not os.path.exists('assets/logo.png'):
        print("[ERROR] Fichier assets/logo.png non trouvé")
        return False
    
    # Sauvegarder l'ancienne icône
    if os.path.exists('assets/icon.ico'):
        os.rename('assets/icon.ico', 'assets/icon_backup.ico')
        print("[INFO] Ancienne icône sauvegardée en icon_backup.ico")
    
    # Créer la nouvelle icône
    success = create_icon()
    
    if success:
        print("\n✅ Icône ICO créée avec succès !")
        print("L'icône contient toutes les tailles nécessaires pour Windows.")
        print("Recompilez maintenant l'application pour appliquer la nouvelle icône.")
        
        return True
    else:
        # Restaurer l'ancienne icône en cas d'erreur
        if os.path.exists('assets/icon_backup.ico'):
            os.rename('assets/icon_backup.ico', 'assets/icon.ico')
            print("[INFO] Ancienne icône restaurée")
        
        return False

if __name__ == "__main__":
    main()
