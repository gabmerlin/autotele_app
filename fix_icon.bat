@echo off
echo Correction de l'icône de l'exécutable...

REM Copier l'icône à côté de l'exécutable
copy "assets\icon.ico" "dist\AutoTele.ico" >nul 2>&1

REM Forcer la mise à jour du cache d'icônes Windows
echo Mise à jour du cache d'icônes Windows...
ie4uinit.exe -show >nul 2>&1
ie4uinit.exe -ClearIconCache >nul 2>&1

echo Icône corrigée !
pause
