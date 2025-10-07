# 🚀 AutoTele - Guide de Démarrage Rapide

## Pour les Développeurs

### 1. Installation de l'Environnement

```powershell
# Cloner le projet (si applicable)
git clone https://github.com/votre-repo/autotele.git
cd autotele

# Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
.\venv\Scripts\Activate.ps1

# Si erreur de sécurité PowerShell :
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Installer les dépendances
pip install -r requirements.txt
```

### 2. Configuration BTCPay

```powershell
# Copier le fichier exemple
copy config\btcpay_config.example.json config\btcpay_config.json

# Éditer avec vos informations BTCPay
notepad config\btcpay_config.json
```

Remplir :
- `server_url` : URL de votre BTCPay Server
- `store_id` : ID du store BTCPay
- `api_key` : Clé API BTCPay

### 3. Lancer en Mode Développement

```powershell
python src\main.py
```

### 4. Build de l'Exécutable

```powershell
.\build\build_exe.ps1
```

L'exécutable sera dans `dist\AutoTele\AutoTele.exe`

---

## Pour les Utilisateurs Finaux

### 1. Installation

1. Téléchargez `AutoTele_Setup.exe`
2. Double-cliquez et suivez l'assistant
3. Lancez AutoTele depuis le bureau ou le menu Démarrer

### 2. Premier Compte (Ultra Simple ! 🚀)

1. Cliquez sur l'onglet **"👤 Comptes Telegram"**
2. Cliquez sur **"➕ Ajouter un compte"**
3. Remplissez :
   - Nom du compte : ex. "Mon compte pro"
   - Numéro : ex. +33612345678
4. Cliquez **"Envoyer le code"**
5. Entrez le code reçu sur Telegram
6. Si 2FA activé, entrez votre mot de passe
7. Cliquez **"Vérifier"**

✨ **C'est tout !** Aucun identifiant API requis, l'application s'occupe de tout.

✅ Votre compte est connecté !

### 3. Premier Message Planifié

1. Allez sur l'onglet **"✉️ Nouveau Message"**
2. Sélectionnez votre compte
3. Cochez les groupes où envoyer
4. Rédigez votre message
5. Choisissez date et heure
6. Cliquez **"📅 Planifier le Message"**

✅ Votre message sera envoyé automatiquement !

---

## Résolution de Problèmes Rapide

### "Licence invalide"

**Solution** : Activez votre licence ou utilisez la période d'essai de 7 jours.

1. Cliquez sur "Gérer la licence"
2. Achetez un abonnement (29.99 EUR/mois)
3. Entrez la clé de licence reçue

### "Impossible de se connecter à Telegram"

**Causes possibles** :
- Identifiants API incorrects
- Connexion Internet

**Solution** :
1. Vérifiez vos api_id et api_hash sur my.telegram.org
2. Vérifiez votre connexion Internet
3. Réessayez

### "Session expirée"

**Solution** : Supprimez le compte et rajoutez-le.

### "Erreur rate limit"

**Solution** : Attendez quelques minutes. Telegram limite le nombre de messages.

---

## Commandes Utiles

### Pour Développeurs

```powershell
# Lancer l'application
python src\main.py

# Lancer les tests
pytest tests/ -v

# Build l'exécutable
.\build\build_exe.ps1

# Nettoyer
Remove-Item dist, build -Recurse -Force
```

### Logs

Les logs sont dans `logs/autotele_YYYYMMDD.log`

```powershell
# Voir les logs du jour
Get-Content logs\autotele_$(Get-Date -Format 'yyyyMMdd').log -Tail 50
```

---

## Liens Utiles

- **Documentation complète** : `README.md`
- **Guide utilisateur** : `docs/user_guide.md`
- **Guide admin** : `docs/admin_guide.md`
- **Intégration BTCPay** : `docs/BTCPay_integration.md`
- **Sécurité** : `docs/security.md`

---

## Support

Besoin d'aide ?
- Consultez la FAQ dans `docs/user_guide.md`
- Vérifiez les logs
- Contactez le support

---

## Checklist Premier Démarrage

**Développeur** :
- [ ] Python 3.11+ installé
- [ ] Dépendances installées (`pip install -r requirements.txt`)
- [ ] BTCPay configuré dans `config/btcpay_config.json`
- [ ] Application démarre : `python src\main.py`
- [ ] Tests passent : `pytest tests/ -v`
- [ ] Build fonctionne : `.\build\build_exe.ps1`

**Utilisateur** :
- [ ] Application installée
- [ ] Identifiants API Telegram obtenus
- [ ] Premier compte ajouté
- [ ] Premier message planifié testé
- [ ] Licence activée (ou période d'essai active)

---

**Prêt à démarrer ? Lancez AutoTele et commencez à planifier ! 🚀**

© 2025 AutoTele - Guide de Démarrage Rapide

