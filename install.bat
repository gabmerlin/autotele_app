@echo off
REM AutoTele - Installation Simple
echo ===================================
echo   AutoTele - Installation
echo ===================================
echo.

cd /d "%~dp0"

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERREUR] Python non trouvé. Installez Python 3.11+ depuis python.org
    pause
    exit /b 1
)

echo [INFO] Python détecté
python --version
echo.

REM Créer l'environnement virtuel
if not exist "venv" (
    echo [INFO] Création de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo [ERREUR] Impossible de créer l'environnement virtuel
        pause
        exit /b 1
    )
    echo [OK] Environnement virtuel créé
)

REM Activer l'environnement
echo [INFO] Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Installer les dépendances
echo [INFO] Installation des dépendances...
pip install nicegui telethon cryptography requests python-dateutil aiofiles Pillow

if errorlevel 1 (
    echo [ERREUR] Erreur lors de l'installation
    pause
    exit /b 1
)

echo.
echo ===================================
echo   Installation terminée !
echo ===================================
echo.
echo Pour lancer l'application :
echo   launch.bat
echo.
pause
