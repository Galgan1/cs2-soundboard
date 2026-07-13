@echo off
chcp 65001 >nul
echo === CS2 Soundboard — instalador ===
where python >nul 2>nul || (echo [ERRO] Instale o Python 3.11+ em python.org (marque "Add to PATH") e rode de novo. & pause & exit /b 1)
echo [1/3] Instalando dependencias Python...
pip install -r "%~dp0requirements.txt" || (echo [ERRO] pip falhou. & pause & exit /b 1)

set "CFG=C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg"
if not exist "%CFG%" (
  echo [AVISO] CS2 nao esta no caminho padrao da Steam.
  echo         Copie a pasta cfg\ manualmente para ...\game\csgo\cfg do seu jogo
  echo         e crie um config_local.json apontando cs2_cfg_dir para la.
  pause & exit /b 1
)
echo [2/3] Copiando cfgs para o CS2...
copy /y "%~dp0cfg\gamestate_integration_soundboard.cfg" "%CFG%" >nul
copy /y "%~dp0cfg\voz_locutor.cfg" "%CFG%" >nul
if not exist "%CFG%\voz_normal.cfg" copy /y "%~dp0cfg\voz_normal.cfg" "%CFG%" >nul

echo [3/3] Pronto o que da pra automatizar. FALTAM 3 passos manuais:
echo   a) Instalar o microfone virtual VB-Cable: https://vb-audio.com/Cable/
echo   b) Editar "%CFG%\voz_normal.cfg" com o nome do SEU microfone (Painel de Som)
echo   c) Colar o conteudo de cfg\autoexec_trecho.cfg no seu autoexec.cfg
echo.
echo Para usar: python soundboard.py   (deixe aberto enquanto joga; numpad = calls, . = voz)
pause
