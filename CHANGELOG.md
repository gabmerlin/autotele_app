# Changelog AutoTele

Toutes les modifications notables du projet AutoTele sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.0.0] - 2025-10-07

### 🎉 Release Initiale

#### Ajouté
- ✅ **Gestion multi-comptes Telegram illimitée**
  - Connexion sécurisée via MTProto (Telethon)
  - Authentification 2FA supportée
  - Sessions chiffrées AES-256
  - Import/Export de sessions

- ✅ **Planification de messages natifs Telegram**
  - Utilisation de l'API `schedule_date` de Telegram
  - Sélection multiple de groupes/canaux
  - Support texte + fichiers (images, PDF, documents)
  - Planification flexible (date/heure personnalisée)

- ✅ **Interface utilisateur professionnelle**
  - Design moderne avec PyQt6
  - Police Segoe UI (professionnelle et dynamique)
  - Tableau de bord des tâches
  - Gestionnaire de comptes intuitif
  - Éditeur de messages avec aperçu
  - Interface 100% en français

- ✅ **Système de licence BTCPay**
  - Intégration BTCPay Server
  - Période d'essai de 7 jours
  - Abonnement mensuel (29.99 EUR)
  - Vérification automatique de validité
  - Paiement crypto sécurisé

- ✅ **Sécurité et chiffrement**
  - Sessions Telegram chiffrées AES-256
  - Dérivation de clé PBKDF2 (100k itérations)
  - Aucune donnée envoyée à des tiers
  - Logs sans informations sensibles

- ✅ **Système de logs et historique**
  - Logs détaillés de toutes les opérations
  - Historique des messages planifiés
  - Export CSV de l'historique
  - Rotation automatique des logs

- ✅ **Rate limiting et conformité**
  - Respect des limites Telegram (20 msg/min)
  - Délai automatique entre messages (3s)
  - Avertissement si >50 groupes sélectionnés
  - Messages anti-abus

#### Sécurité
- Chiffrement AES-256 pour les sessions
- HTTPS obligatoire pour BTCPay
- Validation des entrées utilisateur
- Protection contre les injections
- Audit de code effectué

#### Documentation
- 📖 Guide utilisateur complet
- 🛠️ Guide administrateur
- 🔐 Guide de sécurité
- 🏦 Documentation intégration BTCPay
- 🔨 Guide de build et packaging

#### Tests
- ✅ Tests unitaires (crypto, scheduler, licence)
- ✅ Tests d'intégration (Telegram, BTCPay)
- ✅ Tests end-to-end
- ✅ Coverage des fonctions critiques

#### Build et Déploiement
- Script PowerShell de build automatique
- Configuration PyInstaller optimisée
- Script Inno Setup pour installeur Windows
- Documentation de build complète

### Connu
- Les messages ne peuvent être modifiés une fois planifiés (limitation Telegram)
- Nécessite connexion Internet pour vérification de licence
- Build Windows uniquement (Linux/Mac non supportés dans v1.0)

### Notes Techniques
- Python 3.11+
- PyQt6 pour l'interface
- Telethon 1.36 pour Telegram
- Cryptography 42.0 pour le chiffrement
- BTCPay Server API v1

### Compatibilité
- Windows 10 / 11 (64-bit)
- Telegram API compatible
- BTCPay Server 1.x+

---

## [Unreleased]

### Prévu pour v1.1.0
- [ ] Support de templates de messages
- [ ] Planification récurrente (quotidien, hebdomadaire)
- [ ] Statistiques avancées d'envoi
- [ ] Mode sombre pour l'interface
- [ ] Mise à jour automatique
- [ ] Support multi-langues (EN, ES)

### Considéré pour versions futures
- [ ] Support macOS et Linux
- [ ] API REST pour intégration externe
- [ ] Dashboard web complémentaire
- [ ] Support de plus de types de fichiers
- [ ] Groupes favoris
- [ ] Raccourcis clavier personnalisables

---

## Format des Versions

**[X.Y.Z]**
- X : Version majeure (changements incompatibles)
- Y : Version mineure (nouvelles fonctionnalités compatibles)
- Z : Patch (corrections de bugs)

## Types de Changements

- `Ajouté` : Nouvelles fonctionnalités
- `Modifié` : Changements de fonctionnalités existantes
- `Déprécié` : Fonctionnalités bientôt supprimées
- `Supprimé` : Fonctionnalités supprimées
- `Corrigé` : Corrections de bugs
- `Sécurité` : Corrections de vulnérabilités

---

**Légende des emojis** :
- ✅ Implémenté
- 🎉 Release majeure
- 🔐 Sécurité
- 🐛 Bug fix
- 📖 Documentation
- ⚡ Performance
- 🛠️ Maintenance

---

© 2025 AutoTele - Changelog

