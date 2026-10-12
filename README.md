# yapper-snip

**Português** · [English](#english)

Corte um trecho de voz curto, limpo e de um único falante a partir de um vídeo do YouTube, pronto para usar como áudio de referência na clonagem de voz do OmniVoice.

## Requisitos

- [uv](https://docs.astral.sh/uv/)
- `ffmpeg` e `ffprobe` no PATH
- Node.js no PATH (o yt-dlp usa para ler as páginas do YouTube)
- Opcional: uma GPU NVIDIA para a limpeza de voz e os rascunhos de transcrição

## Como executar

```
uv sync                # só download, editor de corte e exportação
uv sync --extra ml     # também limpeza de voz e rascunhos de transcrição (vários GB)
uv run python -m app
```

Depois abra http://127.0.0.1:8765. A interface está disponível em português e inglês; troque pelo botão **PT / EN** no topo da página.

## Manutenção

Na seção **Manutenção**, no fim da página, ou pelo terminal:

```
uv run python -m app purge-cache    # apaga todos os clipes baixados
uv run python -m app purge-models   # apaga os modelos (vários GB, baixados de novo no próximo uso)
uv run python -m app restart        # reinicia o app: libera a GPU e recarrega tudo
uv run python -m app stop           # encerra o app
```

Nenhuma das limpezas toca nos trechos exportados nem na pasta de saída. As duas também funcionam com o app parado.

## Fluxo de uso

1. **Origem**: cole o link e defina início e fim aproximados. O áudio é baixado com alguns segundos de folga de cada lado.
2. **Pasta de saída**: escolha onde os trechos serão salvos. A exportação fica desativada até isso ser definido.
3. **Corte**: arraste as bordas da região na forma de onda até o início e o fim exatos. O corte tem precisão de amostra.
4. **Limpeza (opcional)**: remova música, reverberação ou ruído e compare Original e Limpo.
5. **Exportação**: grava um WAV e, opcionalmente, uma transcrição `.txt` com o mesmo nome.

## O que faz uma boa referência para o OmniVoice

- De 3 a 10 segundos. Trechos mais longos deixam a inferência mais lenta e podem piorar a clonagem.
- Um único falante, fala contínua, cortada em palavras completas. O OmniVoice remove os silêncios longos de qualquer forma.
- Áudio naturalmente limpo é melhor do que áudio limpo por processamento. O OmniVoice tolera ruído leve, então só use a limpeza quando ouvir um problema real.
- O ritmo e a entonação do trecho passam para a voz gerada.
- Use um trecho no idioma que você vai sintetizar; a clonagem entre idiomas mantém o sotaque.
- Informe a transcrição exata como `ref_text`. O botão de rascunho usa o Whisper; confira o texto com o áudio.

A exportação usa por padrão WAV 24 kHz mono de 16 bits, a mesma taxa de saída do OmniVoice.

## Testes

```
uv run pytest
```

## Observações

- Os clipes baixados ficam em `work/` e os modelos em `models/`; as duas pastas podem ser apagadas a qualquer momento.
- Use apenas vozes que você tem o direito de usar.

---

## English

Cut a short, clean, single-speaker voice snippet from a YouTube video, ready to use as a reference clip for OmniVoice voice cloning.

### Requirements

- [uv](https://docs.astral.sh/uv/)
- `ffmpeg` and `ffprobe` on the PATH
- Node.js on the PATH (yt-dlp uses it to read YouTube pages)
- Optional: an NVIDIA GPU for voice cleanup and transcript drafts

### Run

```
uv sync                # downloader, trim editor and export only
uv sync --extra ml     # also voice cleanup and transcript drafts (several GB)
uv run python -m app
```

Then open http://127.0.0.1:8765. The interface is available in Portuguese and English; switch with the **PT / EN** button at the top of the page.

### Maintenance

Use the **Maintenance** section at the bottom of the page, or the terminal:

```
uv run python -m app purge-cache    # delete all downloaded clips
uv run python -m app purge-models   # delete the models (several GB, downloaded again on next use)
uv run python -m app restart        # restart the app: frees the GPU and reloads everything
uv run python -m app stop           # shut the app down
```

Neither purge touches exported snippets or the output folder. Both also work while the app is stopped.

### Workflow

1. **Source**: paste a link, set a rough start and end. The audio is fetched with a few seconds of padding on each side.
2. **Output folder**: choose where snippets are saved. Export stays disabled until this is set.
3. **Trim**: drag the region edges on the waveform to the exact start and end. Cuts are sample-accurate.
4. **Clean (optional)**: remove music, reverb or noise, then compare Original and Clean.
5. **Export**: writes a WAV plus an optional `.txt` transcript with the same name.

### What makes a good OmniVoice reference

- 3 to 10 seconds. Longer clips slow inference and can reduce cloning quality.
- One speaker, continuous speech, cut on complete words. Long silences are removed by OmniVoice anyway.
- Naturally clean audio beats cleaned-up audio. OmniVoice tolerates mild noise, so only run cleanup when you hear a real problem.
- The clip's pace and delivery carry into the generated voice.
- Use a clip in the language you will synthesize; cross-lingual cloning keeps the accent.
- Pass the exact transcript as `ref_text`. The draft button uses Whisper; check it against the audio.

Exports default to 24 kHz mono 16-bit WAV, which matches OmniVoice's output rate.

### Tests

```
uv run pytest
```

### Notes

- Downloaded clips live in `work/` and models in `models/`; both can be deleted at any time.
- Only use voices you have the right to use.
