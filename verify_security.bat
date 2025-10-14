@echo off
REM Script de verification de securite pour AutoTele
REM Execute tous les tests de securite automatises

echo.
echo ================================================================
echo   VERIFICATION DE SECURITE AUTOTELE v1.3.0
echo ================================================================
echo.

REM Activer l'environnement virtuel
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [+] Environnement virtuel active
) else (
    echo [!] Environnement virtuel non trouve
)

echo.
echo [*] Execution des tests de securite...
echo.

REM Executer les tests
python tests\security_tests.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================
    echo   [+] VERIFICATION TERMINEE - TOUS LES TESTS PASSES
    echo ================================================================
    echo.
    pause
    exit /b 0
) else (
    echo.
    echo ================================================================
    echo   [-] VERIFICATION ECHOUEE - DES TESTS ONT ECHOUE
    echo ================================================================
    echo.
    pause
    exit /b 1
)

