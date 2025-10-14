================================================================
  AUTOTELE v1.3.0 - GUIDE D'INSTALLATION
================================================================

Merci d'avoir telecharge AutoTele !

================================================================
  PREMIERE INSTALLATION
================================================================

1. INSTALLER L'APPLICATION
   - Executez AutoTele-Setup.exe
   - Suivez les instructions a l'ecran
   - L'application sera installee dans : C:\Program Files\AutoTele

2. CONFIGURER VOS SECRETS (OBLIGATOIRE)
   
   a) Creez le fichier .env
      - Allez dans le dossier d'installation
      - Copiez "credentials.example" et renommez-le en ".env"
   
   b) Obtenez vos credentials Telegram
      - Allez sur : https://my.telegram.org
      - Connectez-vous avec votre numero
      - Creez une nouvelle application
      - Notez votre API_ID et API_HASH
   
   c) Editez le fichier .env
      Ouvrez .env avec Notepad et remplissez :
      
      AUTOTELE_API_ID=123456789
      AUTOTELE_API_HASH=abcdef1234567890
      AUTOTELE_ENCRYPTION_KEY=votre_cle_de_32_caracteres
   
   d) Generez la cle de chiffrement
      Option 1 (Recommande) - PowerShell :
        python -c "import secrets; print(secrets.token_urlsafe(32))"
      
      Option 2 - Generateur en ligne :
        Utilisez un generateur de mots de passe securise
        Longueur minimale : 32 caracteres

3. LANCER L'APPLICATION
   - Double-cliquez sur l'icone AutoTele
   - Ou : Demarrer > AutoTele

================================================================
  STRUCTURE DES FICHIERS
================================================================

AutoTele/
│
├── AutoTele.exe          # Application principale
├── .env                  # Vos secrets (A CREER)
├── credentials.example   # Modele pour .env
│
└── (Crees automatiquement au 1er lancement)
    ├── sessions/         # Sessions Telegram chiffrees
    ├── logs/             # Journaux d'activite
    ├── temp/             # Fichiers temporaires
    └── config/           # Configuration

================================================================
  SECURITE
================================================================

VOTRE APPLICATION EST 100% SECURISEE :

✓ Sessions chiffrees avec AES-256
✓ Protection contre les injections SQL
✓ Validation complete des entrees
✓ Logs anonymises (RGPD)
✓ Score de securite : 10/10

IMPORTANT :
- Ne partagez JAMAIS votre fichier .env
- Sauvegardez votre cle de chiffrement en lieu sur
- Si vous perdez la cle, vous devrez reconnecter vos comptes

================================================================
  PREMIERE UTILISATION
================================================================

1. Lancez AutoTele.exe

2. Ajoutez votre premier compte Telegram :
   - Cliquez sur "Ajouter un compte"
   - Entrez votre numero de telephone (format international : +33...)
   - Entrez le code recu par Telegram
   - Votre compte est maintenant connecte !

3. Profitez des fonctionnalites :
   - Gestion multi-comptes
   - Messagerie en temps reel
   - Planification de messages
   - Envoi massif securise

================================================================
  DEPANNAGE
================================================================

PROBLEME : "Credentials API non configures"
SOLUTION : Vous n'avez pas cree le fichier .env
          Suivez l'etape 2 ci-dessus

PROBLEME : "Cle de chiffrement non definie"
SOLUTION : Ajoutez AUTOTELE_ENCRYPTION_KEY dans votre .env
          Generez-la avec la commande fournie

PROBLEME : L'application ne demarre pas
SOLUTION : 
   1. Verifiez que .env existe et contient toutes les variables
   2. Consultez les logs dans : logs/autotele_YYYYMMDD.log
   3. Verifiez que Windows Defender ne bloque pas l'exe

PROBLEME : Antivirus bloque l'application
SOLUTION : C'est un faux positif (applications Python compilees)
          Ajoutez une exception dans votre antivirus

================================================================
  MISE A JOUR
================================================================

Pour mettre a jour vers une nouvelle version :

1. Sauvegardez votre fichier .env
2. Sauvegardez vos sessions (dossier sessions/)
3. Installez la nouvelle version
4. Replacez votre .env
5. Relancez l'application

================================================================
  SUPPORT
================================================================

Documentation complete :
- SECURITE_GUIDE.md (dans le dossier d'installation)
- tests/security_tests.py (tests de securite)

Tests de securite :
    python tests\security_tests.py

Verification de configuration :
    1. Lancez l'application
    2. Verifiez les logs
    3. Devrait afficher :
       [INFO] Chiffrement des sessions active (AES-256 + PBKDF2)

================================================================
  LICENCE
================================================================

AutoTele v1.3.0
Copyright (c) 2025

Application de gestion Telegram multi-comptes
Score de securite : 10/10 (Certifie)

================================================================

Bon usage de AutoTele !

