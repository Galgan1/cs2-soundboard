# 🎙️ CS2 Soundboard — calls táticas com vozes de personagem

Soundboard de numpad para Counter-Strike 2: aperta uma tecla e seu "personagem" grita a call
no **voice chat do jogo** (via microfone virtual) e escreve **o mesmo texto no chat do time** —
sempre idênticos, com variações em rodízio para não enjoar.

**Duas vozes inclusas** (geradas com ElevenLabs, prontas para usar):
- 🔪 **Açougueiro** — vilão grave de filme B ("Guardem o B, capangas!")
- 🧙 **Mago** — feiticeiro de guerra arcano ("Que os ventos arcanos soprem!")

O arsenal muda sozinho conforme seu time (TR/CT), detectado ao vivo pelo Game State
Integration oficial do CS2. Sem hack, sem injeção: é só áudio num cabo virtual + cfgs.

## Como funciona

```
numpad → soundboard.py → toca o MP3 no CABLE Input (mic virtual) → voice chat do CS2
                       → escreve fala_atual.cfg e aperta F3 → texto idêntico no chat
```

| Tecla (numpad) | Lado TR | Lado CT |
|---|---|---|
| 1 | Rush B | Defesa no B |
| 2 | Rush B pelo meio | Atenção ao meio |
| 3 | Rush A pelo fundo | Defesa na Longa |
| 4 | Ataque pela varanda | Segurem a varanda |
| 5 | Avançar | Avançar juntos |
| 6 | Segurar posição | Segurar posições |
| 7 | Fake no A, bomba no B | Rotação de bomb |
| 8 | Round novo | Round novo, comprem |
| 9 / 0 | Vitória / Derrota | Vitória / Derrota |
| **.** | **alterna a voz: açougueiro → mago → misturado** (anuncia no chat com frases enigmáticas) | |

Cada call tem 6 variações que giram em rodízio. Anti-repique de 1s.

## Instalação (Windows)

1. **Python 3.11+** e as dependências:
   ```
   pip install -r requirements.txt
   ```
2. **VB-Cable** (o microfone virtual): https://vb-audio.com/Cable/ — instale e reinicie.
   ⚠️ O instalador pode sequestrar a SAÍDA padrão do Windows (PC "mudo") — vá em
   Configurações de Som e devolva seu fone como padrão.
3. **Cfgs do jogo** — copie os arquivos de [`cfg/`](cfg/) para
   `...\Steam\steamapps\common\Counter-Strike Global Offensive\game\csgo\cfg\`:
   - `gamestate_integration_soundboard.cfg` (deteção de time)
   - `voz_locutor.cfg` (mic do jogo = cabo virtual)
   - `voz_normal.cfg` — **EDITE**: troque o placeholder pelo nome do SEU microfone
     (igualzinho aparece no Painel de Som do Windows)
   - cole o conteúdo de `autoexec_trecho.cfg` no seu `autoexec.cfg`
4. **No jogo**: modo de transmissão de voz = "sempre ativo" (ou deixe o PTT e segure junto);
   rode `exec autoexec` uma vez (ou reinicie o CS2).
5. **Rode o soundboard** (deixe aberto enquanto joga):
   ```
   python soundboard.py
   ```
   Se seu CS2 não está no caminho padrão da Steam, crie um `config_local.json`:
   ```json
   { "cs2_cfg_dir": "D:\\SteamLibrary\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\cfg" }
   ```

## Pegadinhas que custaram horas (para você não pagar de novo)

- **"Os amigos não me ouvem"** → o CS2 PINA o microfone via `voice_device_override`
  (fica em `Steam\userdata\<id>\730\local\cfg\cs2_machine_convars.vcfg`) e ignora o
  Windows E a Steam. É exatamente o que `voz_locutor.cfg`/`voz_normal.cfg` controlam — use F11/F4.
- **Teclado ABNT2**: a tecla do jogo pode ter nome diferente do esperado (o Ç é "semicolon").
  No numpad, o ponto/vírgula decimal atende por `.`, `,`, `decimal` ou `num del` — o
  soundboard aceita todos.
- **NumLock DESLIGADO** faz o numpad virar setas — o soundboard avisa no console.
- **Dois teclados**: hotkey global por nome vaza para a fileira de números — por isso o
  filtro `is_keypad` (só o numpad dispara).
- **`voice_loopback 1`** no console do jogo = você se ouve, teste sem depender de amigos.
- **F12 é screenshot da Steam** — por isso o retorno de mic usa F4.
- Áudio "não profissional"? As ferramentas de régua e masterização estão em
  [`ferramentas/`](ferramentas/) (`medir_audio.py` = gate de loudness/silêncio;
  `masterizar.py` = pipeline a partir de gravações brutas; requer ffmpeg).

## Personalização

- **Textos**: edite `frases_variacoes.json` (cada call = lista de variações; a variação N
  casa com o arquivo `sons/<call>_vN.mp3`). Valide com `python ferramentas/valida_frases.py`.
- **Vozes novas**: gere os MP3 com o TTS que preferir (nós usamos ElevenLabs), nomeie
  `<call>_vN.mp3` e deixe em `sons/` (açougueiro) ou `sons_mago/` (segunda voz).
  Regra de ouro aprendida na dor: **performance de TTS é artefato único** — guarde os MP3
  que você ama; regravar "igual" nunca vem igual.

## Aviso de bom senso

Use em servidores próprios, com amigos, ou onde soundboard for bem-vindo. Em matchmaking
competitivo, voice spam pode render mute/report — a zoeira é responsabilidade de quem aperta. 🎛️

## Licença

MIT — veja [LICENSE](LICENSE). Áudios inclusos gerados por IA (ElevenLabs) pelos autores.
