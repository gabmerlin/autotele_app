@echo off
REM Script de compilation automatique pour AutoTele
REM Cree l'executable et l'installateur Windows

echo.
echo ================================================================
echo   COMPILATION AUTOTELE v1.3.0
echo ================================================================
echo.

REM Verifier que l'environnement virtuel est active
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [+] Environnement virtuel active
) else (
    echo [!] Environnement virtuel non trouve
    echo [!] Veuillez activer votre environnement virtuel d'abord
    pause
    exit /b 1
)

echo.
echo [*] Etape 1/4 : Tests de securite...
echo.

REM Executer les tests de securite
python tests\security_tests.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Les tests de securite ont echoue !
    echo [!] Veuillez corriger les problemes avant de compiler
    pause
    exit /b 1
)

echo.
echo [*] Etape 2/4 : Nettoyage des anciens builds...
echo.

REM Nettoyer les anciens builds
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo [+] Nettoyage termine

echo.
echo [*] Etape 3/4 : Compilation avec PyInstaller...
echo.

REM Compiler avec PyInstaller
pyinstaller autotele.spec --clean --log-level WARN

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [-] ERREUR lors de la compilation !
    pause
    exit /b 1
)

echo [+] Executable cree : dist\AutoTele.exe

echo.
echo [*] Etape 4/4 : Verification de l'executable...
echo.

REM Verifier que l'exe existe
if exist dist\AutoTele.exe (
    echo [+] AutoTele.exe trouve
    
    REM Afficher la taille
    for %%A in (dist\AutoTele.exe) do (
        set size=%%~zA
        set /a sizeMB=!size! / 1048576
        echo [+] Taille : !sizeMB! MB
    )
) else (
    echo [-] AutoTele.exe non trouve !
    pause
    exit /b 1
)

echo.
echo ================================================================
echo   [+] COMPILATION TERMINEE AVEC SUCCES !
echo ================================================================
echo.
echo Executable cree : dist\AutoTele.exe
echo.
echo Prochaines etapes :
echo   1. Tester l'executable : dist\AutoTele.exe
echo   2. Creer l'installateur (optionnel) :
echo      - Installer Inno Setup
echo      - Executer : iscc installer.iss
echo.
pause

