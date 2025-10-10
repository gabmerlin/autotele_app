# Architecture de l'Application AutoTele

## 📐 Vue d'Ensemble

L'application a été entièrement refactorisée pour suivre une architecture modulaire et professionnelle avec une séparation claire des responsabilités.

## 📁 Structure des Dossiers

```
autotele/
├── config/                          # Configuration de l'application
│   └── api_credentials.py          # Credentials API Telegram
│
├── src/                            # Code source principal
│   ├── main.py                     # Point d'entrée simplifié (76 lignes)
│   │
│   ├── ui/                         # Interface utilisateur (NiceGUI)
│   │   ├── app.py                  # Classe principale AutoTeleApp
│   │   ├── components/             # Composants UI réutilisables
│   │   │   ├── calendar.py         # Widget calendrier
│   │   │   ├── dialogs.py          # Dialogues (vérification, confirmation, info)
│   │   │   └── styles.py           # Styles CSS centralisés
│   │   └── pages/                  # Pages de l'application
│   │       ├── accounts_page.py    # Gestion des comptes
│   │       ├── new_message_page.py # Création de messages
│   │       └── scheduled_messages_page.py  # Messages programmés
│   │
│   ├── core/                       # Logique métier
│   │   ├── session_manager.py      # Gestion des sessions
│   │   └── telegram/               # Module Telegram
│   │       ├── account.py          # Classe TelegramAccount
│   │       ├── manager.py          # Classe TelegramManager
│   │       └── credentials.py      # Gestion des credentials
│   │
│   ├── services/                   # Services métier
│   │   ├── message_service.py      # Service d'envoi de messages
│   │   └── dialog_service.py       # Service de gestion des dialogues
│   │
│   └── utils/                      # Utilitaires
│       ├── config.py               # Configuration
│       ├── logger.py               # Logger
│       ├── constants.py            # Constantes globales
│       └── validators.py           # Fonctions de validation
│
├── sessions/                       # Sessions Telegram
├── logs/                           # Logs de l'application
├── temp/                           # Fichiers temporaires
└── venv/                           # Environnement virtuel Python
```

## 🎯 Principes de Conception

### 1. Séparation des Responsabilités

- **UI** (`ui/`) : Interface utilisateur pure (NiceGUI)
- **Core** (`core/`) : Logique métier et entités
- **Services** (`services/`) : Services applicatifs et logique business
- **Utils** (`utils/`) : Utilitaires et helpers

### 2. Modularité

- Chaque module a une responsabilité unique et clairement définie
- Les composants UI sont réutilisables
- Les services sont indépendants et testables

### 3. Typage Fort (PEP 484)

- Tous les paramètres et retours de fonctions sont typés
- Utilisation de `Optional`, `List`, `Dict`, `Tuple`, etc.
- Aucun type `any`

### 4. Documentation Complète

- Docstrings style Google pour toutes les fonctions et classes
- Commentaires explicatifs pour les sections complexes
- README et documentation d'architecture

## 🔧 Composants Principaux

### 1. Point d'Entrée (`main.py`)

Fichier minimaliste (76 lignes) qui :
- Initialise l'application `AutoTeleApp`
- Configure la page NiceGUI
- Lance l'interface native

### 2. Application Principale (`ui/app.py`)

Classe `AutoTeleApp` qui :
- Gère le cycle de vie de l'application
- Crée la sidebar et la navigation
- Délègue aux pages spécialisées
- Coordonne les opérations sur les comptes

### 3. Composants UI (`ui/components/`)

#### a) `dialogs.py`
- `VerificationDialog` : Vérification de compte Telegram
- `ConfirmDialog` : Dialogue de confirmation générique
- `InfoDialog` : Dialogue d'information

#### b) `calendar.py`
- `CalendarWidget` : Calendrier pour sélectionner des dates
- Gère la sélection multiple
- Actions rapides (semaine, mois, effacer)

#### c) `styles.py`
- CSS centralisé pour toute l'application
- Variables CSS pour cohérence visuelle
- Styles modernes et professionnels

### 4. Pages (`ui/pages/`)

#### a) `accounts_page.py`
- Affichage des comptes en grille
- Gestion des paramètres de compte
- Ajout/suppression/reconnexion de comptes

#### b) `new_message_page.py`
- Interface par étapes (wizard)
- Sélection du compte, des groupes, composition du message
- Programmation des dates et heures
- Upload de fichiers

#### c) `scheduled_messages_page.py`
- Visualisation de tous les messages programmés
- Groupés par chat
- Suppression individuelle ou en masse

### 5. Services (`services/`)

#### a) `message_service.py`
- Envoi optimisé de messages programmés
- Gestion des rate limits Telegram (1 msg/sec/chat, 25 msg/sec global)
- Gestion des erreurs (permissions, flood)
- Retry automatique

