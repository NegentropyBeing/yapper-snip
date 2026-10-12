import WaveSurfer from './vendor/wavesurfer.esm.js';
import Regions from './vendor/regions.esm.js';
import Timeline from './vendor/timeline.esm.js';

const $ = (id) => document.getElementById(id);

// OmniVoice: "Use a 3-10 seconds reference audio clip."
const MIN_LEN = 3;
const MAX_LEN = 10;
const MIN_REGION = 0.05;
const CLIP_DBFS = -0.1;
const MAX_ZOOM = 600;

const state = {
  clip: null,
  variant: 'original',
  sel: { start: 0, end: 0 },
  ws: null,
  regions: null,
  region: null,
  playingSelection: false,
  player: null,
};

async function api(path, options = {}) {
  if (options.body !== undefined) {
    options = { ...options, body: JSON.stringify(options.body), headers: { 'Content-Type': 'application/json' } };
  }
  const res = await fetch(path, options);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${res.status})`);
  return data;
}

function clock(seconds) {
  const m = Math.floor(seconds / 60);
  const s = (seconds - m * 60).toFixed(3).padStart(6, '0');
  return `${m}:${s}`;
}

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

/* ---------- settings ---------- */

async function loadSettings() {
  const s = await api('/api/settings');
  $('padding').value = s.padding;
  $('sample-rate').value = s.sample_rate || '';
  $('mono').checked = s.mono;
  $('fade').checked = s.fade_ms > 0;
  $('normalize').checked = s.normalize;
  setOutputDir(s.output_dir);
}

function setOutputDir(dir) {
  $('output-dir').value = dir;
  $('export-btn').disabled = !dir;
  $('export-btn').title = dir ? '' : 'Choose an output folder first';
}

function saveSettings(changes) {
  return api('/api/settings', { method: 'PUT', body: changes }).catch(() => {});
}

$('output-dir').addEventListener('change', async () => {
  const dir = $('output-dir').value.trim();
  await saveSettings({ output_dir: dir });
  setOutputDir(dir);
});

$('pick-folder').addEventListener('click', async () => {
  $('pick-folder').disabled = true;
  try {
    setOutputDir((await api('/api/pick-folder', { method: 'POST' })).output_dir);
  } catch (err) {
    alert(err.message);
  } finally {
    $('pick-folder').disabled = false;
  }
});

$('padding').addEventListener('change', () => saveSettings({ padding: Number($('padding').value) }));
$('sample-rate').addEventListener('change', () => saveSettings({ sample_rate: Number($('sample-rate').value) || 0 }));
$('mono').addEventListener('change', () => saveSettings({ mono: $('mono').checked }));
$('fade').addEventListener('change', () => saveSettings({ fade_ms: $('fade').checked ? 5 : 0 }));
$('normalize').addEventListener('change', () => saveSettings({ normalize: $('normalize').checked }));

/* ---------- source ---------- */

function loadYouTubeApi() {
  return new Promise((resolve) => {
    if (window.YT?.Player) return resolve();
    window.onYouTubeIframeAPIReady = resolve;
    const script = document.createElement('script');
    script.src = 'https://www.youtube.com/iframe_api';
    document.head.append(script);
  });
}

async function showPlayer(videoId) {
  $('player-wrap').hidden = false;
  await loadYouTubeApi();
  if (state.player?.cueVideoById) {
    state.player.cueVideoById(videoId);
  } else {
    state.player = new YT.Player('player', { videoId, playerVars: { playsinline: 1 } });
  }
}

async function probe() {
  const url = $('url').value.trim();
  if (!url) return;
  $('source-error').textContent = '';
  $('video-info').textContent = 'Loading…';
  $('probe').disabled = true;
  try {
    const info = await api('/api/probe', { method: 'POST', body: { url } });
    $('video-info').textContent = `${info.title} · ${info.uploader ?? 'unknown'} · ${clock(info.duration)}`;
    if (info.extractor === 'Youtube') await showPlayer(info.video_id);
    else $('player-wrap').hidden = true;
  } catch (err) {
    $('video-info').textContent = '';
    $('source-error').textContent = err.message;
  } finally {
    $('probe').disabled = false;
  }
}

$('probe').addEventListener('click', probe);
$('url').addEventListener('keydown', (e) => { if (e.key === 'Enter') probe(); });

for (const [button, field] of [['mark-start', 'start'], ['mark-end', 'end']]) {
  $(button).addEventListener('click', () => {
    const t = state.player?.getCurrentTime?.();
    if (t !== undefined) $(field).value = clock(t);
  });
}

async function pollJob(job, render) {
  while (job.status === 'queued' || job.status === 'running') {
    render(job);
    await new Promise((r) => setTimeout(r, 400));
    job = await api(`/api/jobs/${job.id}`);
  }
  if (job.status === 'error') throw new Error(job.error);
  return job.result;
}

function renderDownload(job) {
  $('job').hidden = false;
  $('job-progress').value = job.progress;
  $('job-message').textContent = job.message;
}

$('fetch').addEventListener('click', async () => {
  const url = $('url').value.trim();
  if (!url) return;
  $('source-error').textContent = '';
  $('fetch').disabled = true;
  try {
    const job = await api('/api/clips', {
      method: 'POST',
      body: { url, start: $('start').value, end: $('end').value, padding: Number($('padding').value) },
    });
    const result = await pollJob(job, renderDownload);
    await openClip(result.clip_id);
    refreshRecent();
  } catch (err) {
    $('source-error').textContent = err.message;
  } finally {
    $('job').hidden = true;
    $('fetch').disabled = false;
  }
});

/* ---------- recent clips ---------- */

async function refreshRecent() {
  const clips = await api('/api/clips');
  $('recent').hidden = clips.length === 0;
  $('recent-list').replaceChildren(...clips.map((clip) => {
    const li = document.createElement('li');
    const label = document.createElement('span');
    label.textContent = `${clip.title} · ${clock(clip.window_start)}–${clock(clip.window_end)}`;
    const open = document.createElement('button');
    open.className = 'secondary';
    open.textContent = 'Open';
    open.addEventListener('click', () => openClip(clip.id));
    const del = document.createElement('button');
    del.className = 'secondary';
    del.textContent = 'Delete';
    del.addEventListener('click', async () => {
      await api(`/api/clips/${clip.id}`, { method: 'DELETE' });
      if (state.clip?.id === clip.id) closeClip();
      refreshRecent();
    });
    li.append(label, open, del);
    return li;
  }));
}

/* ---------- waveform ---------- */

function ensureWaveSurfer() {
  if (state.ws) return;
  state.regions = Regions.create();
  state.ws = WaveSurfer.create({
    container: $('waveform'),
    height: 160,
    waveColor: cssVar('--wave'),
    progressColor: cssVar('--wave-played'),
    cursorColor: cssVar('--text'),
    normalize: true,
    plugins: [state.regions, Timeline.create()],
  });

  state.ws.on('decode', () => {
    state.regions.clearRegions();
    state.region = state.regions.addRegion({
      start: state.sel.start,
      end: state.sel.end,
      color: cssVar('--region'),
      drag: true,
      resize: true,
      minLength: MIN_REGION,
    });
    applyZoom();
    renderSelection();
  });

  state.regions.on('region-update', (region) => {
    state.sel = { start: region.start, end: region.end };
    renderSelection(false);
  });
  state.regions.on('region-updated', (region) => {
    state.sel = { start: region.start, end: region.end };
    renderSelection();
  });

  state.ws.on('interaction', () => { state.playingSelection = false; });
  state.ws.on('timeupdate', (time) => {
    if (!state.playingSelection || time < state.sel.end) return;
    state.ws.setTime(state.sel.start);
    if (!$('loop').checked) stopSelection();
  });
  state.ws.on('finish', () => {
    if (!state.playingSelection) return;
    state.ws.setTime(state.sel.start);
    if ($('loop').checked) state.ws.play();
    else stopSelection();
  });
  state.ws.on('play', () => { $('play').textContent = 'Pause'; });
  state.ws.on('pause', () => { $('play').textContent = 'Play selection'; });
  state.ws.on('error', (err) => { $('clip-title').textContent = `Could not load audio: ${err?.message ?? err}`; });
}

function stopSelection() {
  state.playingSelection = false;
  state.ws.pause();
}

function togglePlay() {
  if (!state.ws || !state.clip) return;
  if (state.ws.isPlaying()) return stopSelection();
  state.playingSelection = true;
  state.ws.setTime(state.sel.start);
  state.ws.play();
}

function applyZoom() {
  if (!state.ws?.getDuration()) return;
  const fit = $('waveform').clientWidth / state.ws.getDuration();
  const t = Number($('zoom').value) / 100;
  // Exponential so the low end of the slider stays useful.
  state.ws.zoom(t === 0 ? 0 : fit * Math.pow(Math.max(MAX_ZOOM / fit, 1), t));
}

function selectionPeakDb() {
  const buffer = state.ws.getDecodedData();
  if (!buffer) return null;
  const from = Math.floor(state.sel.start * buffer.sampleRate);
  const to = Math.min(Math.ceil(state.sel.end * buffer.sampleRate), buffer.length);
  let peak = 0;
  for (let c = 0; c < buffer.numberOfChannels; c++) {
    const data = buffer.getChannelData(c);
    for (let i = from; i < to; i++) {
      const v = Math.abs(data[i]);
      if (v > peak) peak = v;
    }
  }
  return peak > 0 ? 20 * Math.log10(peak) : -Infinity;
}

function renderSelection(withPeak = true) {
  const { start, end } = state.sel;
  const length = end - start;
  $('sel-start').value = start.toFixed(3);
  $('sel-end').value = end.toFixed(3);

  const badge = $('sel-duration');
  const ok = length >= MIN_LEN && length <= MAX_LEN;
  badge.className = `badge ${ok ? 'good' : 'warn'}`;
  badge.textContent = `${length.toFixed(3)} s` + (ok ? '' : length < MIN_LEN ? ' · shorter than 3 s' : ' · longer than 10 s');

  if (!withPeak) return;
  const db = selectionPeakDb();
  const peak = $('sel-peak');
  if (db === null) {
    peak.textContent = '';
  } else if (db >= CLIP_DBFS) {
    peak.className = 'badge bad';
    peak.textContent = `peak ${db.toFixed(1)} dBFS · clipping`;
  } else {
    peak.className = 'badge';
    peak.textContent = `peak ${Number.isFinite(db) ? db.toFixed(1) : '−∞'} dBFS`;
  }
}

function setSelection(start, end) {
  const duration = state.clip.duration;
  start = Math.max(0, Math.min(start, duration - MIN_REGION));
  end = Math.max(start + MIN_REGION, Math.min(end, duration));
  state.sel = { start, end };
  state.region?.setOptions({ start, end });
  renderSelection();
}

$('play').addEventListener('click', togglePlay);
$('zoom').addEventListener('input', applyZoom);
$('sel-start').addEventListener('change', () => setSelection(Number($('sel-start').value), state.sel.end));
$('sel-end').addEventListener('change', () => setSelection(state.sel.start, Number($('sel-end').value)));

for (const button of document.querySelectorAll('[data-nudge]')) {
  button.addEventListener('click', () => {
    const by = Number(button.dataset.by);
    if (button.dataset.nudge === 'start') setSelection(state.sel.start + by, state.sel.end);
    else setSelection(state.sel.start, state.sel.end + by);
  });
}

document.addEventListener('keydown', (e) => {
  if (e.code !== 'Space' || /^(INPUT|TEXTAREA|SELECT|BUTTON)$/.test(e.target.tagName)) return;
  e.preventDefault();
  togglePlay();
});

/* ---------- clip ---------- */

function loadVariant(variant) {
  state.variant = variant;
  for (const button of document.querySelectorAll('[data-variant]')) {
    button.classList.toggle('active', button.dataset.variant === variant);
  }
  state.playingSelection = false;
  state.ws.load(`/api/clips/${state.clip.id}/audio?variant=${variant}&t=${Date.now()}`);
}

function defaultName(clip) {
  const base = (clip.uploader || clip.title || 'snippet')
    .normalize('NFD').replace(/[̀-ͯ]/g, '')
    .toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  return base.slice(0, 40) || 'snippet';
}

async function openClip(id) {
  const clip = await api(`/api/clips/${id}`);
  state.clip = clip;
  state.sel = { start: clip.sel_start, end: clip.sel_end };
  $('trim').hidden = false;
  $('clean').hidden = false;
  $('export').hidden = false;
  $('clean-status').textContent = '';
  $('transcribe-status').textContent = '';
  $('clip-title').textContent = `${clip.title} · ${clock(clip.window_start)}–${clock(clip.window_end)} of the video`;
  $('name').value = defaultName(clip);
  $('transcript').value = '';
  $('export-result').textContent = '';
  $('zoom').value = 0;
  $('variants').hidden = !clip.variants.includes('clean');
  ensureWaveSurfer();
  loadVariant('original');
  $('trim').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function closeClip() {
  state.clip = null;
  state.ws?.empty();
  $('trim').hidden = true;
  $('clean').hidden = true;
  $('export').hidden = true;
}

for (const button of document.querySelectorAll('[data-variant]')) {
  button.addEventListener('click', () => loadVariant(button.dataset.variant));
}

/* ---------- clean and transcript ---------- */

async function loadCapabilities() {
  const caps = await api('/api/capabilities');
  $('clean-controls').hidden = !caps.isolate;
  $('clean-missing').hidden = caps.isolate;
  $('transcribe-btn').hidden = !caps.transcribe;
}

$('clean-btn').addEventListener('click', async () => {
  const steps = [...document.querySelectorAll('[data-step]:checked')].map((box) => box.dataset.step);
  const status = $('clean-status');
  status.className = 'muted';
  if (steps.length === 0) {
    status.textContent = 'Tick at least one step.';
    return;
  }
  const clipId = state.clip.id;
  $('clean-btn').disabled = true;
  try {
    const job = await api(`/api/clips/${clipId}/isolate`, { method: 'POST', body: { steps } });
    await pollJob(job, (j) => { status.textContent = j.message || 'Starting… (the first run downloads the models)'; });
    if (state.clip?.id !== clipId) return;
    status.textContent = 'Done. Now showing the cleaned audio; switch back with the Original button.';
    $('variants').hidden = false;
    loadVariant('clean');
  } catch (err) {
    status.className = 'error';
    status.textContent = err.message;
  } finally {
    $('clean-btn').disabled = false;
  }
});

$('transcribe-btn').addEventListener('click', async () => {
  const status = $('transcribe-status');
  status.className = 'muted';
  status.textContent = 'Transcribing… (the first run downloads the model)';
  $('transcribe-btn').disabled = true;
  try {
    const job = await api(`/api/clips/${state.clip.id}/transcribe`, {
      method: 'POST',
      body: { start: state.sel.start, end: state.sel.end, variant: state.variant },
    });
    const result = await pollJob(job, () => {});
    $('transcript').value = result.text;
    status.textContent = 'Draft ready. Check it against the audio before exporting.';
  } catch (err) {
    status.className = 'error';
    status.textContent = err.message;
  } finally {
    $('transcribe-btn').disabled = false;
  }
});

/* ---------- export ---------- */

$('export-btn').addEventListener('click', async () => {
  const result = $('export-result');
  result.className = '';
  result.textContent = 'Exporting…';
  $('export-btn').disabled = true;
  try {
    const out = await api(`/api/clips/${state.clip.id}/export`, {
      method: 'POST',
      body: {
        name: $('name').value,
        start: state.sel.start,
        end: state.sel.end,
        variant: state.variant,
        sample_rate: Number($('sample-rate').value) || null,
        mono: $('mono').checked,
        fade_ms: $('fade').checked ? 5 : 0,
        normalize: $('normalize').checked,
        transcript: $('transcript').value,
      },
    });
    result.className = 'ok';
    result.textContent = `Saved ${out.path} · ${out.duration.toFixed(3)} s · ${out.sample_rate / 1000} kHz · ${out.channels === 1 ? 'mono' : 'stereo'}`;
  } catch (err) {
    result.className = 'fail';
    result.textContent = err.message;
  } finally {
    $('export-btn').disabled = !$('output-dir').value;
  }
});

loadSettings();
loadCapabilities();
refreshRecent();
