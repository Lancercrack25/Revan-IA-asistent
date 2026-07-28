@echo off
title REVAN // INTRUDER DETECTION SYSTEM
color 0C
cls
echo   REVAN PROTOCOL V1.0 // ESCANEO DE INTRUSOS EN RED LOCAL
echo.
echo [+] Obteniendo puerta de enlace y mapeando tabla ARP...
echo.

:: Muestra todos los dispositivos conectados a la red local (Dirección IP y MAC)
arp -a

echo.
echo   ANALISIS ARP FINALIZADO.
echo   Si ves direcciones MAC desconocidas, revisa tu router.
echo.
pause > nul