# 🎨 GUIDE DE CRÉATION DU LOGO AUTOTELE

## 📋 Fichiers Requis

Pour avoir un installateur et une application avec votre logo, vous devez créer :

### 1. **icon.ico** (OBLIGATOIRE)

**Format :** Icône Windows multi-tailles  
**Tailles requises :**
- 256x256 pixels (haute résolution)
- 128x128 pixels
- 64x64 pixels
- 48x48 pixels
- 32x32 pixels
- 16x16 pixels

**Placement :** `assets/icon.ico`

**Utilisation :**
- ✅ Icône de l'exécutable AutoTele.exe
- ✅ Icône de l'installateur
- ✅ Icône dans la barre des tâches Windows
- ✅ Icône dans le menu Démarrer

---

### 2. **wizard_image.bmp** (Optionnel mais recommandé)

**Format :** BMP 24-bit  
**Dimensions :** 164 x 314 pixels  
**Utilisation :** Grande image à gauche de l'installateur

**Conseils :**
- Utilisez votre logo + texte "AutoTele"
- Couleurs de votre branding
- Fond dégradé professionnel

---

### 3. **wizard_small.bmp** (Optionnel)

**Format :** BMP 24-bit  
**Dimensions :** 55 x 58 pixels  
**Utilisation :** Petite image en haut de chaque page de l'installateur

---

### 4. **logo.png** (Optionnel pour l'interface)

**Format :** PNG avec transparence  
**Dimensions :** 200 x 200 pixels minimum  
**Utilisation :** Logo dans l'interface de l'application

---

## 🛠️ OUTILS POUR CRÉER VOS LOGOS

### Option 1 : Convertisseurs en Ligne (Facile)

**Pour créer icon.ico :**
- https://convertio.co/fr/png-ico/
- https://www.icoconverter.com/
- https://redketchup.io/icon-converter

**Étapes :**
1. Créez votre logo en PNG (512x512 minimum)
2. Uploadez sur un convertisseur
3. Cochez toutes les tailles (16, 32, 48, 64, 128, 256)
4. Téléchargez le .ico
5. Renommez en `icon.ico` et placez dans `assets/`

### Option 2 : Logiciels Gratuits

**GIMP (Gratuit, Professionnel) :**
1. Téléchargez : https://www.gimp.org/
2. Créez votre logo
3. Fichier > Exporter sous... > icon.ico
4. Cochez toutes les tailles

**IcoFX (Windows, Gratuit pour usage personnel) :**
1. Téléchargez : https://icofx.ro/
2. Import image > Créer icône
3. Générer toutes les tailles automatiquement

### Option 3 : IA Générative (Moderne)

**Générer un logo avec IA :**
- DALL-E 3 (ChatGPT Plus)
- Midjourney
- Stable Diffusion

**Prompt suggéré :**
```
"Professional app icon for AutoTele, a Telegram management app, 
modern design, blue and white colors, minimalist, 
telegram symbol, automation, clean logo, flat design, 512x512"
```

---

## 📐 SPÉCIFICATIONS DESIGN

### Couleurs Recommandées (Cohérence avec l'App)

Basé sur votre app actuelle :
- **Primaire :** #1e3a8a (Bleu foncé)
- **Secondaire :** #3b82f6 (Bleu clair)
- **Accent :** #0ea5e9 (Cyan)
- **Blanc :** #ffffff

### Style Recommandé

- ✅ Minimaliste et moderne
- ✅ Facilement reconnaissable en petit (16x16)
- ✅ Lié à Telegram (avion en papier, bulle de message)
- ✅ Élément d'automatisation (engrenage, horloge)

### Exemples d'Idées

1. **Avion Telegram + Engrenage** (automatisation)
2. **Bulle de message + Éclair** (vitesse)
3. **T stylisé + Horloge** (planification)
4. **Logo Telegram customisé** (attention aux droits)

---

## 🚀 UTILISATION DU LOGO

### Une fois icon.ico créé

```
assets/
  └── icon.ico    # Votre logo créé
```

**Vérification :**
```bash
# Vérifier que l'icône est valide
Get-Item assets\icon.ico
```

**Compilation :**
```bash
# Le logo sera automatiquement inclus
pyinstaller autotele.spec --clean
```

**Résultat :**
- ✅ `dist/AutoTele.exe` aura votre logo
- ✅ L'installateur aura votre logo
- ✅ L'icône apparaîtra dans Windows

---

## 📁 STRUCTURE FINALE

```
assets/
├── README_LOGO.md           # Ce fichier
├── icon.ico                 # ⚠️ À CRÉER - Logo principal
├── wizard_image.bmp         # Optionnel - Grande image installateur
├── wizard_small.bmp         # Optionnel - Petite image installateur
└── logo.png                 # Optionnel - Logo interface
```

---

## ⚠️ CE QUE VOUS DEVEZ FAIRE

### OBLIGATOIRE ✅

1. **Créer icon.ico** (256x256 minimum, multi-tailles)
   - Utilisez un des outils listés ci-dessus
   - Placez dans `assets/icon.ico`
   - Vérifiez qu'il contient plusieurs tailles

### OPTIONNEL (Améliore l'apparence)

2. **Créer wizard_image.bmp** (164x314)
   - Image pour l'installateur
   - Votre logo + texte "AutoTele"

3. **Créer wizard_small.bmp** (55x58)
   - Petite version du logo

4. **Créer logo.png** (200x200+)
   - Pour afficher dans l'application

---

## 🎨 TEMPLATES FOURNIS

Si vous voulez un logo temporaire pour tester :

**Option 1 : Générer un logo simple**

Utilisez un générateur de placeholder :
- https://placeholder.com/
- https://dummyimage.com/

**Option 2 : Logo texte simple**

Créez une image avec juste le texte "AT" ou "AutoTele" 
sur fond bleu (#1e3a8a)

---

## ✅ VÉRIFICATION

Après avoir créé votre logo :

```bash
# Vérifier la structure
dir assets

# Devrait afficher :
# icon.ico (obligatoire)
# wizard_image.bmp (optionnel)
# wizard_small.bmp (optionnel)
```

**Puis recompilez :**
```bash
build.bat
```

Votre exe et installateur auront maintenant votre logo ! 🎉

---

## 📞 AIDE

**Si vous n'êtes pas designer :**
- Engagez un designer sur Fiverr (~5-20€)
- Utilisez un template gratuit sur Flaticon
- Générez avec une IA (DALL-E, Midjourney)

**Formats acceptés pour conversion :**
- PNG, JPG, SVG → convertir en .ico

---

**Bon design de logo ! 🎨**

