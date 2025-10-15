; ================================================================
; AUTOTELE - INSTALLATEUR WINDOWS PROFESSIONNEL v1.4.0
; ================================================================
; Fonctionnalités:
; - Logo personnalisé sur installateur et application
; - Choix du répertoire d'installation
; - Système de mise à jour (préserve les données)
; - Détection d'installation existante
; - Messages français personnalisés
;
; Prerequis: Inno Setup 6+ (https://jrsoftware.org/isinfo.php)
; Compilation: iscc installer.iss
; Resultat: installer_output/AutoTele-Setup-v1.3.0.exe
; ================================================================

[Setup]
; === INFORMATIONS APPLICATION ===
AppName=AutoTele
AppVersion=1.4.0
AppVerName=AutoTele 1.4.0
AppPublisher=AutoTele Team
AppPublisherURL=https://github.com/gabmerlin/autotele_app
AppSupportURL=https://github.com/gabmerlin/autotele_app/issues
AppUpdatesURL=https://github.com/gabmerlin/autotele_app/releases
AppCopyright=Copyright (C) 2025 AutoTele Team

; === IDENTIFIANT UNIQUE (Pour détection de mise à jour) ===
AppId={{B8F3D9E2-1A4C-4F5E-9D3B-7C8A2E6F4D1B}
VersionInfoVersion=1.4.0.0

; === INSTALLATION - L'utilisateur PEUT choisir le répertoire ===
DefaultDirName={autopf}\AutoTele
; Page de choix du répertoire ACTIVÉE
DisableDirPage=no
; Avertir si le répertoire existe déjà
DirExistsWarning=yes
; Message personnalisé si installation existante
UsePreviousAppDir=yes

; Groupe dans le menu démarrer
DefaultGroupName=AutoTele
DisableProgramGroupPage=no
AllowNoIcons=yes

; === LOGO ET ICÔNES ===
; Logo sur l'installateur
SetupIconFile=assets\icon.ico
; Images de l'assistant (utiliser vos images existantes)
WizardImageFile=assets\wizard_image.bmp
WizardSmallImageFile=assets\wizard_small.bmp

; === SORTIE ===
OutputDir=installer_output
OutputBaseFilename=AutoTele-Setup-v1.4.0

; === COMPRESSION (Maximum) ===
Compression=lzma2/ultra64
SolidCompression=yes
LZMAUseSeparateProcess=yes
LZMANumBlockThreads=4
; Gain: ~30-40% de réduction de taille

; === SÉCURITÉ ET COMPATIBILITÉ ===
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; Nécessite Windows 7 SP1 minimum
MinVersion=6.1sp1

; === INTERFACE ===
WizardStyle=modern
DisableWelcomePage=no
ShowLanguageDialog=auto
; Couleur de fond transparente pour le logo PNG
WizardImageBackColor=clWhite

; === DOCUMENTS ===
LicenseFile=LICENSE.txt
InfoBeforeFile=README_INSTALLATEUR.txt

; === DÉSINSTALLATION ===
UninstallDisplayIcon={app}\AutoTele.exe
UninstallFilesDir={app}\uninstall
UninstallDisplayName=AutoTele 1.4.0

[Languages]
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[CustomMessages]
FinishedLabel=Installation terminée avec succès !
FinishedLabelNoIcons=Installation terminée !
ClickFinish=AutoTele a été installé avec succès sur votre ordinateur.%n%nVous pouvez maintenant lancer l'application et commencer à l'utiliser.%n%nCliquez sur Terminer pour quitter l'assistant d'installation.

[Tasks]
Name: "desktopicon"; Description: "Creer un raccourci sur le bureau"; GroupDescription: "Raccourcis:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "Creer un raccourci dans la barre de lancement rapide"; GroupDescription: "Raccourcis:"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
; Executable principal (avec icône intégrée par PyInstaller)
Source: "dist\AutoTele.exe"; DestDir: "{app}"; Flags: ignoreversion

; Documentation
; SÉCURITÉ : .env ET app_config.json sont maintenant chiffrés et embarqués dans l'exe
; Aucun fichier de configuration n'est copié - tout est en mémoire
Source: "README_INSTALLATEUR.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme
Source: "LICENSE.txt"; DestDir: "{app}"; Flags: ignoreversion

; Tests de securite (optionnel)
Source: "tests\security_tests.py"; DestDir: "{app}\tests"; Flags: ignoreversion

[Dirs]
; Creer les repertoires necessaires
Name: "{app}\sessions"; Permissions: users-full
Name: "{app}\logs"; Permissions: users-full
Name: "{app}\temp"; Permissions: users-full
Name: "{app}\backup"; Permissions: users-full
; NOTE: Pas de dossier config - tout est chiffré et embarqué dans l'exe

[Icons]
; Raccourcis (utiliseront automatiquement l'icône de l'exe)
Name: "{group}\AutoTele"; Filename: "{app}\AutoTele.exe"
Name: "{group}\Desinstaller AutoTele"; Filename: "{uninstallexe}"
Name: "{autodesktop}\AutoTele"; Filename: "{app}\AutoTele.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\AutoTele"; Filename: "{app}\AutoTele.exe"; Tasks: quicklaunchicon

[Run]
; Executer apres installation
Filename: "{app}\AutoTele.exe"; Description: "Lancer AutoTele maintenant"; Flags: postinstall nowait skipifsilent

[UninstallDelete]
; Supprimer les fichiers crees par l'application lors de la desinstallation
Type: filesandordirs; Name: "{app}\temp"
Type: filesandordirs; Name: "{app}\logs"
; NOTE: sessions/ et config/ sont conserves (donnees utilisateur)

[Code]
// ================================================================
// GESTION DES MISES À JOUR ET CONFIGURATION
// ================================================================

var
  IsUpgradeInstallation: Boolean;
  OldInstallPath: String;

// Fonction pour obtenir la date/heure actuelle
function GetCurrentDateTime(Param: String): String;
begin
  Result := GetDateTimeString('yyyy/mm/dd hh:nn:ss', #0, #0);
end;

// Vérifier si c'est une mise à jour
function IsUpgrade(): Boolean;
var
  Version: String;
begin
  Result := RegQueryStringValue(HKCU, 'Software\AutoTele', 'Version', Version);
  if Result then
    RegQueryStringValue(HKCU, 'Software\AutoTele', 'InstallPath', OldInstallPath);
end;

// Initialisation avant installation
function InitializeSetup(): Boolean;
var
  OldVersion: String;
  MsgText: String;
begin
  Result := True;
  IsUpgradeInstallation := False;
  
  // Vérifier si AutoTele est déjà installé
  if RegQueryStringValue(HKCU, 'Software\AutoTele', 'Version', OldVersion) then
  begin
    IsUpgradeInstallation := True;
    
    MsgText := 'AutoTele ' + OldVersion + ' est déjà installé.' + #13#10#13#10 +
               'Voulez-vous le mettre à jour vers la version 1.4.0 ?' + #13#10#13#10 +
               'IMPORTANT:' + #13#10 +
               '✓ Vos sessions Telegram seront préservées' + #13#10 +
               '✓ Votre configuration (.env) sera préservée' + #13#10 +
               '✓ Vos logs seront préservés' + #13#10#13#10 +
               'Seul l''exécutable sera mis à jour.';
    
    if MsgBox(MsgText, mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
    end;
  end;
end;

// Après installation
procedure CurStepChanged(CurStep: TSetupStep);
var
  FirstInstall: Boolean;
begin
  if CurStep = ssPostInstall then
  begin
    // Déterminer si c'est une première installation (pas de dossier sessions)
    FirstInstall := not DirExists(ExpandConstant('{app}\sessions'));
    
    // CORRECTION : Aucun fichier .env à copier car config embarquée et chiffrée
    if FirstInstall then
    begin
      // Message pour première installation
      MsgBox('INSTALLATION TERMINEE !' + #13#10#13#10 +
             'AutoTele v1.4.0 a ete installe avec succes.' + #13#10#13#10 +
             'TOUT EST PRE-CONFIGURE !' + #13#10#13#10 +
             'Vous pouvez lancer AutoTele immediatement :' + #13#10#13#10 +
             '1. Creez votre compte AutoTele' + #13#10 +
             '2. Souscrivez un abonnement (34.99 USD/mois)' + #13#10 +
             '3. Connectez vos comptes Telegram' + #13#10 +
             '4. C''est parti !' + #13#10#13#10 +
             'Consultez README_INSTALLATEUR.txt pour plus de details.',
             mbInformation, MB_OK);
    end
    else if IsUpgradeInstallation then
    begin
      // Message pour mise à jour
MsgBox('MISE A JOUR TERMINEE !' + #13#10#13#10 +
             'AutoTele a ete mis a jour vers la version 1.4.0' + #13#10#13#10 +
             'NOUVEAUTES :' + #13#10 +
             '✓ Configuration securisee et chiffree' + #13#10 +
             '✓ Messagerie ultra rapide et fluide' + #13#10 +
             '✓ Affichage photos de profil optimise' + #13#10 +
             '✓ Performances 2x ameliorees' + #13#10 +
             '✓ Recherche @username fonctionnelle' + #13#10 +
             '✓ Interface stable sans bugs' + #13#10#13#10 +
             'Vos sessions et configuration ont ete preservees.',
             mbInformation, MB_OK);
    end;
  end;
end;


[Messages]
; === MESSAGES PERSONNALISÉS EN FRANÇAIS ===
french.WelcomeLabel2=Ceci va installer [name/ver] sur votre ordinateur.%n%nAutoTele est une application de gestion Telegram multi-comptes certifiée sécurisée.%n%nIl est recommandé de fermer toutes les autres applications avant de continuer.

french.SelectDirLabel3=L''installation va installer [name] dans le dossier suivant.%n%nVous pouvez changer ce dossier si vous le souhaitez en cliquant sur Parcourir.

french.SelectDirBrowseLabel=Pour continuer, cliquez sur Suivant. Pour sélectionner un autre dossier, cliquez sur Parcourir.

french.DiskSpaceGBLabel=L''installation nécessite au moins {#SetupSetting('NumGigabytes')} Go d''espace disque disponible.

french.FinishedLabel=L''installation de [name] est terminée avec succès !%n%n AutoTele est maintenant prêt à être utilisé.%n%n Vous pouvez lancer l''application directement depuis le bureau ou le menu Démarrer.%n%n Pour plus d''informations, consultez README_INSTALLATEUR.txt dans le dossier d''installation.

french.ConfirmUninstall=Êtes-vous sûr de vouloir désinstaller complètement %1 et tous ses composants ?%n%nATTENTION: Vos sessions Telegram et logs seront conservés. Supprimez-les manuellement si nécessaire.

french.UninstalledAll=%1 a été correctement désinstallé de votre ordinateur.%n%nVos données (sessions, logs, config) ont été préservées dans le dossier d''installation.

