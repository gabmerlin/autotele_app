# Intégration BTCPay Server - Guide Technique

Ce document détaille l'intégration technique entre AutoTele et BTCPay Server pour la gestion des licences et abonnements.

## Vue d'Ensemble

AutoTele utilise BTCPay Server comme solution de paiement et de gestion d'abonnements. L'intégration permet :

- ✅ Création de factures de paiement
- ✅ Vérification du statut de paiement
- ✅ Activation automatique de licences
- ✅ Vérification périodique de la validité
- ✅ Gestion des abonnements mensuels

## Architecture

```
┌─────────────────┐                    ┌──────────────────┐
│  AutoTele       │                    │  BTCPay Server   │
│  (Client)       │                    │  (VPS)           │
├─────────────────┤                    ├──────────────────┤
│                 │                    │                  │
│ LicenseManager  │────── HTTPS ──────>│  REST API        │
│                 │                    │  /api/v1/        │
│  - check()      │<────── JSON ───────│                  │
│  - activate()   │                    │  - Stores        │
│  - verify()     │                    │  - Invoices      │
│                 │                    │  - Payments      │
└─────────────────┘                    └──────────────────┘
```

## Configuration BTCPay Server

### 1. Installation BTCPay

Suivez le guide officiel : https://docs.btcpayserver.org/Deployment/

**Recommandation** : Déploiement Docker sur VPS Ubuntu

```bash
# Installation rapide
git clone https://github.com/btcpayserver/btcpayserver-docker
cd btcpayserver-docker

export BTCPAY_HOST="btcpay.votre-domaine.com"
export BTCPAYGEN_CRYPTO1="btc"
export BTCPAYGEN_CRYPTO2="ltc"

./btcpay-setup.sh -i
```

### 2. Configuration du Store

#### Création du Store

1. Connectez-vous à BTCPay : `https://btcpay.votre-domaine.com`
2. **Stores** → **Create a new store**
3. Paramètres :
   - **Store Name** : `AutoTele Subscriptions`
   - **Default Currency** : `EUR` (ou `USD`)

#### Configuration du Wallet

1. Dans votre store, allez dans **Wallets** → **Bitcoin**
2. Options :
   - **Import existing wallet** (si vous avez déjà un wallet)
   - **Create new wallet** (génère un nouveau wallet)
3. Sauvegardez votre seed phrase en lieu sûr !

#### Paramètres du Store

**General Settings** :
- Invoice expires after : `24 hours`
- Payment invalid after : `15 minutes`
- Consider invoice confirmed after : `1 block`
- Consider invoice paid after : `0 confirmations` (pour tests rapides)

**Checkout Experience** :
- Default language : `French`
- Require refund email : `No`
- Redirect URL after payment : `https://votre-site.com/thanks`

### 3. Génération de l'API Key

#### Étapes

1. **Account Settings** (icône utilisateur) → **API Keys**
2. Cliquez sur **Generate Key**
3. Configuration :
   - **Label** : `AutoTele Application`
   - **Permissions** :
     - ✅ `View invoices`
     - ✅ `Create invoice`
     - ✅ `Modify invoices`
     - ✅ `Modify stores webhooks`
     - ✅ `View your stores`
4. Cliquez sur **Generate**
5. **Copiez la clé immédiatement** (elle ne sera plus affichée)

#### Format de la Clé

```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0
```

### 4. Configuration des Webhooks (Optionnel)

Pour des notifications en temps réel :

1. **Store Settings** → **Webhooks** → **Create Webhook**
2. Configuration :
   - **Payload URL** : `https://votre-backend.com/webhooks/btcpay`
   - **Secret** : Générez un secret fort (ex: `openssl rand -base64 32`)
   - **Events** :
     - ✅ `InvoiceReceivedPayment`
     - ✅ `InvoiceSettled`
     - ✅ `InvoiceExpired`
3. Sauvegardez

## Configuration AutoTele

### Fichier de Configuration

Créez ou modifiez `config/btcpay_config.json` :

