# Configuration des Credentials Telegram

## 🎯 Pour le Développeur / Administrateur

En tant qu'administrateur de l'application AutoTele, vous devez configurer **UNE SEULE FOIS** les credentials API Telegram. Ces credentials seront utilisés par **tous les utilisateurs** de l'application.

## 📋 Étapes de Configuration

### 1. Obtenir les Credentials API Telegram

1. **Visitez** https://my.telegram.org
2. **Connectez-vous** avec votre numéro de téléphone Telegram personnel
3. **Cliquez** sur "API development tools"
4. **Remplissez** le formulaire :
   - **App title** : `AutoTele Production`
   - **Short name** : `autotele`
   - **Platform** : `Desktop`
   - **Description** : `Application de planification de messages Telegram pour recruteurs`
5. **Copiez** les valeurs :
   - `api_id` : un nombre (ex: 12345678)
   - `api_hash` : une chaîne alphanumérique (ex: abcdef1234567890abcdef1234567890)

### 2. Configurer l'Application

Vous avez **3 méthodes** pour configurer les credentials :

#### Méthode 1 : Variables d'Environnement (Recommandé pour Production)

**Windows PowerShell** :
```powershell
# Variables permanentes
[System.Environment]::SetEnvironmentVariable('AUTOTELE_API_ID', '12345678', 'Machine')
[System.Environment]::SetEnvironmentVariable('AUTOTELE_API_HASH', 'abcdef...', 'Machine')

# Redémarrer pour appliquer
```

**Windows CMD** :
```cmd
setx AUTOTELE_API_ID "12345678" /M
setx AUTOTELE_API_HASH "abcdef..." /M
```

**Linux/Mac** (pour développement) :
```bash
export AUTOTELE_API_ID="12345678"
export AUTOTELE_API_HASH="abcdef..."

# Permanent : ajouter dans ~/.bashrc ou ~/.zshrc
echo 'export AUTOTELE_API_ID="12345678"' >> ~/.bashrc
echo 'export AUTOTELE_API_HASH="abcdef..."' >> ~/.bashrc
```

#### Méthode 2 : Fichier de Configuration

```powershell
# Copier le fichier exemple
copy config\telegram_credentials.example.json config\telegram_credentials.json

# Éditer avec vos valeurs
notepad config\telegram_credentials.json
```

Remplir :
```json
{
  "api_id": "12345678",
  "api_hash": "abcdef1234567890abcdef1234567890"
}
```

#### Méthode 3 : Directement dans le Code (Développement uniquement)

**⚠️ NE PAS UTILISER EN PRODUCTION**

Éditez `src/core/telegram_manager.py` :
```python
DEFAULT_API_ID = "12345678"  # Votre api_id
DEFAULT_API_HASH = "abcdef1234567890"  # Votre api_hash
```

**Important** : Ne commitez jamais ces valeurs dans Git !

### 3. Vérification

**Tester en mode développement** :
```powershell
python src\main.py
```

Si tout est correct, l'application démarre sans erreur.

**Tester l'ajout d'un compte** :
1. Lancez l'application
2. Ajoutez un compte avec juste votre numéro
3. Vous devriez recevoir le code de vérification

Si erreur "api_id invalide", vérifiez votre configuration.

## 🔒 Sécurité

### Protéger les Credentials

Ces credentials sont **critiques** car ils donnent accès à l'API Telegram :

✅ **À FAIRE** :
- Utiliser des variables d'environnement en production
- Ne jamais commiter dans Git
- Restreindre l'accès au serveur/machine
- Surveiller l'usage API sur my.telegram.org
- Documenter où sont stockés les credentials

❌ **À NE PAS FAIRE** :
- Commiter dans Git
- Partager publiquement
- Envoyer par email/chat non chiffré
- Hardcoder dans le code en production
- Donner aux utilisateurs finaux

### Quotas et Limites

Vos credentials API Telegram ont des **quotas partagés** :

- **~1000-10000 requêtes par jour** selon l'historique du compte
- **Rate limits** : 20 requêtes par seconde max
- **Flood limits** : Telegram peut bloquer temporairement en cas d'abus

**Monitoring** :
- Surveillez l'usage sur https://my.telegram.org
- Implémentez des rate limits dans l'app (déjà fait ✅)
- Détectez les utilisateurs abusifs

### Si les Credentials sont Compromis

1. **Immédiat** :
   - Allez sur my.telegram.org
   - Supprimez l'application compromise
   - Créez une nouvelle application
   - Mettez à jour les credentials dans AutoTele

2. **Investigation** :
   - Vérifiez les logs d'accès
   - Identifiez la source de la fuite
   - Notifiez les utilisateurs si nécessaire

## 📊 Monitoring de l'Usage

### Via Telegram

1. Connectez-vous sur https://my.telegram.org
2. Allez dans votre application
3. Consultez les statistiques d'usage

### Dans l'Application

Les logs AutoTele incluent :
- Nombre de requêtes API
- Erreurs de quota
- Rate limits atteints

```powershell
# Voir les erreurs de quota
Get-Content logs\autotele_*.log | Select-String "rate limit|flood"
```

## 🚀 Déploiement

### Build de l'Exécutable

Les credentials doivent être configurés **avant** le build :

```powershell
# Option 1 : Variables d'environnement (recommandé)
$env:AUTOTELE_API_ID = "12345678"
$env:AUTOTELE_API_HASH = "abcdef..."

# Build
.\build\build_exe.ps1
```

Les variables d'environnement seront lues au **runtime**, pas au build time.

### Distribution

**Pour les utilisateurs** :

1. **Documentation** : Indiquez clairement qu'aucun API ID n'est requis
2. **Support** : Préparez une FAQ pour les erreurs de connexion
3. **Monitoring** : Surveillez les quotas surtout les premiers jours

## ❓ FAQ

### Q : Dois-je partager mes credentials avec les utilisateurs ?

**R : NON !** Les utilisateurs n'ont pas besoin de ces credentials. Ils utilisent seulement leur numéro de téléphone + code.

### Q : Puis-je utiliser plusieurs ensembles de credentials ?

**R : Oui**, vous pouvez implémenter une rotation :
```python
CREDENTIAL_POOL = [
    {"api_id": "111", "api_hash": "aaa..."},
    {"api_id": "222", "api_hash": "bbb..."},
]
# Puis choisir aléatoirement ou en round-robin
```

### Q : Que se passe-t-il si je dépasse les quotas ?

**R :** Telegram bloque temporairement (FloodWaitError). L'application gérera automatiquement et demandera d'attendre.

### Q : Les credentials sont-ils visibles dans l'exécutable ?

**R :** Si vous utilisez des variables d'environnement : **NON**.  
Si vous hardcodez : **OUI** (un reverse engineering peut les extraire).

**Solution** : Toujours utiliser des variables d'environnement en production.

### Q : Un utilisateur peut-il utiliser ses propres credentials ?

**R :** Oui, c'est possible mais pas implémenté par défaut. Vous pouvez ajouter une option "Mode avancé" dans l'interface si nécessaire.

## 📞 Support

Pour toute question sur la configuration :
- Documentation complète : `docs/admin_guide.md`
- Intégration : `docs/BTCPay_integration.md`

---

**Dernière mise à jour** : 2025-10-07  
**Version** : 1.0.0

© 2025 AutoTele - Configuration des Credentials

