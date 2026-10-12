const STORAGE_KEY = 'yapper-lang';

const STRINGS = {
  en: {
    tagline: 'Cut a clean 3–10 s voice reference from a video.',

    sourceTitle: '1. Source',
    load: 'Load',
    markStart: 'Set start from player',
    markEnd: 'Set end from player',
    start: 'Start',
    end: 'End',
    padding: 'Padding (s)',
    fetch: 'Fetch audio',
    recent: 'Recent clips',
    open: 'Open',
    delete: 'Delete',
    loading: 'Loading…',
    unknownUploader: 'unknown',

    outputTitle: '2. Output folder',
    outputPlaceholder: 'Choose where exported snippets are saved',
    browse: 'Browse…',
    pickFolderTitle: 'Output folder',
    chooseOutputFirst: 'Choose an output folder first',

    trimTitle: '3. Trim',
    play: 'Play selection',
    pause: 'Pause',
    loop: 'Loop',
    zoom: 'Zoom',
    original: 'Original',
    cleanVariant: 'Clean',
    startSeconds: 'Start (s)',
    endSeconds: 'End (s)',
    trimHint: 'Drag the edges of the highlighted region. Space plays the selection; − / + move an edge by 10 ms.',
    ofVideo: '{range} of the video',
    tooShort: 'shorter than 3 s',
    tooLong: 'longer than 10 s',
    peak: 'peak',
    clipping: 'clipping',
    audioLoadFailed: 'Could not load audio: {error}',

    cleanTitle: '4. Clean (optional)',
    cleanHint: 'OmniVoice copes with mild noise by itself, so leave this off for already clean speech. Use the lightest step that fixes the problem, then compare Original and Clean by ear.',
    stepVocals: 'Remove music and background',
    stepDereverb: 'Reduce reverb',
    stepDenoise: 'Reduce noise',
    runCleanup: 'Run cleanup',
    cleanMissing: 'Voice cleanup is not installed. Run <code>uv sync --extra ml</code> and restart the app.',
    tickStep: 'Tick at least one step.',
    cleanStarting: 'Starting… (the first run downloads the models)',
    cleanDone: 'Done. Now showing the cleaned audio; switch back with the Original button.',

    exportTitle: '5. Export',
    fileName: 'File name',
    sampleRate: 'Sample rate',
    keep48: 'Keep 48 kHz',
    mono: 'Mono',
    fades: '5 ms fades',
    normalize: 'Normalize peak',
    transcriptLabel: 'Transcript (saved next to the WAV as .txt, used as OmniVoice <code>ref_text</code>)',
    transcriptPlaceholder: 'Optional: the exact words spoken in the selection',
    draftTranscript: 'Draft transcript from selection',
    transcribing: 'Transcribing… (the first run downloads the model)',
    draftReady: 'Draft ready. Check it against the audio before exporting.',
    exportButton: 'Export snippet',
    exporting: 'Exporting…',
    saved: 'Saved {path}',
    monoOut: 'mono',
    stereoOut: 'stereo',

    maintenanceTitle: 'Maintenance',
    purgeCache: 'Purge cache',
    purgeModels: 'Purge models',
    restart: 'Restart app',
    stop: 'Stop app',
    purgeCacheConfirm: 'Delete all downloaded clips? Exported snippets in your output folder are not touched.',
    purgeModelsConfirm: 'Delete all downloaded models? They are several GB and are downloaded again the next time you run cleanup or a transcript draft.',
    cachePurged: 'Cache purged, {mb} MB freed.',
    modelsPurged: 'Models purged, {mb} MB freed.',
    restarting: 'Restarting…',
    notBack: 'The app did not come back. Start it again from the terminal.',
    stopConfirm: 'Stop the app? You will need the terminal to start it again.',
    stoppedTitle: 'App stopped',
    stoppedBody: 'Start it again with <code>uv run python -m app</code>, then reload this page.',

    requestFailed: 'Request failed ({status})',
  },

  pt: {
    tagline: 'Corte uma referência de voz limpa de 3 a 10 s a partir de um vídeo.',

    sourceTitle: '1. Origem',
    load: 'Carregar',
    markStart: 'Marcar início pelo player',
    markEnd: 'Marcar fim pelo player',
    start: 'Início',
    end: 'Fim',
    padding: 'Folga (s)',
    fetch: 'Baixar áudio',
    recent: 'Clipes recentes',
    open: 'Abrir',
    delete: 'Apagar',
    loading: 'Carregando…',
    unknownUploader: 'desconhecido',

    outputTitle: '2. Pasta de saída',
    outputPlaceholder: 'Escolha onde os trechos exportados serão salvos',
    browse: 'Procurar…',
    pickFolderTitle: 'Pasta de saída',
    chooseOutputFirst: 'Escolha primeiro uma pasta de saída',

    trimTitle: '3. Corte',
    play: 'Reproduzir seleção',
    pause: 'Pausar',
    loop: 'Repetir',
    zoom: 'Zoom',
    original: 'Original',
    cleanVariant: 'Limpo',
    startSeconds: 'Início (s)',
    endSeconds: 'Fim (s)',
    trimHint: 'Arraste as bordas da região destacada. Espaço reproduz a seleção; − / + movem uma borda em 10 ms.',
    ofVideo: '{range} do vídeo',
    tooShort: 'menor que 3 s',
    tooLong: 'maior que 10 s',
    peak: 'pico',
    clipping: 'clipagem',
    audioLoadFailed: 'Não foi possível carregar o áudio: {error}',

    cleanTitle: '4. Limpeza (opcional)',
    cleanHint: 'O OmniVoice lida sozinho com ruído leve, então deixe isto desligado quando a fala já estiver limpa. Use a etapa mais leve que resolva o problema e depois compare Original e Limpo de ouvido.',
    stepVocals: 'Remover música e fundo',
    stepDereverb: 'Reduzir reverberação',
    stepDenoise: 'Reduzir ruído',
    runCleanup: 'Executar limpeza',
    cleanMissing: 'A limpeza de voz não está instalada. Execute <code>uv sync --extra ml</code> e reinicie o app.',
    tickStep: 'Marque pelo menos uma etapa.',
    cleanStarting: 'Iniciando… (a primeira execução baixa os modelos)',
    cleanDone: 'Pronto. Mostrando agora o áudio limpo; volte com o botão Original.',

    exportTitle: '5. Exportação',
    fileName: 'Nome do arquivo',
    sampleRate: 'Taxa de amostragem',
    keep48: 'Manter 48 kHz',
    mono: 'Mono',
    fades: 'Fades de 5 ms',
    normalize: 'Normalizar pico',
    transcriptLabel: 'Transcrição (salva ao lado do WAV como .txt, usada como <code>ref_text</code> do OmniVoice)',
    transcriptPlaceholder: 'Opcional: as palavras exatas faladas na seleção',
    draftTranscript: 'Rascunhar transcrição da seleção',
    transcribing: 'Transcrevendo… (a primeira execução baixa o modelo)',
    draftReady: 'Rascunho pronto. Confira com o áudio antes de exportar.',
    exportButton: 'Exportar trecho',
    exporting: 'Exportando…',
    saved: 'Salvo em {path}',
    monoOut: 'mono',
    stereoOut: 'estéreo',

    maintenanceTitle: 'Manutenção',
    purgeCache: 'Limpar cache',
    purgeModels: 'Apagar modelos',
    restart: 'Reiniciar app',
    stop: 'Encerrar app',
    purgeCacheConfirm: 'Apagar todos os clipes baixados? Os trechos exportados na sua pasta de saída não são afetados.',
    purgeModelsConfirm: 'Apagar todos os modelos baixados? Eles ocupam vários GB e são baixados de novo na próxima limpeza ou rascunho de transcrição.',
    cachePurged: 'Cache limpo, {mb} MB liberados.',
    modelsPurged: 'Modelos apagados, {mb} MB liberados.',
    restarting: 'Reiniciando…',
    notBack: 'O app não voltou. Inicie-o de novo pelo terminal.',
    stopConfirm: 'Encerrar o app? Você vai precisar do terminal para iniciá-lo de novo.',
    stoppedTitle: 'App encerrado',
    stoppedBody: 'Inicie-o de novo com <code>uv run python -m app</code> e recarregue esta página.',

    requestFailed: 'A requisição falhou ({status})',
  },
};

