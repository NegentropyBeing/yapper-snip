# yapper-snip

**Português** · [English](#english)

Corta um trecho de voz curto e limpo de um vídeo, para usar como áudio de referência na clonagem de voz.

## Linguagem

**Clip**:
O áudio baixado de um intervalo de um vídeo, guardado no cache de trabalho, de onde saem os trechos exportados.
_Avoid_: download, arquivo

**Variant**:
Uma versão de áudio de um Clip: `original` (como baixado) ou `clean` (depois da limpeza de voz).
_Avoid_: versão, track

**Model runtime**:
Os modelos de aprendizado de máquina usados pela limpeza de voz e pela transcrição: onde ficam em disco, qual está carregado na GPU e como são apagados.
_Avoid_: ML, motor

---

## English

Cuts a short, clean voice snippet from a video, for use as reference audio in voice cloning.

### Language

**Clip**:
The audio downloaded for a range of a video, kept in the work cache, from which exported snippets are cut.
_Avoid_: download, file

**Variant**:
One audio version of a Clip: `original` (as downloaded) or `clean` (after voice cleanup).
_Avoid_: version, track

**Model runtime**:
The machine-learning models used by voice cleanup and transcription: where they live on disk, which one is loaded on the GPU, and how they are deleted.
_Avoid_: ML, engine
