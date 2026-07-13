# assistente.py — primeira execucao do soundboard: configura o CS2 sozinho.
# Copia cfgs, escolhe o SEU microfone num menu (escreve voz_normal.cfg) e garante os binds
# no autoexec. Tambem oferece o modo --diagnostico (gate executavel do pacote).
import io
import json
import os
import sys

RAIZ = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.abspath(__file__)))
MARCADOR = os.path.join(RAIZ, ".configurado")
CFG_PADRAO = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg"

BINDS_CFG = """// escrito pelo assistente do CS2 Soundboard — nao editar na mao
bind "f3" "exec fala_atual"     // tecla-fantasma do TEXTO do chat
bind "f11" "exec voz_locutor"   // mic do jogo = cabo virtual (soundboard fala)
bind "f4" "exec voz_normal"     // volta pro seu microfone (o soundboard aperta sozinho)
"""


def acha_cfg_dir():
    local = os.path.join(RAIZ, "config_local.json")
    if os.path.exists(local):
        d = json.load(io.open(local, encoding="utf-8")).get("cs2_cfg_dir", "")
        if os.path.isdir(d):
            return d
    if os.path.isdir(CFG_PADRAO):
        return CFG_PADRAO
    return None


def pergunta_cfg_dir():
    print("\nNao achei o CS2 no caminho padrao da Steam.")
    print(r"Cole aqui o caminho da pasta cfg do seu jogo (termina em \game\csgo\cfg):")
    d = input("> ").strip().strip('"')
    if not os.path.isdir(d):
        print("Pasta nao existe. Rode de novo quando achar o caminho."); sys.exit(1)
    json.dump({"cs2_cfg_dir": d}, io.open(os.path.join(RAIZ, "config_local.json"), "w", encoding="utf-8"))
    return d


def copia_cfgs(cfg_dir):
    import shutil
    for nome in ("gamestate_integration_soundboard.cfg", "voz_locutor.cfg"):
        shutil.copy(os.path.join(RAIZ, "cfg", nome), cfg_dir)
    print("[ok] cfgs de integracao copiados")


def escolhe_microfone(cfg_dir):
    import sounddevice as sd
    entradas = [(i, d["name"]) for i, d in enumerate(sd.query_devices())
                if d["max_input_channels"] > 0 and not d["name"].startswith("CABLE Output")]
    # dedup por nome (Windows lista o mesmo mic em varias APIs)
    vistos, mics = set(), []
    for i, nome in entradas:
        if nome not in vistos:
            vistos.add(nome); mics.append((i, nome))
    if not mics:
        print("[aviso] nenhum microfone encontrado — edite voz_normal.cfg depois"); return
    print("\nQual e o SEU microfone (o de verdade, para o F4 devolver a voz)?")
    for n, (_, nome) in enumerate(mics, 1):
        print(f"  {n}) {nome}")
    try:
        esc = int(input("> ").strip())
        nome_mic = mics[esc - 1][1]
    except (ValueError, IndexError):
        print("[aviso] escolha invalida — edite voz_normal.cfg depois"); return
    io.open(os.path.join(cfg_dir, "voz_normal.cfg"), "w", encoding="utf-8").write(
        'voice_device_override "%s"\nvoice_vox 0\necho ">>> VOZ = SEU MICROFONE"\n' % nome_mic)
    print(f"[ok] voz_normal.cfg escrito com: {nome_mic}")


def garante_binds(cfg_dir):
    io.open(os.path.join(cfg_dir, "soundboard_binds.cfg"), "w", encoding="utf-8").write(BINDS_CFG)
    autoexec = os.path.join(cfg_dir, "autoexec.cfg")
    linha = "exec soundboard_binds"
    conteudo = io.open(autoexec, encoding="utf-8", errors="replace").read() if os.path.exists(autoexec) else ""
    if linha not in conteudo:
        if conteudo:
            import shutil
            shutil.copy(autoexec, autoexec + ".bak-soundboard")
        io.open(autoexec, "a", encoding="utf-8").write("\n" + linha + "   // CS2 Soundboard\n")
        print("[ok] binds garantidos no autoexec (backup .bak-soundboard)")
    else:
        print("[ok] autoexec ja tinha os binds")


def tem_cable():
    import sounddevice as sd
    return any(d["name"].startswith("CABLE Input") and d["max_output_channels"] > 0
               for d in sd.query_devices())


def configurar():
    print("=== CS2 Soundboard — assistente de configuracao ===")
    cfg_dir = acha_cfg_dir() or pergunta_cfg_dir()
    print(f"[ok] pasta cfg do CS2: {cfg_dir}")
    copia_cfgs(cfg_dir)
    escolhe_microfone(cfg_dir)
    garante_binds(cfg_dir)
    if tem_cable():
        print("[ok] VB-Cable presente")
    else:
        print("\n[FALTA 1 COISA] Instale o microfone virtual VB-Cable (gratis):")
        print("  https://vb-audio.com/Cable/  → baixe, instale, reinicie o PC")
        print("  Depois e so abrir o soundboard de novo.")
    io.open(MARCADOR, "w").write("ok\n")
    print("\nConfigurado! No jogo: voz 'sempre ativo' (ou segure o PTT junto). Numpad = calls; . = voz.\n")


def diagnostico():
    falhas = []
    cfg_dir = acha_cfg_dir()
    checks = [
        ("pasta cfg do CS2 encontrada", cfg_dir is not None),
        ("sons/ com audios", os.path.isdir(os.path.join(RAIZ, "sons")) and
         len([f for f in os.listdir(os.path.join(RAIZ, "sons")) if f.endswith(".mp3")]) >= 60),
        ("sons_mago/ com audios", os.path.isdir(os.path.join(RAIZ, "sons_mago")) and
         len([f for f in os.listdir(os.path.join(RAIZ, "sons_mago")) if f.endswith(".mp3")]) >= 60),
        ("frases_variacoes.json", os.path.exists(os.path.join(RAIZ, "frases_variacoes.json"))),
        ("VB-Cable instalado", tem_cable()),
    ]
    if cfg_dir:
        checks.append(("gamestate copiado", os.path.exists(os.path.join(cfg_dir, "gamestate_integration_soundboard.cfg"))))
    for nome, ok in checks:
        print(("[ok]  " if ok else "[X]   ") + nome)
        if not ok:
            falhas.append(nome)
    print("DIAGNOSTICO: " + ("VERDE" if not falhas else "VERMELHO (%s)" % ", ".join(falhas)))
    sys.exit(0 if not falhas else 1)