```json
{
  "server_url": "https://btcpay.votre-domaine.com",
  "store_id": "VOTRE_STORE_ID_ICI",
  "api_key": "VOTRE_API_KEY_ICI",
  "webhook_secret": "votre_webhook_secret",
  "subscription_price": 29.99,
  "currency": "EUR",
  "trial_days": 7,
  "check_interval_hours": 24
}
```

#### Comment Obtenir le Store ID

Méthode 1 : Via l'URL
- Allez dans **Store Settings**
- L'URL ressemble à : `https://btcpay.votre-domaine.com/stores/ABC123...`
- Le Store ID est : `ABC123...`

Méthode 2 : Via l'API
```bash
curl -H "Authorization: token VOTRE_API_KEY" \
  https://btcpay.votre-domaine.com/api/v1/stores
```

### Variables d'Environnement (Alternative)

Au lieu du fichier JSON, vous pouvez utiliser des variables d'environnement :

```powershell
# Windows PowerShell
$env:AUTOTELE_BTCPAY_URL = "https://btcpay.votre-domaine.com"
$env:AUTOTELE_BTCPAY_STORE_ID = "ABC123..."
$env:AUTOTELE_BTCPAY_API_KEY = "your_api_key..."
```

## Flux de Paiement

### 1. Création d'une Facture

#### Côté Client (AutoTele)

```python
# Dans license_manager.py
def create_payment_invoice(self):
    headers = {
        "Authorization": f"token {self.api_key}",
        "Content-Type": "application/json"
    }
    
    # Générer un order_id unique (servira de license key)
    order_id = generate_token(32)
    
    data = {
        "amount": "29.99",
        "currency": "EUR",
        "orderId": order_id,
        "metadata": {
            "machineId": self.license_data["machine_id"],
            "product": "AutoTele Monthly Subscription"
        },
        "checkout": {
            "redirectURL": "https://votre-site.com/success",
            "redirectAutomatically": False
        }
    }
    
    response = requests.post(
        f"{self.btcpay_url}/api/v1/stores/{self.store_id}/invoices",
        headers=headers,
        json=data,
        timeout=10
    )
    
    if response.status_code in [200, 201]:
        invoice = response.json()
        return invoice["checkoutLink"], order_id
```

#### Réponse BTCPay

```json
{
  "id": "invoice_id_123",
  "checkoutLink": "https://btcpay.votre-domaine.com/i/abc123",
  "status": "new",
  "amount": "29.99",
  "currency": "EUR",
  "orderId": "license_key_abc123...",
  "createdTime": 1234567890
}
```

### 2. Paiement Utilisateur

1. L'utilisateur clique sur "Acheter un abonnement"
2. Une facture est créée sur BTCPay
3. L'order_id (license key) est affiché à l'utilisateur
4. Le navigateur s'ouvre sur la page de paiement BTCPay
5. L'utilisateur paye en Bitcoin (ou autre crypto)
6. BTCPay confirme le paiement
7. L'utilisateur revient dans AutoTele et entre sa license key

### 3. Vérification du Paiement

#### Au moment de l'activation

```python
def _verify_license_with_btcpay(self, license_key):
    headers = {
        "Authorization": f"token {self.api_key}",
        "Content-Type": "application/json"
    }
    
    # Chercher la facture par orderId
    url = f"{self.btcpay_url}/api/v1/stores/{self.store_id}/invoices"
    params = {"orderId": license_key}
    
    response = requests.get(url, headers=headers, params=params, timeout=10)
    
    if response.status_code == 200:
        invoices = response.json()
        if invoices:
            invoice = invoices[0]
            # Statuts BTCPay:
            # - new: Non payée
            # - processing: Paiement reçu, en attente de confirmations
            # - settled: Payée et confirmée
            return invoice["status"] in ["settled", "processing"]
    
    return False
```

### 4. Vérification Périodique

L'application vérifie la validité de la licence toutes les 24h :

```python
def check_license_validity(self):
    # Vérifier si l'intervalle est écoulé
    if datetime.now() - self.last_check < self.check_interval:
        return self.is_license_valid()
    
    # Vérifier avec BTCPay
    license_key = self.license_data.get("license_key")
    is_valid = self._verify_license_with_btcpay(license_key)
    
    if is_valid:
        # Renouveler pour 30 jours
        self.license_data["expiry_date"] = (
            datetime.now() + timedelta(days=30)
        ).isoformat()
    else:
        self.license_data["status"] = "expired"
    
    return is_valid
```

