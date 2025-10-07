# AutoTele - Planificateur de Messages Telegram Professionnel

## Description

AutoTele est une application Windows professionnelle permettant aux recruteurs et professionnels de programmer des messages sur plusieurs comptes Telegram simultanément. L'application utilise la fonctionnalité native de planification de Telegram pour garantir que les messages apparaissent comme planifiés par l'utilisateur.

## Fonctionnalités Principales

- ✅ **Multi-comptes illimités** : Connectez plusieurs comptes Telegram
- ✅ **Sélection multi-groupes** : Planifiez des messages dans plusieurs groupes/canaux simultanément
- ✅ **Messages planifiés natifs** : Utilise l'API MTProto pour créer de vrais messages planifiés
- ✅ **Support média** : Texte, images, documents et fichiers
- ✅ **Sessions chiffrées** : Stockage sécurisé AES-256 des sessions Telegram
- ✅ **Système d'abonnement BTCPay** : Gestion de licences et abonnements sécurisés
- ✅ **Interface professionnelle** : Design moderne et intuitif en français
- ✅ **Historique & Logs** : Suivi complet des envois avec export CSV

## Prérequis

### Pour l'utilisateur final
- Windows 10 ou supérieur (64-bit)
- Connexion Internet
- Compte(s) Telegram actif(s)
- API ID et API Hash Telegram (voir guide ci-dessous)
- Abonnement actif via BTCPay

### Pour le développement
- Python 3.11 ou supérieur
- Git
- Visual Studio Build Tools (pour certaines dépendances)

## Installation Rapide (Utilisateur)

1. Téléchargez `AutoTele_Setup.exe` depuis les releases
2. Exécutez l'installateur et suivez les instructions
3. Obtenez vos identifiants API Telegram :
   - Allez sur https://my.telegram.org
   - Connectez-vous avec votre numéro de téléphone
   - Cliquez sur "API development tools"
   - Créez une application et notez `api_id` et `api_hash`
4. Activez votre licence via BTCPay
5. Lancez AutoTele et ajoutez votre premier compte

## Installation Développeur

```bash
# Cloner le repository
git clone https://github.com/votre-repo/autotele.git
cd autotele

# Créer un environnement virtuel
python -m venv venv
venv\Scripts\activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
python src/main.py
```

## Connexion Telegram Simplifiée

✨ **Aucun identifiant API requis !** L'application utilise des credentials partagés pour simplifier votre expérience.

Vous avez seulement besoin de :
- 📱 Votre numéro de téléphone Telegram
- 🔢 Le code de vérification reçu sur Telegram
- 🔐 Votre mot de passe 2FA (si activé)

## Build de l'Exécutable

Pour créer le fichier .exe :

```powershell
# Activer l'environnement virtuel
.\venv\Scripts\activate

# Lancer le script de build
.\build\build_exe.ps1
```

Le fichier .exe sera généré dans `dist/AutoTele.exe`

## Configuration BTCPay Server

Voir la documentation détaillée dans `docs/BTCPay_integration.md`

### Configuration Rapide

1. Créez un store sur votre BTCPay Server
2. Générez une clé API avec les permissions :
   - `btcpay.store.canviewinvoices`
   - `btcpay.store.cancreateinvoice`
3. Configurez dans `config/btcpay_config.json` :

```json
{
  "server_url": "https://votre-btcpay-server.com",
  "store_id": "votre_store_id",
  "api_key": "votre_api_key",
  "webhook_secret": "secret_pour_webhooks",
  "subscription_price": 29.99,
  "currency": "EUR",
  "trial_days": 7
}
```

## Structure du Projet

```
autotele/
├── src/
│   ├── main.py                 # Point d'entrée de l'application
│   ├── core/
│   │   ├── telegram_manager.py  # Gestion multi-comptes Telegram
│   │   ├── session_manager.py   # Chiffrement des sessions
│   │   ├── scheduler.py         # Planification des messages
│   │   └── license_manager.py   # Gestion licences BTCPay
│   ├── ui/
│   │   ├── main_window.py       # Fenêtre principale
│   │   ├── account_manager.py   # Gestion des comptes
│   │   ├── message_editor.py    # Éditeur de messages
│   │   └── styles.py            # Styles UI
│   └── utils/
│       ├── crypto.py            # Utilitaires de chiffrement
│       ├── logger.py            # Système de logs
│       └── config.py            # Configuration
├── build/
│   ├── build_exe.ps1           # Script de build Windows
│   └── autotele.spec           # Config PyInstaller
├── docs/
│   ├── user_guide.md           # Guide utilisateur
│   ├── admin_guide.md          # Guide administrateur
│   ├── BTCPay_integration.md   # Documentation BTCPay
│   └── security.md             # Recommandations sécurité
├── tests/
│   ├── test_telegram.py
│   ├── test_scheduler.py
│   ├── test_crypto.py
│   └── test_license.py
├── config/
│   └── btcpay_config.json      # Configuration BTCPay
├── requirements.txt
└── README.md
```

## Utilisation

### 1. Ajouter un Compte Telegram

1. Cliquez sur "Ajouter un compte"
2. Entrez vos `api_id` et `api_hash`
3. Entrez votre numéro de téléphone
4. Entrez le code de vérification reçu sur Telegram
5. Si activé, entrez votre mot de passe 2FA

### 2. Programmer un Message

1. Sélectionnez un compte dans la liste
2. Cliquez sur "Nouveau message planifié"
3. Sélectionnez les groupes/canaux cibles
4. Rédigez votre message (texte et/ou média)
5. Choisissez la date et l'heure de publication
6. Cliquez sur "Planifier"

### 3. Gérer les Tâches

Le tableau de bord affiche toutes vos tâches planifiées avec :
- Statut (En attente, Envoyé, Échoué)
- Date et heure de planification
- Comptes et groupes concernés
- Actions (Modifier, Supprimer)

## Sécurité

- ✅ Sessions Telegram chiffrées AES-256
- ✅ Aucun identifiant envoyé à un serveur externe
- ✅ Vérification HTTPS pour BTCPay
- ✅ Logs sans données sensibles
- ✅ Option d'export/import sécurisé des sessions

⚠️ **Conformité** : Vous devez respecter les conditions d'utilisation de Telegram et les lois anti-spam. N'utilisez pas cette application pour du spam massif.

## Limitations et Rate Limits

Pour éviter les bannissements Telegram :
- Maximum 20 messages par minute par compte
- Délai de 3 secondes entre chaque message
- Warning si plus de 50 groupes sélectionnés

## Support et Contribution

- Documentation complète : voir dossier `docs/`
- Signaler un bug : [Issues](https://github.com/votre-repo/autotele/issues)
- Questions : [Discussions](https://github.com/votre-repo/autotele/discussions)

## Licence

© 2025 AutoTele. Tous droits réservés.

Cette application nécessite un abonnement actif. L'utilisation est soumise aux conditions d'utilisation disponibles sur notre site web.

## Avertissements Légaux

- Respectez les lois locales sur le marketing et le spam
- Obtenez le consentement des destinataires avant l'envoi de messages commerciaux
- Respectez les conditions d'utilisation de Telegram
- L'éditeur décline toute responsabilité en cas d'utilisation abusive

## Changelog

### Version 1.0.0 (2025-10-07)
- Release initiale
- Support multi-comptes illimités
- Planification native Telegram
- Intégration BTCPay Server
- Interface française professionnelle