// The server only speaks English; its known messages are translated here by exact text.
const SERVER_PT = {
  'Padding must be between 0 and 60 seconds': 'A folga deve estar entre 0 e 60 segundos',
  'Unknown job': 'Tarefa desconhecida',
  'Unknown clip': 'Clipe desconhecido',
  'Unknown clip or variant': 'Clipe ou variante desconhecidos',
  'Choose at least one cleanup step': 'Escolha pelo menos uma etapa de limpeza',
  'End must be after start': 'O fim deve vir depois do início',
  'Start is past the end of the video': 'O início está depois do fim do vídeo',
  'Could not open the folder dialog': 'Não foi possível abrir a janela de seleção de pasta',
  'A job is still running; wait for it or restart the app first': 'Ainda há uma tarefa em execução; aguarde ou reinicie o app antes',
  "Restart needs the launcher: start the app with 'uv run python -m app'": "Reiniciar exige o launcher: inicie o app com 'uv run python -m app'",
  'Transcription is not installed. Run: uv sync --extra ml': 'A transcrição não está instalada. Execute: uv sync --extra ml',
  'Voice cleanup is not installed. Run: uv sync --extra ml': 'A limpeza de voz não está instalada. Execute: uv sync --extra ml',
  'Live streams are not supported': 'Transmissões ao vivo não são suportadas',
  'Could not determine the video duration': 'Não foi possível determinar a duração do vídeo',
  'yt-dlp did not produce a file': 'O yt-dlp não gerou nenhum arquivo',
  'Invalid file name': 'Nome de arquivo inválido',
  'Choose an output folder first': 'Escolha primeiro uma pasta de saída',
  'The output folder must be an absolute path': 'A pasta de saída deve ser um caminho absoluto',
  'Selection is silent': 'A seleção está em silêncio',
  'Reading video info': 'Lendo informações do vídeo',
  'Downloading audio': 'Baixando áudio',
  'Converting to WAV': 'Convertendo para WAV',
  'Transcribing': 'Transcrevendo',
};

