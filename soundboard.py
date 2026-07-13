# -*- coding: utf-8 -*-
# Soundboard v4 do CS2 — numpad com 3 VARIACOES por call (rodizio), arsenal TR/CT via GSI,
# e TEXTO NO CHAT DO TIME sempre identico ao audio: o python escreve fala_atual.cfg com a
# frase da variacao sorteada e aperta F3 (bind: exec fala_atual) — fonte unica, zero desvio.
# Ritual por aperto (com CS2 em foco): escreve texto -> F3 (chat) -> F11 (mic=cabo) ->
# segura PTT fantasma (kp_multiply) -> toca -> solta -> F4 (mic normal).
import threading
import time
import ctypes
import json
import random
import re
import io
import os
import sounddevice as sd
import soundfile as sf
import keyboard
import psutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import sys
# no exe congelado (PyInstaller onefile) __file__ mora numa pasta temporaria — a raiz real
# (onde vivem sons/, cfg/, config_local.json) e a pasta do executavel
RAIZ = (os.path.dirname(sys.executable) if getattr(sys, "frozen", False)
        else os.path.dirname(os.path.abspath(__file__)))
PASTA = os.path.join(RAIZ, "sons")
# pasta de cfg do SEU CS2: o padrao cobre a instalacao comum da Steam; se o seu jogo mora em
# outro disco, crie um config_local.json ao lado deste arquivo: {"cs2_cfg_dir": "D:\\...\\csgo\\cfg"}
_CFG_PADRAO = r"C:\Program Files (x86)\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg"
_CFG_LOCAL = os.path.join(RAIZ, "config_local.json")
CS2_CFG_DIR = (json.load(io.open(_CFG_LOCAL, encoding="utf-8")).get("cs2_cfg_dir", _CFG_PADRAO)
               if os.path.exists(_CFG_LOCAL) else _CFG_PADRAO)
FALA_CFG = os.path.join(CS2_CFG_DIR, "fala_atual.cfg")

FRASES = json.load(io.open(os.path.join(RAIZ, "frases_variacoes.json"), encoding="utf-8"))

# log proprio (13/07): o registro.log dependia do REDIRECIONAMENTO do lancador — restart sem
# redirect deixava a telemetria cega. Agora todo print tambem cai no arquivo, sempre.
_print_console = print
def print(*a, **k):  # noqa: A001 - tee deliberado
    _print_console(*a, **k)
    try:
        with io.open(os.path.join(RAIZ, "registro.log"), "a", encoding="utf-8") as _f:
            _f.write(time.strftime("%H:%M:%S ") + " ".join(str(x) for x in a) + "\n")
    except Exception:
        pass

ESTADO = {"time": "TR", "voz": "acougueiro"}
MODOS_VOZ = ["acougueiro", "mago", "misturado"]   # numpad . alterna (pedido 13/07); vale p/ os DOIS arsenais
PASTAS_VOZ = {"acougueiro": PASTA, "mago": os.path.join(RAIZ, "sons_mago")}
BASES = {
  "TR": {"1": "rushb", "2": "rushb_meio", "3": "rusha_fundo", "4": "varanda", "5": "avancar",
          "6": "segurar", "7": "fake_a", "8": "respawn", "9": "vitoria", "0": "derrota"},
  "CT": {"1": "ct_defb", "2": "ct_meio", "3": "ct_longa", "4": "ct_varanda", "5": "ct_avancar",
          "6": "ct_segurar", "7": "ct_rotacao", "8": "ct_round", "9": "vitoria", "0": "derrota"},
}

ESPERA_TROCA = 0.45
MARGEM_FIM = 0.8

def acha_cable():
    for i, d in enumerate(sd.query_devices()):
        if d["name"].startswith("CABLE Input") and d["max_output_channels"] > 0:
            return i
    return None

CABLE = acha_cable()

