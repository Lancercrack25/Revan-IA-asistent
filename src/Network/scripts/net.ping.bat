@echo off
title REVAN // NETWORK DIAGNOSTIC - PING
color 0A
cls
echo   REVAN PROTOCOL V1.0 // TACTICAL PING DIAGNOSTIC
echo.
echo [+] Enviando paquetes de prueba a: %1
echo.
ping %1 -n 5
echo.
echo   ANÁLISIS DE RED FINALIZADO. Presiona cualquier tecla.
pause > nul