const STEPS_PT = { vocals: 'remoção de música e fundo', dereverb: 'redução de reverberação', denoise: 'redução de ruído' };

const SERVER_PT_PATTERNS = [
  [/^Range is too long: at most (\d+) minutes including padding$/, (m) => `O intervalo é longo demais: no máximo ${m[1]} minutos incluindo a folga`],
  [/^Invalid timestamp: (.*)$/, (m) => `Marcação de tempo inválida: ${m[1]}`],
  [/^Running (\w+) \((\d+)\/(\d+)\)$/, (m) => `Executando ${STEPS_PT[m[1]] ?? m[1]} (${m[2]}/${m[3]})`],
];

function initialLang() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored in STRINGS) return stored;
  } catch {}
  return navigator.language?.toLowerCase().startsWith('pt') ? 'pt' : 'en';
}

let lang = initialLang();

export function getLang() {
  return lang;
}

export function setLang(next) {
  if (!(next in STRINGS)) return;
  lang = next;
  try {
    localStorage.setItem(STORAGE_KEY, next);
  } catch {}
}

export function t(key, params = {}) {
  const text = STRINGS[lang][key] ?? STRINGS.en[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (_, name) => params[name] ?? '');
}

export function serverText(message) {
  if (lang !== 'pt' || typeof message !== 'string') return message;
  if (message in SERVER_PT) return SERVER_PT[message];
  for (const [pattern, render] of SERVER_PT_PATTERNS) {
    const match = message.match(pattern);
    if (match) return render(match);
  }
  return message;
}

export function applyStatic() {
  document.documentElement.lang = lang === 'pt' ? 'pt-BR' : 'en';
  for (const el of document.querySelectorAll('[data-i18n]')) el.textContent = t(el.dataset.i18n);
  for (const el of document.querySelectorAll('[data-i18n-html]')) el.innerHTML = t(el.dataset.i18nHtml);
  for (const el of document.querySelectorAll('[data-i18n-placeholder]')) el.placeholder = t(el.dataset.i18nPlaceholder);
}
