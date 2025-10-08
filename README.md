# AutoTele - Planificateur de Messages Telegram

Application desktop pour planifier et automatiser l'envoi de messages sur Telegram.

## 🚀 Installation

### 1. Installer les dépendances

```bash
install.bat
```

### 2. Lancer l'application

```bash
launch.bat
```

L'application s'ouvrira automatiquement dans votre navigateur à l'adresse : http://localhost:8080

## 📋 Prérequis

- Python 3.11 ou supérieur
- Connexion Internet
- Comptes Telegram

## 📖 Documentation

- **[NOUVEAU_DEPART.md](NOUVEAU_DEPART.md)** - État actuel et réinitialisation
- **[DEMARRAGE_RAPIDE.txt](DEMARRAGE_RAPIDE.txt)** - Guide visuel rapide

## 🛠️ Développement

L'application est actuellement en cours de développement avec une base propre et fonctionnelle.

### Structure du projet

```
autotele/
├── src/
│   ├── main.py              # Application NiceGUI
│   ├── core/                # Logique métier
│   └── utils/               # Utilitaires
├── config/                  # Configuration
├── sessions/                # Sessions Telegram
├── logs/                    # Logs de l'application
├── install.bat              # Installation
├── launch.bat               # Lancement
└── requirements.txt         # Dépendances Python
```

## 📝 Fonctionnalités prévues

- ⏳ Gestion de comptes Telegram multiples
- ⏳ Planification de messages
- ⏳ Envoi automatique
- ⏳ Tableau de bord

## 🐛 Dépannage

### L'application ne démarre pas
1. Vérifiez que Python est installé : `python --version`
2. Réinstallez les dépendances : `install.bat`
3. Vérifiez les logs dans le dossier `logs/`

### Port 8080 déjà utilisé
L'application utilise le port 8080. Si ce port est déjà utilisé, fermez l'autre application ou modifiez le port dans `src/main.py`.

## 📄 Licence

Projet privé - Usage personnel uniquement

## 👨‍💻 Support

Pour toute question ou problème, consultez les logs dans le dossier `logs/`.
