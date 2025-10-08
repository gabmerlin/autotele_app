@echo off
REM AutoTele - Lancement Simple
echo ===================================
echo   AutoTele - Lancement
echo ===================================
echo.

cd /d "%~dp0"

REM Vérifier l'environnement virtuel
if not exist "venv\Scripts\activate.bat" (
    echo [ERREUR] Environnement virtuel non trouvé
    echo Exécutez d'abord : install.bat
    pause
    exit /b 1
)

REM Activer l'environnement
echo [INFO] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Lancer l'application
echo [INFO] Lancement d'AutoTele...
echo [INFO] L'application s'ouvrira dans votre navigateur
echo.
python src\main.py

pause
