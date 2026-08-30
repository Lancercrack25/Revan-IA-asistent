@echo off
title REVAN // NETWORK DIAGNOSTIC - NETSTAT
color 0B
cls
echo   REVAN PROTOCOL V1.0 // ACTIVE CONNECTIONS SCAN
echo.
echo [+] Mapeando sockets y puertos activos...
echo.
netstat -ano | findstr /i "ESTABLISHED LISTENING"
echo.
echo   ANÁLISIS DE SOCKETS COMPLETADO.
pause > nul