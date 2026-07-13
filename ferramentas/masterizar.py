# masterizar.py — masteriza o acervo A PARTIR DOS BRUTOS para o padrao profissional:
# pitch (so acougueiro) -> trim de silencio -> HPF 80Hz -> loudnorm 2-PASSADAS (linear) ->
# padding anti-click -> mono 44.1k. Gate: python medir_audio.py <staging>.
# Uso: python masterizar.py  (gera sons_master/ e sons_master_mago/ — o swap e manual/consciente)
import json
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.abspath(__file__))
PITCH_ACG = "asetrate=44100*0.9,aresample=44100,atempo=1.1111,"
PREP = ("silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.04,"
        "areverse,silenceremove=start_periods=1:start_threshold=-45dB:start_silence=0.10,areverse,"
        "highpass=f=80,adelay=40,apad=pad_dur=0.10")
LN = "loudnorm=I=-16:TP=-1.5:LRA=7"


def roda(args):
    return subprocess.run(args, capture_output=True, text=True)


def masteriza(origem, destino, com_pitch):
    prep = (PITCH_ACG if com_pitch else "") + PREP
    tmp = destino + ".tmp.wav"
    r = roda(["ffmpeg", "-y", "-loglevel", "error", "-i", origem, "-af", prep,
              "-ar", "44100", "-ac", "1", tmp])
    if r.returncode != 0:
        return f"prep: {r.stderr[:120]}"
    # gritos curtos tem crest alto: loudnorm linear RECUA o ganho pelo TP e entrega LUFS baixo
    # (98/216 na 1a tentativa). Broadcast de bark: ganho exato + brickwall limiter (-1.5dBTP),
    # em laco de convergencia ate cravar o alvo.
    def mede_lufs(arq):
        r = roda(["ffmpeg", "-i", arq, "-af", "loudnorm=print_format=json", "-f", "null", "-"])
        m = re.search(r"\{[^}]+\}", r.stderr, re.S)
        return float(json.loads(m.group(0))["input_i"]) if m else None
    # convergencia POS-limiter (v3): aplica ganho ACUMULADO sobre o tmp original -> limita
    # (0.79 = folga p/ picos que o encoder MP3 recria) -> MEDE o resultado ja limitado ->
    # repete ate cravar. Medir antes do limiter deixava 8/216 ~0.5dB abaixo do alvo.
    atual = None
    ganho_acum = 0.0
    for passo in range(5):
        prox = tmp + f".{passo}.wav"
        r = roda(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-af",
                  f"volume={ganho_acum:.2f}dB,alimiter=limit=0.79:level=false",
                  "-ar", "44100", "-ac", "1", prox])
        if r.returncode != 0:
            os.remove(tmp); return f"ganho: {r.stderr[:120]}"
        if atual: os.remove(atual)
        atual = prox
        i_atual = mede_lufs(atual)
        if i_atual is None:
            os.remove(tmp); return "sem medida de LUFS"
        delta = -16.0 - i_atual
        if abs(delta) <= 0.7:
            break
        ganho_acum += delta
    r2 = roda(["ffmpeg", "-y", "-loglevel", "error", "-i", atual,
               "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-q:a", "2", destino])
    os.remove(atual)
    os.remove(tmp)
    return None if r2.returncode == 0 else f"encode: {r2.stderr[:120]}"


def main():
    lotes = [("brutos", "sons_master", True), ("brutos_mago", "sons_master_mago", False)]
    falhas = []
    for origem_dir, destino_dir, pitch in lotes:
        os.makedirs(os.path.join(RAIZ, destino_dir), exist_ok=True)
        arquivos = [f for f in sorted(os.listdir(os.path.join(RAIZ, origem_dir)))
                    if f.endswith(".mp3") and "_v" in f]
        for f in arquivos:
            destino = os.path.join(RAIZ, destino_dir, f)
            erro = masteriza(os.path.join(RAIZ, origem_dir, f), destino, pitch)
            if erro:
                falhas.append(f"{origem_dir}/{f}: {erro}")
        print(f"{origem_dir} -> {destino_dir}: {len(arquivos)} arquivos")
    if falhas:
        print("VERMELHO:"); [print("  ", x) for x in falhas]; sys.exit(1)
    print("VERDE: masterizacao completa — rode: python medir_audio.py sons_master sons_master_mago")
    sys.exit(0)


if __name__ == "__main__":
    main()