## API BTCPay Utilisée

### Endpoints

#### 1. Lister les Stores

```http
GET /api/v1/stores
Authorization: token YOUR_API_KEY
```

**Réponse** :
```json
[
  {
    "id": "store_id_123",
    "name": "AutoTele Subscriptions"
  }
]
```

#### 2. Créer une Facture

```http
POST /api/v1/stores/{storeId}/invoices
Authorization: token YOUR_API_KEY
Content-Type: application/json

{
  "amount": "29.99",
  "currency": "EUR",
  "orderId": "unique_order_id"
}
```

**Réponse** :
```json
{
  "id": "invoice_id",
  "checkoutLink": "https://btcpay.../i/abc",
  "status": "new",
  "amount": "29.99"
}
```

#### 3. Récupérer une Facture

```http
GET /api/v1/stores/{storeId}/invoices/{invoiceId}
Authorization: token YOUR_API_KEY
```

**Réponse** :
```json
{
  "id": "invoice_id",
  "status": "settled",
  "amount": "29.99",
  "currency": "EUR",
  "orderId": "license_key_123",
  "createdTime": 1234567890,
  "metadata": {
    "machineId": "abc123"
  }
}
```

#### 4. Rechercher des Factures

```http
GET /api/v1/stores/{storeId}/invoices?orderId=license_key_123
Authorization: token YOUR_API_KEY
```

### Codes d'État HTTP

- `200` : Succès
- `201` : Créé
- `400` : Mauvaise requête
- `401` : Non autorisé (API key invalide)
- `404` : Non trouvé
- `500` : Erreur serveur

### Statuts de Facture

- `new` : Créée, en attente de paiement
- `processing` : Paiement reçu, en attente de confirmations
- `settled` : Payée et confirmée (VALIDE)
- `expired` : Expirée sans paiement
- `invalid` : Invalidée

## Gestion des Abonnements

### Modèle Mensuel

1. **Activation initiale** : L'utilisateur paye et active avec la license key
2. **Validité** : 30 jours à partir de l'activation
3. **Renouvellement** : L'utilisateur doit payer une nouvelle facture
4. **Vérification** : L'app vérifie tous les jours la validité

### Workflow de Renouvellement

```
Jour 0  : Activation (29.99 EUR payés)
Jour 30 : Licence expire
Jour 30 : L'utilisateur voit "Licence expirée"
Jour 30 : L'utilisateur paye une nouvelle facture
Jour 30 : Nouvelle licence activée pour 30 jours
```

### Période d'Essai

- **Durée** : 7 jours
- **Limitations** : Aucune (accès complet)
- **Après l'essai** : Obligation d'activer une licence

## Webhooks (Avancé)

### Configuration Serveur

Si vous voulez implémenter des webhooks pour des notifications temps réel :

#### Serveur de Réception

```python
# webhook_server.py
from flask import Flask, request, jsonify
import hmac
import hashlib

app = Flask(__name__)
WEBHOOK_SECRET = "votre_webhook_secret"

@app.route('/webhooks/btcpay', methods=['POST'])
def btcpay_webhook():
    # Vérifier la signature
    signature = request.headers.get('BTCPay-Sig')
    body = request.get_data()
    
    expected_sig = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    if signature != f"sha256={expected_sig}":
        return jsonify({"error": "Invalid signature"}), 401
    
    # Traiter l'événement
    event = request.json
    
    if event['type'] == 'InvoiceSettled':
        # Facture payée !
        order_id = event['orderId']
        # TODO: Marquer la licence comme valide
        print(f"License {order_id} activated!")
    
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

#### Types d'Événements

- `InvoiceCreated` : Facture créée
- `InvoiceReceivedPayment` : Paiement reçu (peut être partiel)
- `InvoiceProcessing` : Paiement en cours de confirmation
- `InvoiceSettled` : **Paiement confirmé** ✅
- `InvoiceExpired` : Facture expirée sans paiement
- `InvoiceInvalid` : Facture invalidée

## Tests

### Test Manuel

#### 1. Test de Création de Facture

```python
# test_btcpay_manual.py
import requests

