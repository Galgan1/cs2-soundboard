# instalar-remoto.ps1 — CS2 Soundboard em UM comando (sem git):
#   powershell -ExecutionPolicy Bypass -c "irm https://raw.githubusercontent.com/Galgan1/cs2-soundboard/main/instalar-remoto.ps1 | iex"
$ErrorActionPreference = "Stop"
$repoZip = "https://github.com/Galgan1/cs2-soundboard/archive/refs/heads/main.zip"
$destino = Join-Path $env:USERPROFILE "cs2-soundboard"
Write-Host "=== CS2 Soundboard - instalador de 1 comando ===" -ForegroundColor Cyan

# [1/4] Python
if (Get-Command python -ErrorAction SilentlyContinue) {
    Write-Host "[1/4] Python OK"
} else {
    Write-Host "[1/4] Python nao encontrado - instalando via winget..." -ForegroundColor Yellow
    winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "User") + ";" +
                [Environment]::GetEnvironmentVariable("Path", "Machine")
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Host "Feche e reabra o terminal e rode o comando de novo (PATH novo)." -ForegroundColor Yellow
        exit 1
    }
}

# [2/4] baixar e extrair (instalacao anterior vira backup, nunca se apaga)
Write-Host "[2/4] Baixando o soundboard..."
$zip = Join-Path $env:TEMP "cs2-soundboard.zip"
Invoke-WebRequest $repoZip -OutFile $zip
if (Test-Path $destino) {
    $bak = "$destino-antigo-" + (Get-Date -Format "yyyyMMdd-HHmmss")
    Move-Item $destino $bak
    Write-Host "  (instalacao anterior preservada em $bak)"
}
$tmpx = Join-Path $env:TEMP "cs2sb-extract"
if (Test-Path $tmpx) { Remove-Item $tmpx -Recurse -Force }
Expand-Archive $zip -DestinationPath $tmpx
Move-Item (Join-Path $tmpx "cs2-soundboard-main") $destino
Remove-Item $zip -Force

# [3/4] dependencias
Write-Host "[3/4] Instalando dependencias Python..."
python -m pip install -q -r (Join-Path $destino "requirements.txt")

# [4/4] cfgs do CS2
$cfg = "C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg"
if (Test-Path $cfg) {
    Copy-Item (Join-Path $destino "cfg\gamestate_integration_soundboard.cfg") $cfg -Force
    Copy-Item (Join-Path $destino "cfg\voz_locutor.cfg") $cfg -Force
    if (-not (Test-Path (Join-Path $cfg "voz_normal.cfg"))) {
        Copy-Item (Join-Path $destino "cfg\voz_normal.cfg") $cfg
    }
    Write-Host "[4/4] Cfgs copiados para o CS2."
} else {
    Write-Host "[4/4] CS2 fora do caminho padrao da Steam - copie a pasta cfg\ manualmente" -ForegroundColor Yellow
    Write-Host "      e crie $destino\config_local.json apontando cs2_cfg_dir." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== INSTALADO em $destino ===" -ForegroundColor Green
Write-Host "Faltam 3 passos manuais (uma vez so):" -ForegroundColor Yellow
Write-Host "  a) Microfone virtual VB-Cable: https://vb-audio.com/Cable/"
Write-Host "  b) Editar voz_normal.cfg (na pasta cfg do CS2) com o nome do SEU microfone"
Write-Host "  c) Colar o conteudo de cfg\autoexec_trecho.cfg no seu autoexec.cfg"
Write-Host ""
Write-Host "Para jogar:  cd $destino ; python soundboard.py" -ForegroundColor Cyan
