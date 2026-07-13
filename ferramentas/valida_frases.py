# valida_frases.py — gate das calls do soundboard (regra do usuario 13/07):
# cada call = UMA mensagem canonica; variacoes = PARAFRASES (nunca status/auto-atribuicao);
# sem duplicatas; 2-6 palavras (calls COMPOSTAS isentas); referente da call presente.
import json, io, re, sys
fr = json.load(io.open(__file__.rsplit("\\",1)[0].rsplit("/",1)[0] + "/frases_variacoes.json", encoding="utf-8"))
REF = {"ct_defb":["b"],"ct_meio":["meio"],"ct_longa":["longa"],"ct_varanda":["varanda"],
       "ct_avancar":["avan","frente"],"ct_segurar":["segur","posi","mexe","sai","quiet"],
       "ct_rotacao":["rota","bomb","roda","troc"],"ct_round":["round","compr","equip"]}
COMPOSTAS = {"fake_a"}
falhas = []
for call, frases in fr.items():
    limpas = [re.sub(r"\[[^\]]*\]","",f).strip().lower() for f in frases]
    if len(set(limpas)) != len(limpas): falhas.append(f"{call}: variacao duplicada")
    for f in frases:
        n = len(re.findall(r"\w+", re.sub(r"\[[^\]]*\]","",f)))
        if call in REF and not any(r in f.lower() for r in REF[call]):
            falhas.append(f"{call}: '{f}' sem referente")
        if call not in COMPOSTAS and not (2 <= n <= 6):
            falhas.append(f"{call}: '{f}' com {n} palavras")
if falhas:
    print("VERMELHO:"); [print(" -", x) for x in falhas]; sys.exit(1)
print("VERDE: frases ok"); sys.exit(0)