def cs2_em_foco():
    h = ctypes.windll.user32.GetForegroundWindow()
    pid = ctypes.c_ulong()
    ctypes.windll.user32.GetWindowThreadProcessId(h, ctypes.byref(pid))
    try:
        return psutil.Process(pid.value).name().lower() == "cs2.exe"
    except Exception:
        return False

def toca_em(dev, data, sr):
    try:
        with sd.OutputStream(device=dev, samplerate=sr, channels=data.shape[1] if data.ndim > 1 else 1) as s:
            s.write(data)
    except Exception as e:
        print("  (falha device %s: %s)" % (dev, e), flush=True)

_ultimo = {}
_geracao = 0
_trava = threading.Lock()
_rodizio = {}   # (time, tecla) -> proxima variacao 0..2

def _devolve_mic(minha_geracao):
    with _trava:
        if minha_geracao != _geracao:
            return
    keyboard.release("num *")
    for _ in range(120):
        if cs2_em_foco():
            keyboard.send("f4")
            print("[mic] devolvido (F4)", flush=True)
            return
        time.sleep(1)
    print("[mic] CS2 nao voltou ao foco em 2min; aperte F4 manualmente", flush=True)

def limpa_tags(frase):
    return re.sub(r"\s+", " ", re.sub(r"\[[^\]]*\]", "", frase)).strip()

def tocar(tecla):
    global _geracao
    lado = ESTADO["time"]
    base = BASES[lado][tecla]
    agora = time.time()
    if agora - _ultimo.get(base, 0) < 1.0:
        return
    _ultimo[base] = agora
    idx = _rodizio.get((lado, tecla), 0)
    _rodizio[(lado, tecla)] = (idx + 1) % len(FRASES.get(base, [0, 0, 0]))
    modo = ESTADO.get("voz", "acougueiro")
    voz = random.choice(("acougueiro", "mago")) if modo == "misturado" else modo
    pasta_voz = PASTAS_VOZ.get(voz, PASTA)
    arquivo = "%s_v%d.mp3" % (base, idx + 1)
    caminho = os.path.join(pasta_voz, arquivo)
    if not os.path.exists(caminho) and voz != "acougueiro":
        pasta_voz = PASTAS_VOZ["acougueiro"]   # mago ainda nao gravado p/ esta fala
        caminho = os.path.join(pasta_voz, arquivo)
    if not os.path.exists(caminho):
        arquivo = base + ".mp3"          # fallback: variacao ainda nao gerada
        caminho = os.path.join(pasta_voz, arquivo)
    frase = limpa_tags(FRASES.get(base, ["", "", ""])[idx])
    data, sr = sf.read(caminho, dtype="float32")
    dur = len(data) / sr
    em_jogo = cs2_em_foco()
    if em_jogo:
        with _trava:
            _geracao += 1
            g = _geracao
        # texto no chat = exatamente a variacao falada
        io.open(FALA_CFG, "w", encoding="utf-8").write('say_team "-RADIO- %s"\n' % frase)
        keyboard.send("f3")
        keyboard.send("f11")
        time.sleep(ESPERA_TROCA)
        keyboard.press("num *")
    alvos = [None] + ([CABLE] if CABLE is not None else [])
    for dev in alvos:
        threading.Thread(target=toca_em, args=(dev, data, sr), daemon=True).start()
    print("[som]", arquivo, "| voz:", voz, "| texto:", frase, "| lado:", lado, "(em jogo)" if em_jogo else "(preview)", flush=True)
    if em_jogo:
        threading.Timer(dur + MARGEM_FIM, _devolve_mic, args=(g,)).start()

NAV_NUMLOCK_OFF = {"end", "down", "page down", "left", "clear", "right", "home", "up", "page up", "insert"}

