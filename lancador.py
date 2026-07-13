# lancador.py — entrada do soundboard.exe (PyInstaller):
#   duplo clique      -> configura na 1a vez, depois roda o soundboard
#   --configurar      -> forca o assistente de novo
#   --diagnostico     -> gate executavel (exit 0 = pacote sao)
import os
import sys

import assistente


def principal():
    if "--diagnostico" in sys.argv:
        assistente.diagnostico()
    if "--configurar" in sys.argv or not os.path.exists(assistente.MARCADOR):
        assistente.configurar()
        if "--configurar" in sys.argv:
            input("Enter para abrir o soundboard (ou feche a janela)...")
    import soundboard  # noqa: F401 - o soundboard roda no import (hook de teclado + GSI)


if __name__ == "__main__":
    try:
        principal()
    except KeyboardInterrupt:
        pass
    except Exception as e:  # janela de exe fecha rapido demais p/ ler — segura o erro
        print("\n[ERRO]", e)
        input("Enter para fechar...")
