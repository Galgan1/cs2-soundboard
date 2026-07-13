# medir_audio.py — regua de "profissional" do acervo (gate executavel; uso: python medir_audio.py [pasta...])
# Mede por arquivo: LUFS integrado, true peak, silencio inicial/final, canais, sample rate.
# VERDE = 100% dentro: LUFS -16+-1 | TP <= -1.0 | sil.ini <= 0.15s | sil.fim <= 0.30s | mono 44100.
import json
import os
import re
import subprocess
import sys

ALVO_LUFS, TOL_LUFS, TP_MAX, SIL_INI, SIL_FIM = -16.0, 1.0, -1.0, 0.15, 0.30


def mede(caminho):
    r = subprocess.run(["ffmpeg", "-i", caminho, "-af",
                        "loudnorm=I=-16:TP=-1.5:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = re.search(r"\{[^}]+\}", r.stderr, re.S)
    ln = json.loads(m.group(0)) if m else {}
    r2 = subprocess.run(["ffmpeg", "-i", caminho, "-af",
                         "silencedetect=noise=-45dB:d=0.05", "-f", "null", "-"],
                        capture_output=True, text=True)
    dur = float(re.search(r"time=(\d+):(\d+):([\d.]+)", r2.stderr) and 0 or 0) or None
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=channels,sample_rate:format=duration", "-of", "json", caminho],
                       capture_output=True, text=True)
    meta = json.loads(p.stdout)
    dur = float(meta["format"]["duration"])
    ch = int(meta["streams"][0]["channels"])
    sr = int(meta["streams"][0]["sample_rate"])
    inicios = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", r2.stderr)]
    fins = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", r2.stderr)]
    sil_ini = fins[0] if inicios and inicios[0] < 0.01 and fins else 0.0
    sil_fim = dur - inicios[-1] if inicios and (not fins or inicios[-1] > (fins[-1] if fins else 0)) else 0.0
    return {"lufs": float(ln.get("input_i", "nan")), "tp": float(ln.get("input_tp", "nan")),
            "sil_ini": sil_ini, "sil_fim": sil_fim, "ch": ch, "sr": sr, "dur": dur}


def avalia(m):
    probs = []
    if abs(m["lufs"] - ALVO_LUFS) > TOL_LUFS: probs.append(f"LUFS {m['lufs']:.1f}")
    if m["tp"] > TP_MAX: probs.append(f"TP {m['tp']:.1f}")
    if m["sil_ini"] > SIL_INI: probs.append(f"sil.ini {m['sil_ini']:.2f}s")
    if m["sil_fim"] > SIL_FIM: probs.append(f"sil.fim {m['sil_fim']:.2f}s")
    if m["ch"] != 1: probs.append(f"ch={m['ch']}")
    if m["sr"] != 44100: probs.append(f"sr={m['sr']}")
    return probs


def main():
    pastas = sys.argv[1:] or ["sons", "sons_mago"]
    raiz = os.path.dirname(os.path.abspath(__file__))
    total, ruins, exemplos = 0, 0, []
    piores = {"lufs": [], "sil": []}
    for pasta in pastas:
        for f in sorted(os.listdir(os.path.join(raiz, pasta))):
            if not f.endswith(".mp3"): continue
            total += 1
            m = mede(os.path.join(raiz, pasta, f))
            probs = avalia(m)
            if probs:
                ruins += 1
                if len(exemplos) < 12: exemplos.append(f"{pasta}/{f}: " + ", ".join(probs))
            piores["lufs"].append(m["lufs"])
            piores["sil"].append(m["sil_ini"])
    lufs = sorted(piores["lufs"])
    print(f"arquivos: {total} | fora da regua: {ruins}")
    print(f"LUFS: min {lufs[0]:.1f} / mediana {lufs[len(lufs)//2]:.1f} / max {lufs[-1]:.1f} (alvo -16+-1)")
    print(f"silencio inicial max: {max(piores['sil']):.2f}s (alvo <=0.15s)")
    for e in exemplos: print("  ", e)
    print("VERDE: acervo profissional" if ruins == 0 else f"VERMELHO: {ruins}/{total} fora da regua")
    sys.exit(0 if ruins == 0 else 1)


if __name__ == "__main__":
    main()
