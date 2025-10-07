# Guide de Sécurité AutoTele

Ce document décrit les mesures de sécurité implémentées dans AutoTele et les bonnes pratiques recommandées.

## Table des Matières

1. [Sécurité des Sessions Telegram](#sécurité-des-sessions-telegram)
2. [Protection des Données](#protection-des-données)
3. [Intégration BTCPay](#intégration-btcpay)
4. [Recommandations Utilisateur](#recommandations-utilisateur)
5. [Audits de Sécurité](#audits-de-sécurité)

## Sécurité des Sessions Telegram

### Chiffrement des Sessions

**Algorithme** : AES-256 via Fernet (bibliothèque `cryptography`)

Les sessions Telegram sont chiffrées au repos pour protéger vos identifiants :

```python
# Chiffrement automatique
- Algorithme : AES-256-CBC
- Mode : Fernet (AES + HMAC)
- Dérivation de clé : PBKDF2-SHA256
- Itérations : 100,000
- Salt : Unique par installation
```

### Stockage des Sessions

**Emplacement** : `sessions/`

Chaque session Telegram est stockée dans un fichier `.session` :
- Format : SQLite (Telethon)
- Contient : Clés d'authentification, informations de session
- Protection : Chiffrement AES-256

**Important** :
- ❌ Ne partagez JAMAIS le dossier `sessions/`
- ❌ Ne commitez JAMAIS ces fichiers dans Git
- ✅ Sauvegardez-les de manière sécurisée
- ✅ Utilisez un gestionnaire de mots de passe pour les backups

### Authentification

**Flux d'authentification** :

1. **Identifiants API** : Obtenus sur my.telegram.org
   - `api_id` : Identifiant numérique
   - `api_hash` : Hash alphanumérique
   - ⚠️ Ces identifiants ne sont JAMAIS envoyés à un serveur tiers

2. **Code de vérification** : Envoyé par Telegram
   - Code à 5 chiffres
   - Envoyé via l'app Telegram
   - Validité : ~10 minutes

3. **2FA (optionnel)** : Si activé sur votre compte
   - Mot de passe cloud
   - Non stocké par AutoTele
   - Utilisé uniquement lors de l'authentification

### Révocation d'Accès

Pour révoquer l'accès d'AutoTele à votre compte Telegram :

1. Ouvrez Telegram
2. **Paramètres** → **Confidentialité et sécurité** → **Sessions actives**
3. Trouvez "AutoTele" ou votre nom de session
4. Cliquez sur **Terminer la session**

## Protection des Données

### Données Stockées Localement

| Donnée | Emplacement | Chiffrement | Sensibilité |
|--------|-------------|-------------|-------------|
| Sessions Telegram | `sessions/` | AES-256 | ⚠️ Critique |
| Licence | `config/license.json` | Non | 🔵 Moyen |
| Configuration | `config/app_config.json` | Non (API key oui) | 🟡 Élevé |
| Logs | `logs/` | Non | 🟢 Faible |
| Tâches planifiées | `config/scheduled_tasks.json` | Non | 🟢 Faible |

### Données NON Stockées

AutoTele ne stocke **JAMAIS** :
- ❌ Mots de passe Telegram
- ❌ Codes de vérification
- ❌ Contenu complet des messages (seulement aperçus dans les logs)
- ❌ Données des groupes et canaux (seulement IDs et noms)

### Transmission de Données

**Connexions Telegram** :
- 🔒 Protocole : MTProto (chiffré de bout en bout)
- 🌐 Direct : Client → Serveurs Telegram
- ⚠️ Aucun intermédiaire tiers

**Connexions BTCPay** :
- 🔒 HTTPS uniquement
- 🔑 API Key dans l'en-tête Authorization
- ✅ Vérification des certificats SSL

## Intégration BTCPay

### Protection de l'API Key

L'API key BTCPay est sensible et doit être protégée :

**Stockage** :
- Fichier : `config/app_config.json`
- Permissions : Lecture seule pour l'utilisateur
- Format : JSON (jamais en clair dans les logs)

**Bonnes pratiques** :
1. ✅ Générez une clé avec permissions minimales
2. ✅ Renouvelez régulièrement (tous les 6 mois)
3. ✅ Révoquez immédiatement si compromise
4. ❌ Ne commitez jamais dans Git
5. ❌ Ne partagez jamais par email/chat

### Permissions API Requises

Minimum strict :
- `btcpay.store.canviewinvoices` : Voir les factures
- `btcpay.store.cancreateinvoice` : Créer des factures

**Pas besoin de** :
- ❌ Accès aux wallets
- ❌ Modification des stores
- ❌ Gestion des utilisateurs

### Vérification de Paiement

Le processus de vérification est sécurisé :

1. **Création de facture** : Génère un `orderId` unique (license key)
2. **Paiement** : L'utilisateur paye via BTCPay (hors application)
3. **Vérification** : L'app vérifie le statut via l'API BTCPay
4. **Activation** : Si `status == "settled"`, la licence est activée

**Sécurité** :
- Pas de stockage de moyens de paiement
- Pas de gestion de portefeuilles
- Vérification côté serveur (BTCPay)

## Recommandations Utilisateur

### Configuration du Système

#### Windows Defender / Antivirus

AutoTele peut être signalé comme suspect (faux positif courant avec PyInstaller) :

1. **Ajouter une exception** :
   - Windows Defender → Paramètres → Exclusions
   - Ajouter le dossier d'installation d'AutoTele

2. **Vérifier la signature** (si disponible) :
   ```powershell
   Get-AuthenticodeSignature "C:\Program Files\AutoTele\AutoTele.exe"
   ```

#### Pare-feu

Autoriser AutoTele à accéder à :
- Telegram API (tcp.telegram.org, ports 443, 80)
- BTCPay Server (votre domaine, port 443)

#### Permissions Fichiers

Restreindre l'accès au dossier d'installation :

```powershell
# Windows : Permissions recommandées
icacls "C:\Users\VotreNom\AppData\Local\AutoTele\sessions" /inheritance:r
icacls "C:\Users\VotreNom\AppData\Local\AutoTele\sessions" /grant:r "%USERNAME%:(OI)(CI)F"
```

### Bonnes Pratiques

#### Mots de Passe

- ✅ Utilisez un mot de passe fort pour votre compte Telegram
- ✅ Activez la double authentification (2FA) sur Telegram
- ✅ Ne réutilisez pas de mots de passe

#### Sauvegardes

**Que sauvegarder** :
- `sessions/` : Sessions Telegram (chiffrées)
- `config/license.json` : Votre licence
- `config/app_config.json` : Configuration personnalisée

**Comment sauvegarder** :
1. Créez une archive chiffrée :
   ```powershell
   # Avec 7-Zip
   7z a -p -mhe=on backup_autotele.7z sessions/ config/
   ```

2. Stockez sur :
   - Clé USB chiffrée
   - Cloud avec chiffrement (Cryptomator, etc.)
   - Gestionnaire de mots de passe (Bitwarden, 1Password)

**Fréquence** : Après chaque ajout de compte

#### Mises à Jour

- ✅ Installez les mises à jour de sécurité
- ✅ Vérifiez la source des téléchargements
- ✅ Lisez les changelogs

### Détection de Compromission

**Signes d'alerte** :
- Sessions Telegram inconnues dans Telegram
- Messages planifiés non créés par vous
- Activité suspecte dans vos groupes
- Licence désactivée sans raison

**Actions en cas de compromission** :

1. **Immédiat** :
   - Changez votre mot de passe Telegram
   - Révoquez toutes les sessions actives
   - Supprimez et recréez vos sessions dans AutoTele

2. **Investigation** :
   - Vérifiez les logs : `logs/autotele_*.log`
   - Scannez votre système avec un antivirus
   - Vérifiez les factures BTCPay

3. **Prévention** :
   - Générez de nouvelles API keys Telegram
   - Renouvelez l'API key BTCPay
   - Réinstallez AutoTele

## Audits de Sécurité

### Code Source

AutoTele est open-source et peut être audité :

**Éléments auditables** :
- Chiffrement : `src/utils/crypto.py`
- Gestion sessions : `src/core/session_manager.py`
- API Telegram : `src/core/telegram_manager.py`
- Licence BTCPay : `src/core/license_manager.py`

### Dépendances

Audit des dépendances avec :

```bash
# Scanner les vulnérabilités
pip install safety
safety check -r requirements.txt

# Mettre à jour les dépendances
pip list --outdated
pip install --upgrade [package]
```

### Pentest

Pour les entreprises souhaitant un audit complet :

**Points de test** :
1. Chiffrement des sessions
2. Protection de l'API key BTCPay
3. Validation des entrées utilisateur
4. Sécurité des communications réseau
5. Gestion des erreurs (pas de fuite d'info)

## Conformité

### RGPD (Protection des Données)

AutoTele traite des données personnelles minimales :

**Données collectées** :
- Numéros de téléphone Telegram (local uniquement)
- IDs de groupes et canaux (local uniquement)
- Logs d'activité (local uniquement)

**Droits des utilisateurs** :
- ✅ Droit d'accès : Toutes les données sont locales
- ✅ Droit de rectification : Modifiable via l'interface
- ✅ Droit à l'effacement : Suppression des comptes possible
- ✅ Droit à la portabilité : Export des sessions possible

**Pas de transfert de données** :
- ❌ Aucune donnée envoyée à l'éditeur
- ❌ Aucun tracking ou analytics
- ❌ Aucune télémétrie

### Conditions d'Utilisation Telegram

⚠️ **Important** : L'utilisateur est responsable de respecter les ToS de Telegram :

- https://telegram.org/tos
- https://core.telegram.org/api/terms

**Interdictions** :
- ❌ Spam massif
- ❌ Messages non sollicités
- ❌ Contenu illégal
- ❌ Abus des API

**Conséquences** : Bannissement du compte Telegram

## Reporting de Vulnérabilités

Si vous découvrez une vulnérabilité :

**Processus** :
1. ❌ Ne la divulguez PAS publiquement
2. ✉️ Contactez : security@autotele.com (exemple)
3. 📝 Incluez :
   - Description détaillée
   - Steps to reproduce
   - Impact potentiel
   - Version affectée

**Délai de réponse** : 48h maximum

## Checklist de Sécurité

### Installation

- [ ] Téléchargé depuis une source officielle
- [ ] Signature vérifiée (si disponible)
- [ ] Antivirus à jour
- [ ] Pare-feu configuré

### Configuration

- [ ] API keys Telegram sécurisées
- [ ] API key BTCPay sécurisée
- [ ] Permissions fichiers restreintes
- [ ] 2FA activée sur Telegram

### Utilisation

- [ ] Sessions Telegram sauvegardées
- [ ] Mots de passe forts
- [ ] Logs vérifiés régulièrement
- [ ] Mises à jour installées

### Maintenance

- [ ] Sauvegardes mensuelles
- [ ] Renouvellement API keys (6 mois)
- [ ] Audit des sessions actives Telegram
- [ ] Vérification des dépendances

---

**Dernière mise à jour** : 2025-10-07  
**Version du document** : 1.0

Pour toute question de sécurité, consultez la documentation complète ou contactez le support.

© 2025 AutoTele - Guide de Sécurité

