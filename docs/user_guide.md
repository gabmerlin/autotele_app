# Guide Utilisateur AutoTele

Bienvenue dans le guide d'utilisation d'AutoTele, votre outil professionnel de planification de messages Telegram.

## Table des Matières

1. [Installation](#installation)
2. [Premier Démarrage](#premier-démarrage)
3. [Ajouter un Compte Telegram](#ajouter-un-compte-telegram)
4. [Planifier un Message](#planifier-un-message)
5. [Gérer les Tâches](#gérer-les-tâches)
6. [Gestion de la Licence](#gestion-de-la-licence)
7. [FAQ](#faq)

## Installation

### Configuration Requise

- Windows 10 ou supérieur (64-bit)
- Connexion Internet stable
- 500 MB d'espace disque
- Compte(s) Telegram actif(s)

### Étapes d'Installation

1. **Télécharger AutoTele**
   - Téléchargez `AutoTele_Setup.exe` depuis le site officiel
   - Ou téléchargez l'archive ZIP et extrayez-la

2. **Installer l'Application**
   - Double-cliquez sur `AutoTele_Setup.exe`
   - Suivez les instructions de l'assistant d'installation
   - Acceptez la licence d'utilisation
   - Choisissez le dossier d'installation (par défaut : `C:\Program Files\AutoTele`)

3. **Lancer AutoTele**
   - Double-cliquez sur l'icône AutoTele sur votre bureau
   - Ou lancez depuis le menu Démarrer

## Premier Démarrage

### Écran de Licence

Au premier lancement, vous verrez l'écran de gestion de licence :

- **Période d'essai gratuite** : 7 jours pour tester toutes les fonctionnalités
- **Activation** : Achetez un abonnement pour continuer après l'essai

Pour activer une licence :
1. Cliquez sur "Acheter un Abonnement"
2. Complétez le paiement via BTCPay
3. Copiez votre clé de licence
4. Collez-la dans le champ d'activation
5. Cliquez sur "Activer"

### Obtenir vos Identifiants API Telegram

Pour connecter vos comptes Telegram, vous avez besoin d'identifiants API :

1. **Visitez** : https://my.telegram.org
2. **Connectez-vous** avec votre numéro de téléphone Telegram
3. **Cliquez** sur "API development tools"
4. **Remplissez** le formulaire :
   - App title : `AutoTele`
   - Short name : `autotele`
   - Platform : `Desktop`
   - Description : (optionnel)
5. **Notez** votre `api_id` (numérique) et `api_hash` (alphanumérique)

⚠️ **IMPORTANT** : Gardez ces identifiants confidentiels. Ne les partagez jamais.

## Ajouter un Compte Telegram

### Étape 1 : Accéder au Gestionnaire de Comptes

1. Dans l'interface AutoTele, cliquez sur l'onglet **"👤 Comptes Telegram"**
2. Cliquez sur le bouton **"➕ Ajouter un compte"**

### Étape 2 : Entrer les Informations

Dans la fenêtre qui s'ouvre, remplissez :

- **Nom du compte** : Un nom pour identifier ce compte (ex: "Compte Recrutement")
- **Numéro de téléphone** : Votre numéro Telegram au format international (ex: +33612345678)
- **API ID** : L'api_id obtenu sur my.telegram.org
- **API Hash** : L'api_hash obtenu sur my.telegram.org

### Étape 3 : Vérification

1. Cliquez sur **"Envoyer le code"**
2. Vous recevrez un code de vérification sur votre Telegram
3. Entrez le code dans le champ "Code de vérification"
4. Si vous avez activé la double authentification (2FA), entrez votre mot de passe
5. Cliquez sur **"Vérifier"**

✅ Votre compte est maintenant connecté !

### Gérer vos Comptes

- **Voir les comptes** : La liste affiche tous vos comptes avec leur statut
- **Supprimer un compte** : Sélectionnez-le et cliquez sur "🗑️ Supprimer"

## Planifier un Message

### Étape 1 : Créer un Nouveau Message

1. Cliquez sur l'onglet **"✉️ Nouveau Message"**

### Étape 2 : Sélectionner le Compte

1. Dans la section "1️⃣ Sélectionner le Compte", choisissez le compte à utiliser
2. Les groupes et canaux de ce compte seront automatiquement chargés

### Étape 3 : Sélectionner les Groupes

1. Dans la section "2️⃣ Sélectionner les Groupes/Canaux", cochez les groupes cibles
2. Vous pouvez utiliser les boutons :
   - **"Tout sélectionner"** : Sélectionne tous les groupes
   - **"Tout désélectionner"** : Désélectionne tout

⚠️ **Attention** : Sélectionner plus de 50 groupes peut déclencher des limites Telegram

### Étape 4 : Rédiger le Message

1. Dans la section "3️⃣ Contenu du Message", rédigez votre message
2. Le compteur de caractères vous aide à surveiller la longueur
3. Utilisez des emojis et formatage selon vos besoins

**Exemple de message professionnel :**

```
🔔 Nouvelle Offre d'Emploi

Nous recherchons un Développeur Python Senior pour rejoindre notre équipe.

📍 Localisation : Paris / Remote
💰 Salaire : 50-60K€
📅 Début : Dès que possible

Compétences requises :
✅ Python 3.x
✅ Django/FastAPI
✅ PostgreSQL
✅ Docker

Intéressé(e) ? Envoyez votre CV à : recrutement@entreprise.com
```

### Étape 5 : Joindre un Fichier (Optionnel)

1. Cliquez sur **"📎 Joindre un fichier"**
2. Sélectionnez votre fichier (image, PDF, document, etc.)
3. Le nom du fichier s'affiche à l'écran
4. Pour retirer le fichier, cliquez sur **"❌"**

### Étape 6 : Planifier l'Heure

1. Dans la section "4️⃣ Planifier l'Envoi", choisissez la date et l'heure
2. Utilisez les raccourcis rapides :
   - **"+1h"** : Dans 1 heure
   - **"+3h"** : Dans 3 heures
   - **"Demain 9h"** : Demain à 9h00

### Étape 7 : Confirmer et Planifier

1. Vérifiez toutes les informations
2. Cliquez sur **"📅 Planifier le Message"**
3. Confirmez dans la boîte de dialogue
4. ✅ Votre message est planifié !

## Gérer les Tâches

### Tableau de Bord

L'onglet **"📊 Tableau de bord"** affiche toutes vos tâches planifiées.

#### Colonnes du Tableau

- **Statut** : État actuel de la tâche
  - ⏳ En attente
  - ⚙️ En cours
  - ✅ Terminé
  - ❌ Échoué
  - ⚠️ Partiel (certains groupes ont échoué)

- **Compte** : Nom du compte utilisé
- **Groupes** : Nombre de groupes ciblés
- **Message** : Aperçu du message
- **Heure planifiée** : Date et heure d'envoi
- **Actions** : Boutons d'action

#### Actions Disponibles

- **ℹ️ Détails** : Voir les détails complets de la tâche
  - Informations complètes
  - Message entier
  - Résultats par groupe (succès/échecs)

- **🗑️ Supprimer** : Supprimer une tâche en attente
  - Uniquement pour les tâches non encore envoyées

#### Fonctions Utiles

- **🔄 Rafraîchir** : Actualiser la liste des tâches
- **💾 Exporter l'historique** : Exporter toutes les tâches en CSV
- **🗑️ Nettoyer l'historique** : Supprimer les tâches de plus de 30 jours

### Comprendre les Résultats

Après l'envoi d'une tâche, consultez les détails pour voir :

- ✅ **Succès** : Le message a été planifié dans le groupe
- ❌ **Échec** : Erreur lors de la planification
  - Raisons possibles : Droits insuffisants, rate limit, groupe inexistant

## Gestion de la Licence

### Vérifier votre Licence

1. Cliquez sur **"Gérer la licence"** en haut à droite
2. Vous verrez :
   - Statut actuel (Essai ou Actif)
   - Jours restants
   - Date d'expiration

### Renouveler votre Abonnement

1. Dans le dialogue de licence, cliquez sur **"Acheter un Abonnement"**
2. Complétez le paiement via BTCPay
3. Votre licence sera automatiquement renouvelée

### Tarification

- **Période d'essai** : 7 jours gratuits
- **Abonnement mensuel** : 29.99 EUR/mois
- **Paiement** : Crypto via BTCPay Server

## FAQ

### Q : Mes messages seront-ils visibles comme envoyés par moi ?

**R** : Oui ! AutoTele utilise l'API native de Telegram pour créer des **messages planifiés**. Ils apparaîtront exactement comme si vous les aviez planifiés manuellement dans Telegram.

### Q : Puis-je planifier le même message sur plusieurs comptes ?

**R** : Actuellement, une tâche = un compte. Pour envoyer depuis plusieurs comptes, créez une tâche pour chaque compte.

### Q : Y a-t-il des limites Telegram ?

**R** : Oui, Telegram impose des limites :
- Maximum ~20 messages par minute
- Délais automatiques entre les messages (3 secondes)
- Rate limits en cas d'abus

AutoTele respecte automatiquement ces limites.

### Q : Que se passe-t-il si mon ordinateur est éteint à l'heure planifiée ?

**R** : Les messages sont **planifiés** sur les serveurs Telegram. Même si votre PC est éteint, ils seront envoyés à l'heure prévue.

### Q : Puis-je modifier un message déjà planifié ?

**R** : Non, une fois planifié, un message ne peut être que supprimé (si pas encore envoyé). Pour modifier, supprimez la tâche et recréez-la.

### Q : L'application est-elle sécurisée ?

**R** : Oui :
- Sessions Telegram chiffrées AES-256
- Aucune donnée n'est envoyée à un serveur externe
- Code source disponible pour audit

### Q : Puis-je utiliser AutoTele pour du spam ?

**R** : **NON**. AutoTele est conçu pour un usage professionnel légitime (recrutement, communication). Le spam viole :
- Les conditions d'utilisation de Telegram
- Les lois anti-spam
- Les conditions d'utilisation d'AutoTele

Votre compte Telegram peut être banni si vous abusez.

### Q : Comment obtenir du support ?

**R** : 
- Consultez cette documentation
- Vérifiez les logs dans le dossier `logs/`
- Contactez le support technique via le site officiel

### Q : Puis-je utiliser AutoTele sur plusieurs ordinateurs ?

**R** : Une licence = une machine. Pour utiliser sur plusieurs PC, vous devez acheter plusieurs licences.

### Q : Comment exporter mes sessions pour les sauvegarder ?

**R** : Les sessions sont stockées dans le dossier `sessions/`. Vous pouvez sauvegarder ce dossier. **Attention** : Ces fichiers contiennent l'accès à vos comptes Telegram, protégez-les.

## Conseils d'Utilisation Professionnelle

### 1. Organisez vos Comptes

Donnez des noms clairs à vos comptes :
- ✅ "Compte Recrutement IT"
- ✅ "Compte Marketing"
- ❌ "Compte 1"

### 2. Testez d'abord

Avant un envoi massif :
- Testez avec un seul groupe
- Vérifiez que le message s'affiche correctement
- Vérifiez les pièces jointes

### 3. Respectez les Bonnes Pratiques

- Obtenez le consentement des membres
- Proposez toujours une option de désabonnement
- Ne sur-sollicitez pas (max 1-2 messages par semaine)
- Personnalisez vos messages

### 4. Planifiez aux Bonnes Heures

Pour maximiser la visibilité :
- **Offres d'emploi** : Lundi-Jeudi, 9h-10h ou 14h-15h
- **Événements** : 2-3 jours avant
- **Évitez** : Nuit, week-end, jours fériés

### 5. Suivez vos Résultats

- Exportez régulièrement l'historique
- Analysez les taux d'échec
- Ajustez votre stratégie

## Dépannage

### Problème : "Compte non connecté"

**Solution** :
1. Vérifiez votre connexion Internet
2. Réessayez de vous connecter
3. Si le problème persiste, supprimez et réajoutez le compte

### Problème : "Erreur rate limit"

**Solution** :
- Attendez quelques minutes
- Réduisez le nombre de groupes
- Espacez vos envois

### Problème : "Session expirée"

**Solution** :
1. Supprimez le compte
2. Reconnectez-vous avec le même numéro

### Problème : "Droits insuffisants"

**Solution** :
- Vérifiez que vous êtes administrateur du groupe/canal
- Vérifiez que vous avez le droit de publier

## Mentions Légales

AutoTele est un outil professionnel. En l'utilisant, vous acceptez de :
- Respecter les conditions d'utilisation de Telegram
- Respecter les lois anti-spam locales
- Obtenir le consentement des destinataires
- Ne pas utiliser l'outil pour du spam ou des activités illégales

L'éditeur décline toute responsabilité en cas d'utilisation abusive.

---

© 2025 AutoTele - Tous droits réservés