SERVER_URL = "https://btcpay.votre-domaine.com"
API_KEY = "votre_api_key"
STORE_ID = "votre_store_id"

headers = {
    "Authorization": f"token {API_KEY}",
    "Content-Type": "application/json"
}

# Créer une facture de test
data = {
    "amount": "0.01",  # Petit montant pour test
    "currency": "EUR",
    "orderId": "test_123"
}

response = requests.post(
    f"{SERVER_URL}/api/v1/stores/{STORE_ID}/invoices",
    headers=headers,
    json=data
)

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Ouvrir le lien de paiement
checkout_link = response.json()["checkoutLink"]
print(f"\nPay here: {checkout_link}")
```

#### 2. Test de Vérification

```python
# Après avoir payé la facture de test
order_id = "test_123"

response = requests.get(
    f"{SERVER_URL}/api/v1/stores/{STORE_ID}/invoices",
    headers=headers,
    params={"orderId": order_id}
)

invoices = response.json()
if invoices:
    status = invoices[0]["status"]
    print(f"Invoice status: {status}")
    print(f"Valid: {status in ['settled', 'processing']}")
```

### Test sur Testnet (Bitcoin)

Pour éviter de dépenser du vrai Bitcoin pendant les tests :

1. **Reconfigurer BTCPay en Testnet** :
```bash
export NBITCOIN_NETWORK="testnet"
./btcpay-setup.sh -i
```

2. **Obtenir des Testnet Coins** :
   - https://testnet-faucet.mempool.co
   - https://coinfaucet.eu/en/btc-testnet/

3. **Tester le flow complet**

## Sécurité

### Protection de l'API Key

⚠️ **Ne JAMAIS** :
- Commit l'API key dans Git
- Partager l'API key publiquement
- Logger l'API key en clair

✅ **TOUJOURS** :
- Stocker dans un fichier de config ignoré par Git
- Utiliser des variables d'environnement
- Restreindre les permissions au minimum nécessaire
- Révoquer et regénérer en cas de compromission

### HTTPS Obligatoire

Toutes les communications avec BTCPay doivent se faire en HTTPS :

```python
# Bon
SERVER_URL = "https://btcpay.votre-domaine.com"

# ❌ Mauvais
SERVER_URL = "http://btcpay.votre-domaine.com"
```

### Validation des Webhooks

Si vous utilisez des webhooks, validez TOUJOURS la signature :

```python
def verify_webhook_signature(body, signature, secret):
    expected = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return signature == f"sha256={expected}"
```

## Troubleshooting

### Erreur 401 Unauthorized

**Cause** : API key invalide ou permissions insuffisantes

**Solution** :
1. Vérifiez que l'API key est correcte
2. Vérifiez les permissions de la clé
3. Régénérez une nouvelle clé si nécessaire

### Erreur 404 Store Not Found

**Cause** : Store ID incorrect

**Solution** :
1. Listez vos stores : `GET /api/v1/stores`
2. Vérifiez le Store ID dans la config

### Facture Non Trouvée par orderId

**Cause** : orderId mal formé ou facture pas encore indexée

**Solution** :
1. Attendez quelques secondes (indexation)
2. Recherchez par Invoice ID au lieu de orderId
3. Vérifiez l'orthographe de l'orderId

### Status "processing" Bloqué

**Cause** : Attente de confirmations Bitcoin

**Solution** :
- C'est normal, attendez 10-60 minutes (1-6 blocs)
- Pour tests : Configurez "0 confirmations required"

## Resources

- **Documentation BTCPay** : https://docs.btcpayserver.org
- **API Reference** : https://docs.btcpayserver.org/API/Greenfield/v1/
- **Support** : https://chat.btcpayserver.org
- **GitHub** : https://github.com/btcpayserver/btcpayserver

---

© 2025 AutoTele - Intégration BTCPay Server

