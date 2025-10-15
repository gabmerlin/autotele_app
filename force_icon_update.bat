@echo off
echo ========================================
echo FORCE UPDATE DES ICONES WINDOWS
echo ========================================
echo.

echo [1/5] Arret de l'explorateur Windows...
taskkill /f /im explorer.exe >nul 2>&1

echo [2/5] Suppression du cache d'icones...
del /q "%localappdata%\IconCache.db" >nul 2>&1
del /q "%localappdata%\Microsoft\Windows\Explorer\iconcache*.db" >nul 2>&1
del /q "%localappdata%\Microsoft\Windows\Explorer\thumbcache*.db" >nul 2>&1

echo [3/5] Suppression des cles de registre d'icones...
reg delete "HKEY_CURRENT_USER\Software\Classes\Local Settings\Software\Microsoft\Windows\Shell\MuiCache" /f >nul 2>&1

echo [4/5] Redemarrage de l'explorateur...
start explorer.exe
timeout /t 3 /nobreak >nul

echo [5/5] Mise a jour des icones system...
ie4uinit.exe -show >nul 2>&1
ie4uinit.exe -ClearIconCache >nul 2>&1

echo.
echo ========================================
echo MISE A JOUR TERMINEE !
echo ========================================
echo.
echo Les icones ont ete forcees a se mettre a jour.
echo Redemarrez votre ordinateur si le probleme persiste.
echo.
pause
