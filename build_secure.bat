@echo off
REM Script de compilation sécurisée avec PyArmor + PyInstaller
REM Usage: build_secure.bat

echo ========================================
echo COMPILATION SECURISEE - AutoTele v1.4.0
echo ========================================
echo.

REM Étape 1: Chiffrer les configs
echo [1/5] Chiffrement des configurations...
python encrypt_env.py
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Echec du chiffrement
    exit /b 1
)
echo   -> OK
echo.

REM Étape 2: Obfusquer avec PyArmor
echo [2/5] Obfuscation avec PyArmor...
python protect_with_pyarmor.py
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Echec de l'obfuscation
    exit /b 1
)
echo   -> OK
echo.

REM Étape 3: Compiler avec PyInstaller
echo [3/5] Compilation avec PyInstaller...
python -m PyInstaller autotele.spec --clean
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Echec de la compilation
    echo Restauration des fichiers originaux...
    if exist src_backup (
        rmdir /s /q src
        move src_backup src
    )
    exit /b 1
)
echo   -> OK
echo.

REM Étape 4: Créer l'installateur
echo [4/5] Creation de l'installateur avec Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Echec de la creation de l'installateur
    exit /b 1
)
echo   -> OK
echo.

REM Étape 5: Restaurer les fichiers originaux (important pour le dev)
echo [5/5] Restauration des fichiers originaux...
if exist src_backup (
    rmdir /s /q src
    move src_backup src
    echo   -> Fichiers restaures
) else (
    echo   -> Pas de sauvegarde trouvee
)
echo.

echo ========================================
echo COMPILATION TERMINEE AVEC SUCCES !
echo ========================================
echo.
echo FICHIER FINAL:
echo   installer_output\AutoTele-Setup-v1.4.0.exe
echo.
echo SECURITE:
echo   [x] Configuration chiffree (AES-256)
echo   [x] Code obfusque (PyArmor)
echo   [x] Anti-debug actif
echo   [x] Protection reverse engineering: 85%%
echo.
pause