def ao_apertar(ev):
    if ev.event_type != "down" or not getattr(ev, "is_keypad", False):
        return
    # tecla decimal do numpad: nome varia por layout/teclado (ABNT2 pode dar ",", "num del"...)
    if ev.name and ev.name.lower() in ("decimal", ".", ",", "num del", "del", "delete", "separator"):
        # anti-repique: segurar a tecla dispara auto-repeat e ciclava varios modos por aperto
        agora_t = time.time()
        if agora_t - ESTADO.get("ult_toggle", 0) < 0.8:
            return
        ESTADO["ult_toggle"] = agora_t
        i = (MODOS_VOZ.index(ESTADO.get("voz", "acougueiro")) + 1) % len(MODOS_VOZ)
        ESTADO["voz"] = MODOS_VOZ[i]
        print("[voz] numpad . -> modo:", ESTADO["voz"].upper(), flush=True)
        # anuncio PARA TODOS (say, nao say_team): frases GENERICAS/enigmaticas, sem cara de sistema
        # (pedido 13/07: nada de explicar o soundboard — so clima)
        anuncio = {
            "acougueiro": "Estamos num açougue?",
            "mago": "A magia começou.",
            "misturado": "Hoje tem de tudo um pouco...",
        }[ESTADO["voz"]]
        if cs2_em_foco():
            io.open(FALA_CFG, "w", encoding="utf-8").write('say "%s"\n' % anuncio)
            keyboard.send("f3")
        else:
            # fora do jogo nao ha chat: feedback AUDIVEL nos fones (incidente 15:16 — toggle
            # funcionava mas era mudo fora de foco e parecia quebrado)
            try:
                voz_fb = random.choice(("acougueiro", "mago")) if ESTADO["voz"] == "misturado" else ESTADO["voz"]
                data_fb, sr_fb = sf.read(os.path.join(PASTAS_VOZ[voz_fb], "avancar_v1.mp3"), dtype="float32")
                threading.Thread(target=toca_em, args=(None, data_fb, sr_fb), daemon=True).start()
            except Exception as e_fb:
                print("  (feedback do toggle falhou: %s)" % e_fb, flush=True)
        return
    if ev.name in BASES["TR"]:
        tocar(ev.name)
    elif ev.name in NAV_NUMLOCK_OFF:
        print("[aviso] NumLock DESLIGADO — liga o NumLock pro soundboard funcionar!", flush=True)
    else:
        # instrumento permanente (incidente 13/07: '.' nao disparava e o log ficava mudo):
        # toda tecla de keypad SEM acao se identifica — o nome real vai direto pro registro
        print("[tecla] keypad sem acao: %r (avise o Claude se era pra fazer algo)" % ev.name, flush=True)

class RecebeGSI(BaseHTTPRequestHandler):
    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        corpo = self.rfile.read(n)
        self.send_response(200); self.end_headers()
        try:
            dados = json.loads(corpo)
            time_cru = (dados.get("player") or {}).get("team")
        except Exception:
            return
        if time_cru not in ("CT", "T"):
            return
        novo = "CT" if time_cru == "CT" else "TR"
        if novo != ESTADO["time"]:
            ESTADO["time"] = novo
            print("[time] voce agora e", novo, "— arsenal trocado", flush=True)
    def log_message(self, *a):
        pass

def _serve_gsi():
    try:
        ThreadingHTTPServer(("127.0.0.1", 3202), RecebeGSI).serve_forever()
    except Exception as e:
        print("[gsi] servidor falhou:", e, flush=True)

threading.Thread(target=_serve_gsi, daemon=True).start()

print("=== SOUNDBOARD v4 (3 variacoes por call) ===", flush=True)
print("CABLE:", ("ok (device %d)" % CABLE) if CABLE is not None else "AUSENTE (so fones)", flush=True)
for k in "1234567890":
    print("  numpad %s -> TR:%s | CT:%s (x3 variacoes)" % (k, BASES["TR"][k], BASES["CT"][k]), flush=True)
print("GSI :3202 | texto do chat = variacao falada (via F3/fala_atual.cfg)", flush=True)
keyboard.hook(ao_apertar)
keyboard.wait()
