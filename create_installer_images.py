#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour créer les images d'installateur Inno Setup avec transparence
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_wizard_image():
    """Crée l'image principale de l'assistant (164x314 pixels)"""
    # Charger le logo original
    logo = Image.open('assets/logo.png')
    
    # Créer une image blanche de la taille requise par Inno Setup
    width, height = 164, 314
    wizard_img = Image.new('RGBA', (width, height), (255, 255, 255, 0))  # Fond transparent
    
    # Redimensionner le logo pour s'adapter
    logo_size = min(width - 20, height - 40)  # Marges
    logo_resized = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
    
    # Centrer le logo
    x = (width - logo_size) // 2
    y = (height - logo_size) // 2
    wizard_img.paste(logo_resized, (x, y), logo_resized)
    
    # Sauvegarder
    wizard_img.save('assets/wizard_image.png', 'PNG')
    print("[OK] Image wizard_image.png créée (164x314)")
    return wizard_img

def create_wizard_small_image():
    """Crée la petite image de l'assistant (55x55 pixels)"""
    # Charger le logo original
    logo = Image.open('assets/logo.png')
    
    # Créer une image de la taille requise
    size = 55
    small_img = Image.new('RGBA', (size, size), (255, 255, 255, 0))  # Fond transparent
    
    # Redimensionner le logo
    logo_resized = logo.resize((size, size), Image.Resampling.LANCZOS)
    small_img.paste(logo_resized, (0, 0), logo_resized)
    
    # Sauvegarder
    small_img.save('assets/wizard_small.png', 'PNG')
    print("[OK] Image wizard_small.png créée (55x55)")
    return small_img

def main():
    """Fonction principale"""
    print("Création des images d'installateur avec transparence...")
    
    try:
        # Vérifier que le logo existe
        if not os.path.exists('assets/logo.png'):
            print("[ERROR] Fichier assets/logo.png non trouvé")
            return False
        
        # Créer les images
        create_wizard_image()
        create_wizard_small_image()
        
        print("\n[SUCCESS] Images d'installateur créées avec succès !")
        print("Fichiers créés :")
        print("- assets/wizard_image.png (164x314)")
        print("- assets/wizard_small.png (55x55)")
        print("\nCes images ont des fonds transparents et s'adapteront parfaitement à Inno Setup.")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Erreur : {e}")
        return False

if __name__ == "__main__":
    main()