#### b) `dialog_service.py`
- Récupération des dialogues (groupes/canaux)
- Filtrage et recherche
- Utilitaires de gestion

### 6. Core Telegram (`core/telegram/`)

#### a) `account.py` - Classe `TelegramAccount`
Représente un compte Telegram connecté :
- Connexion/déconnexion
- Authentification (code + 2FA)
- Récupération des dialogues
- Envoi de messages programmés
- Gestion des messages programmés

#### b) `manager.py` - Classe `TelegramManager`
Gestionnaire central de tous les comptes :
- Ajout/suppression de comptes
- Chargement des sessions existantes
- Vérification des codes
- Reconnexion

#### c) `credentials.py`
- Chargement des credentials API Telegram
- Ordre : Variables d'environnement → Fichier config → Par défaut

### 7. Utilitaires (`utils/`)

#### a) `constants.py`
- Constantes globales (messages, icônes, limites)
- Configuration UI (tailles, couleurs)
- Types `Final` pour immutabilité

#### b) `validators.py`
- Validation de numéros de téléphone
- Validation de noms de compte
- Validation de codes de vérification
- Validation de messages
- Validation d'horaires (HH:MM)

#### c) `config.py`
- Gestion de la configuration JSON
- Paramètres Telegram, BTCPay, UI, etc.

#### d) `logger.py`
- Logger personnalisé
- Logs en fichiers journaliers
- Historique des envois en JSON

## 📊 Flux de Données

### Envoi de Messages Programmés

```
UI (NewMessagePage)
    ↓
Services (MessageService)
    ↓
Core (TelegramAccount)
    ↓
Telethon API
```

### Gestion de Comptes

```
UI (AccountsPage)
    ↓
App (AutoTeleApp)
    ↓
Manager (TelegramManager)
    ↓
Account (TelegramAccount)
    ↓
SessionManager
```

## 🔐 Sécurité

- Sessions Telegram chiffrées par Telethon
- Credentials API séparés dans `config/`
- Pas de mots de passe en clair
- Validation stricte des entrées utilisateur

## 🚀 Performance

- Import lazy des modules lourds
- Chargement asynchrone des dialogues
- Rate limiting optimisé (25 msg/sec)
- Cache des messages programmés
- UI réactive avec NiceGUI

## 📝 Conventions de Code

- **PEP 8** : Style de code Python
- **PEP 257** : Docstrings
- **PEP 484** : Type hints
- **Naming** :
  - Classes : `PascalCase`
  - Fonctions/méthodes : `snake_case`
  - Constantes : `UPPER_SNAKE_CASE`
  - Privé : `_prefixe`

## 🧪 Tests

Pour tester l'application refactorisée :

1. Assurez-vous que le venv est activé
2. Lancez : `python src/main.py`
3. Testez chaque fonctionnalité :
   - Ajout de compte
   - Création de message
   - Programmation
   - Visualisation des messages

## 📈 Améliorations Apportées

### Avant Refactoring
- `main.py` : 745 lignes - mélange UI/logique
- `new_message_page.py` : 1376 lignes - trop complexe
- `telegram_manager.py` : 713 lignes - deux classes mélangées
- Duplication de code importante
- CSS inline partout
- Pas de validation centralisée
- Typage incomplet

### Après Refactoring
- `main.py` : 76 lignes - point d'entrée pur
- Pages : 200-400 lignes chacune - modulaires
- Classes séparées et responsables
- Composants réutilisables
- CSS centralisé
- Validation centralisée
- Typage complet PEP 484
- Documentation complète

## 🎓 Pour Aller Plus Loin

### Prochaines Améliorations Possibles

1. **Tests Unitaires** : Ajouter des tests pour les services
2. **CI/CD** : Pipeline de déploiement automatisé
3. **Internationalisation** : Support multilingue (i18n)
4. **Thèmes** : Mode sombre/clair
5. **Analytics** : Statistiques d'envoi
6. **Export** : Export des messages en CSV/JSON
7. **Templates** : Messages prédéfinis réutilisables

## 💡 Bonnes Pratiques Appliquées

✅ **Single Responsibility Principle** : Chaque classe/fonction a une seule responsabilité
✅ **DRY (Don't Repeat Yourself)** : Code non dupliqué
✅ **KISS (Keep It Simple, Stupid)** : Code simple et compréhensible
✅ **Separation of Concerns** : UI séparée de la logique
✅ **Type Safety** : Typage fort partout
✅ **Documentation** : Code auto-documenté

## 📞 Support

Pour toute question sur l'architecture, consultez :
- Ce fichier `ARCHITECTURE.md`
- Les docstrings dans le code
- Les commentaires inline
- Le `README.md` principal

