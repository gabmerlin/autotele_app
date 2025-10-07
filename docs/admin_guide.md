# Guide Administrateur AutoTele

Ce guide est destiné aux administrateurs et développeurs responsables du déploiement et de la maintenance d'AutoTele.

## Table des Matières

1. [Architecture](#architecture)
2. [Installation et Déploiement](#installation-et-déploiement)
3. [Configuration](#configuration)
4. [Gestion du Serveur BTCPay](#gestion-du-serveur-btcpay)
5. [Maintenance](#maintenance)
6. [Sécurité](#sécurité)
7. [Monitoring](#monitoring)
8. [Dépannage](#dépannage)

## Architecture

### Composants Principaux

```
AutoTele Application (Client Windows)
    ├── Interface Utilisateur (PyQt6)
    ├── Gestionnaire Telegram (Telethon)
    ├── Scheduler de Messages
    ├── Gestionnaire de Sessions (Chiffrement AES-256)
    └── Gestionnaire de Licences (BTCPay Client)
            │
            ↓ HTTPS
    BTCPay Server (VPS)
    ├── API REST
    ├── Store Management
    ├── Invoice Generation
    └── Webhook Notifications
```

### Technologies Utilisées

- **Frontend** : PyQt6 (Interface graphique)
- **Telegram API** : Telethon (MTProto)
- **Chiffrement** : cryptography (AES-256, PBKDF2)
- **Async** : asyncio, qasync
- **Build** : PyInstaller
- **Paiement** : BTCPay Server API

### Flux de Données

1. **Authentification Telegram** : Client → Telegram API (direct)
2. **Stockage Sessions** : Local chiffré (AES-256)
3. **Planification Messages** : Client → Telegram API (schedule_date)
4. **Vérification Licence** : Client → BTCPay Server API → Response

## Installation et Déploiement

### Déploiement de l'Application Client

#### Prérequis

- Windows Server 2019+ ou Windows 10+ (pour tests)
- Python 3.11+ (pour build)
- Visual C++ Redistributable 2015-2022

#### Build de l'Application

```powershell
# Cloner le repo
git clone https://github.com/votre-repo/autotele.git
cd autotele

# Créer l'environnement
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Build
.\build\build_exe.ps1
```

#### Distribution

1. **Exécutable Portable** : Distribuez le dossier `dist/AutoTele/`
2. **Installeur** : Compilez `build/build_installer.iss` avec Inno Setup
3. **Signature** : Signez l'exécutable avec un certificat de code

```powershell
# Signature (optionnel mais recommandé)
signtool sign /f "certificate.pfx" /p "password" /t http://timestamp.digicert.com "dist/AutoTele/AutoTele.exe"
```

### Déploiement du Serveur BTCPay

#### Option 1 : VPS avec Docker (Recommandé)

**Prérequis** :
- VPS Linux (Ubuntu 20.04+ recommandé)
- 2 vCPU, 4 GB RAM minimum
- 50 GB SSD
- Nom de domaine avec SSL

**Installation** :

```bash
# Connexion SSH au VPS
ssh root@votre-vps.com

# Installation BTCPay Server
cd /tmp
git clone https://github.com/btcpayserver/btcpayserver-docker
cd btcpayserver-docker

# Configuration
export BTCPAY_HOST="btcpay.votre-domaine.com"
export REVERSEPROXY_DEFAULT_HOST="$BTCPAY_HOST"
export NBITCOIN_NETWORK="mainnet"
export BTCPAYGEN_CRYPTO1="btc"
export BTCPAYGEN_CRYPTO2="ltc"
export BTCPAY_ENABLE_SSH=true

# Lancement
./btcpay-setup.sh -i

# Attendre la synchronisation (peut prendre plusieurs heures)
```

**Configuration Post-Installation** :

1. Accédez à `https://btcpay.votre-domaine.com`
2. Créez votre compte administrateur
3. Créez un store "AutoTele Subscriptions"
4. Générez une API key

#### Option 2 : BTCPay Tiers

Si vous préférez utiliser un service hébergé :
- BTCPay Jungle : https://junglepay.me
- Luna Node : https://lunanode.com/btcpay

## Configuration

### Configuration de l'Application

Le fichier `config/app_config.json` est créé au premier lancement :

```json
{
  "app": {
    "name": "AutoTele",
    "version": "1.0.0",
    "language": "fr"
  },
  "telegram": {
    "rate_limit_delay": 3,
    "max_messages_per_minute": 20,
    "max_groups_warning": 50
  },
  "btcpay": {
    "server_url": "https://btcpay.votre-domaine.com",
    "store_id": "VOTRE_STORE_ID",
    "api_key": "VOTRE_API_KEY",
    "webhook_secret": "secret_unique",
    "subscription_price": 29.99,
    "currency": "EUR",
    "trial_days": 7,
    "check_interval_hours": 24
  },
  "security": {
    "session_encryption": true,
    "auto_logout_minutes": 0,
    "require_password": false
  },
  "paths": {
    "sessions_dir": "sessions",
    "logs_dir": "logs",
    "config_dir": "config",
    "temp_dir": "temp"
  }
}
```

### Variables d'Environnement (Optionnel)

Pour les déploiements avancés :

```powershell
# Configuration BTCPay
$env:AUTOTELE_BTCPAY_URL = "https://btcpay.votre-domaine.com"
$env:AUTOTELE_BTCPAY_API_KEY = "your_api_key"
$env:AUTOTELE_BTCPAY_STORE_ID = "your_store_id"

# Configuration Logging
$env:AUTOTELE_LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
```

## Gestion du Serveur BTCPay

### Création d'un Store

1. Connectez-vous à BTCPay Server
2. Allez dans **Stores** → **Create a new store**
3. Nom : "AutoTele Subscriptions"
4. Devise par défaut : EUR (ou USD)
5. Configurez votre wallet Bitcoin

### Génération d'une API Key

1. **Account Settings** → **API Keys** → **Generate Key**
2. Permissions requises :
   - `btcpay.store.canviewinvoices`
   - `btcpay.store.cancreateinvoice`
3. Copiez la clé générée
4. Ajoutez-la dans `config/app_config.json`

### Configuration des Webhooks (Optionnel)

Pour des notifications en temps réel :

1. **Store Settings** → **Webhooks** → **Create Webhook**
2. Payload URL : `https://votre-backend.com/webhooks/btcpay`
3. Events : `InvoiceSettled`, `InvoiceExpired`
4. Secret : Même que `webhook_secret` dans la config

### Test de l'Intégration

```python
# Script de test (test_btcpay.py)
import requests

SERVER_URL = "https://btcpay.votre-domaine.com"
API_KEY = "votre_api_key"
STORE_ID = "votre_store_id"

headers = {
    "Authorization": f"token {API_KEY}",
    "Content-Type": "application/json"
}

# Tester la connexion
response = requests.get(
    f"{SERVER_URL}/api/v1/stores/{STORE_ID}",
    headers=headers
)

print(f"Status: {response.status_code}")
print(f"Store: {response.json()}")

# Créer une facture de test
data = {
    "amount": "29.99",
    "currency": "EUR",
    "orderId": "test_order_123"
}

response = requests.post(
    f"{SERVER_URL}/api/v1/stores/{STORE_ID}/invoices",
    headers=headers,
    json=data
)

print(f"Invoice: {response.json()}")
```

## Maintenance

### Mises à Jour

#### Mise à Jour de l'Application

1. **Préparer la nouvelle version**
   ```powershell
   # Mettre à jour le code
   git pull origin main
   
   # Mettre à jour la version dans src/__init__.py
   # Mettre à jour CHANGELOG.md
   
   # Rebuild
   .\build\build_exe.ps1
   ```

2. **Distribuer la mise à jour**
   - Uploader sur le serveur de distribution
   - Notifier les utilisateurs
   - Optionnel : Implémenter un système de mise à jour automatique

#### Mise à Jour BTCPay Server

```bash
# SSH sur le VPS
cd /var/lib/docker/volumes/generated_btcpay_datadir/_data

# Backup
./backup.sh

# Mise à jour
cd ~/btcpayserver-docker
git pull
./btcpay-update.sh
```

### Sauvegardes

#### Sauvegarde Client (Utilisateurs)

Les utilisateurs doivent sauvegarder :
- `sessions/` : Sessions Telegram chiffrées
- `config/` : Configuration et licences

#### Sauvegarde Serveur BTCPay

```bash
# Script de backup automatique
#!/bin/bash

BACKUP_DIR="/backup/btcpay"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup volumes Docker
docker run --rm \
  -v btcpayserver_datadir:/data \
  -v $BACKUP_DIR:/backup \
  alpine \
  tar czf /backup/btcpay_data_$DATE.tar.gz /data

# Retention : garder 30 jours
find $BACKUP_DIR -name "btcpay_data_*.tar.gz" -mtime +30 -delete

# Backup base de données PostgreSQL
docker exec btcpayserver_postgres \
  pg_dump -U postgres btcpayserver \
  > $BACKUP_DIR/btcpay_db_$DATE.sql
```

Ajoutez au crontab :
```bash
0 2 * * * /root/backup_btcpay.sh
```

### Nettoyage

#### Nettoyage Logs Client

```powershell
# Supprimer les logs de plus de 90 jours
Get-ChildItem -Path "logs" -Filter "*.log" | 
  Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-90)} | 
  Remove-Item
```

#### Nettoyage Factures BTCPay

Les factures expirées peuvent être archivées manuellement via l'interface BTCPay.

## Sécurité

### Sécurité de l'Application

#### Chiffrement des Sessions

- **Algorithme** : AES-256 via Fernet (cryptography)
- **Dérivation de clé** : PBKDF2 avec 100,000 itérations
- **Salt** : Unique par installation, stocké dans `config/.salt`

#### Protection des Données

- Sessions Telegram : Chiffrées au repos
- API Keys : Jamais loggées en clair
- Mots de passe : Jamais stockés (seulement pour 2FA temporaire)

#### Recommandations

1. **Permissions fichiers** : Restreindre l'accès au dossier `sessions/`
2. **Antivirus** : Ajouter une exception pour AutoTele.exe
3. **Firewall** : Autoriser les connexions Telegram et BTCPay
4. **Updates** : Maintenir l'application à jour

### Sécurité du Serveur BTCPay

#### Hardening du VPS

```bash
# Désactiver root login
sed -i 's/PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config

# Configurer le firewall
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Fail2ban
apt install fail2ban
systemctl enable fail2ban
```

#### SSL/TLS

BTCPay utilise Let's Encrypt automatiquement. Vérifiez le renouvellement :

```bash
certbot renew --dry-run
```

#### API Key Rotation

Changez régulièrement les API keys :
1. Générez une nouvelle clé dans BTCPay
2. Mettez à jour la configuration
3. Testez
4. Révoquez l'ancienne clé

## Monitoring

### Logs de l'Application

Emplacement : `logs/`

Fichiers :
- `autotele_YYYYMMDD.log` : Logs applicatifs
- `send_history.json` : Historique des envois

Niveaux :
- INFO : Opérations normales
- WARNING : Avertissements (rate limits, etc.)
- ERROR : Erreurs (échecs d'envoi, etc.)

### Monitoring BTCPay

#### Health Check

```bash
# Vérifier l'état des services
docker ps

# Logs BTCPay
docker logs btcpayserver_btcpayserver_1 --tail 100

# Logs PostgreSQL
docker logs btcpayserver_postgres_1 --tail 100
```

#### Métriques

Utilisez Prometheus + Grafana pour monitorer :
- Nombre de factures créées
- Taux de paiement
- Temps de réponse API
- Espace disque

### Alertes

Configurez des alertes pour :
- Serveur BTCPay down
- Certificat SSL expirant
- Espace disque < 10%
- Erreurs API répétées

## Dépannage

### Problèmes Communs Client

#### "Impossible de se connecter à Telegram"

**Causes** :
- Connexion Internet
- Identifiants API invalides
- Telegram bloqué (pare-feu)

**Solutions** :
1. Vérifier la connexion
2. Vérifier api_id et api_hash
3. Tester sur un autre réseau
4. Vérifier les logs : `logs/autotele_*.log`

#### "Licence invalide"

**Causes** :
- Facture BTCPay non payée
- Clé de licence incorrecte
- BTCPay server inaccessible

**Solutions** :
1. Vérifier l'état de la facture sur BTCPay
2. Vérifier la connexion au serveur BTCPay
3. Consulter les logs de vérification

#### "Session expirée"

**Causes** :
- Déconnexion Telegram
- Session corrompue
- Changement de mot de passe Telegram

**Solutions** :
1. Supprimer et réajouter le compte
2. Vérifier les fichiers dans `sessions/`

### Problèmes Communs Serveur

#### BTCPay Server Inaccessible

```bash
# Vérifier les services
docker ps -a

# Redémarrer BTCPay
cd ~/btcpayserver-docker
./btcpay-down.sh
./btcpay-up.sh

# Vérifier les logs
docker logs btcpayserver_btcpayserver_1 --tail 200
```

#### Factures Non Créées

**Diagnostic** :
1. Vérifier les permissions API
2. Tester l'API manuellement
3. Vérifier les logs BTCPay

```bash
# Test API
curl -H "Authorization: token YOUR_API_KEY" \
  https://btcpay.votre-domaine.com/api/v1/stores/YOUR_STORE_ID
```

#### Synchronisation Blockchain Lente

C'est normal lors de la première installation. Patientez ou utilisez un snapshot :

```bash
# Utiliser un snapshot Bitcoin (optionnel)
cd ~/btcpayserver-docker
./btcpay-down.sh
./btcpay-restore.sh /path/to/snapshot
./btcpay-up.sh
```

### Support Technique

Pour une assistance supplémentaire :

1. **Documentation BTCPay** : https://docs.btcpayserver.org
2. **Telegram BTCPay** : https://t.me/btcpayserver
3. **Logs** : Fournir les logs pertinents (sans données sensibles)
4. **Configuration** : Décrire votre setup (OS, versions, etc.)

## Checklist de Déploiement

### Avant le Lancement

- [ ] BTCPay Server déployé et fonctionnel
- [ ] Store créé et configuré
- [ ] API key générée avec bonnes permissions
- [ ] Wallet Bitcoin configuré
- [ ] SSL actif et valide
- [ ] Application buildée et testée
- [ ] Configuration BTCPay dans app_config.json
- [ ] Tests d'achat de licence effectués
- [ ] Documentation mise à jour
- [ ] Backup configuré
- [ ] Monitoring en place

### Post-Lancement

- [ ] Surveiller les premiers paiements
- [ ] Vérifier les logs régulièrement
- [ ] Collecter les feedbacks utilisateurs
- [ ] Planifier les mises à jour
- [ ] Tester la restauration depuis backup

---

Pour toute question technique, consultez la documentation complète ou contactez le support.

© 2025 AutoTele - Documentation Administrateur

