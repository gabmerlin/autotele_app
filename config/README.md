# Configuration AutoTele

Ce dossier contient les fichiers de configuration de l'application.

## Fichiers

### Configuration Administrateur (à créer une seule fois)

#### Credentials Telegram

**Pour l'administrateur uniquement** - À configurer avant la distribution :

1. Copiez `telegram_credentials.example.json` vers `telegram_credentials.json`
2. Obtenez vos credentials sur https://my.telegram.org
3. Remplissez le fichier :

```json
{
  "api_id": "12345678",
  "api_hash": "abcdef1234567890abcdef1234567890"
}
```

**Alternative recommandée** : Variables d'environnement
```powershell
$env:AUTOTELE_API_ID = "12345678"
$env:AUTOTELE_API_HASH = "abcdef..."
```

📖 **Guide complet** : `docs/SETUP_CREDENTIALS.md`

⚠️ **Ces credentials sont partagés par tous les utilisateurs de l'application**

### Fichiers Utilisateur (générés automatiquement)

- `app_config.json` : Configuration générale de l'application
- `license.json` : Informations de licence
- `scheduled_tasks.json` : Tâches planifiées
- `sessions_index.json` : Index des sessions Telegram
- `.salt` : Salt pour le chiffrement

**⚠️ Ne pas modifier manuellement ces fichiers**

### Fichier BTCPay (à créer)

1. Copiez `btcpay_config.example.json` vers `btcpay_config.json`
2. Remplissez avec vos vraies informations BTCPay :

```json
{
  "server_url": "https://btcpay.votre-domaine.com",
  "store_id": "ABC123...",
  "api_key": "votre_api_key",
  "webhook_secret": "secret_fort",
  "subscription_price": 29.99,
  "currency": "EUR",
  "trial_days": 7,
  "check_interval_hours": 24
}
```

### Comment Obtenir les Informations BTCPay

#### 1. Server URL
L'URL de votre installation BTCPay Server  
Exemple : `https://btcpay.exemple.com`

#### 2. Store ID
1. Connectez-vous à BTCPay
2. Allez dans **Store Settings**
3. L'URL contient le Store ID : `/stores/[STORE_ID]/...`

Ou via API :
```bash
curl -H "Authorization: token YOUR_API_KEY" \
  https://btcpay.exemple.com/api/v1/stores
```

#### 3. API Key
1. **Account Settings** → **API Keys** → **Generate Key**
2. Permissions nécessaires :
   - `View invoices`
   - `Create invoice`
3. Copiez la clé immédiatement (ne sera plus affichée)

#### 4. Webhook Secret (optionnel)
Générez un secret fort :
```bash
openssl rand -base64 32
```

## Sécurité

🔒 **Important** :
- Ne commitez JAMAIS ces fichiers dans Git
- Sauvegardez `btcpay_config.json` de manière sécurisée
- Ne partagez jamais l'API key
- Renouvelez l'API key tous les 6 mois

## Documentation

Pour plus d'informations, consultez :
- `docs/BTCPay_integration.md` : Guide complet BTCPay
- `docs/admin_guide.md` : Guide administrateur

---

© 2025 AutoTele

