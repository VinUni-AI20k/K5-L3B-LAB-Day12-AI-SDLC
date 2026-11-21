// Music = <audio> files from the manifest (crossfaded). SFX = file if the manifest has one, else a small WebAudio synth.
let ac = null, master = null, muted = false;
const files = { music: {}, sfx: {} };
const buffers = {};
let current = null, currentName = null;

export function registerAudio(manifest) {
  for (const a of manifest) {
    if (a.kind === "music" && a.id) files.music[a.id] = "assets/" + a.path;
    if (a.kind === "sfx" && a.id) files.sfx[a.id] = "assets/" + a.path;
  }
}

export function unlock() {
  if (ac) { if (ac.state === "suspended") ac.resume(); return; }
  ac = new (window.AudioContext || window.webkitAudioContext)();
  master = ac.createGain(); master.gain.value = 0.5; master.connect(ac.destination);
  for (const [id, url] of Object.entries(files.sfx)) {
    fetch(url).then((r) => r.arrayBuffer()).then((b) => ac.decodeAudioData(b)).then((buf) => (buffers[id] = buf)).catch(() => {});
  }
  if (pending) { const p = pending; pending = null; music(p); }
}

export function toggleMute() {
  muted = !muted;
  if (master) master.gain.value = muted ? 0 : 0.5;
  if (current) current.muted = muted;
  return muted;
}
export const isMuted = () => muted;

let pending = null;
export function music(name, vol = 0.55) {
  if (name === currentName) return;
  if (!ac) { pending = name; return; }
  const old = current;
  currentName = name;
  current = null;
  if (old) fadeOut(old);
  const url = files.music[name];
  if (!url) return;
  const a = new Audio(url);
  a.loop = true; a.volume = 0; a.muted = muted;
  a.play().catch(() => {});
  current = a;
  const t0 = performance.now();
  const step = () => {
    if (current !== a) return;
    const k = Math.min(1, (performance.now() - t0) / 900);
    a.volume = vol * k;
    if (k < 1) requestAnimationFrame(step);
  };
  step();
}
function fadeOut(a) {
  const v0 = a.volume, t0 = performance.now();
  const step = () => {
    const k = Math.min(1, (performance.now() - t0) / 600);
    a.volume = v0 * (1 - k);
    if (k < 1) requestAnimationFrame(step); else a.pause();
  };
  step();
}
export function stopMusic() { if (current) fadeOut(current); current = null; currentName = null; }

// ---------- SFX ----------
function tone({ type = "sine", f0 = 440, f1 = f0, dur = 0.15, vol = 0.3, delay = 0, noise = false, q = 1 }) {
  const t = ac.currentTime + delay;
  const g = ac.createGain();
  g.gain.setValueAtTime(0.0001, t);
  g.gain.exponentialRampToValueAtTime(vol, t + 0.01);
  g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
  let src;
  if (noise) {
    const len = Math.ceil(ac.sampleRate * dur);
    const buf = ac.createBuffer(1, len, ac.sampleRate), d = buf.getChannelData(0);
    for (let i = 0; i < len; i++) d[i] = Math.random() * 2 - 1;
    src = ac.createBufferSource(); src.buffer = buf;
    const flt = ac.createBiquadFilter(); flt.type = "bandpass"; flt.Q.value = q;
    flt.frequency.setValueAtTime(f0, t); flt.frequency.exponentialRampToValueAtTime(Math.max(40, f1), t + dur);
    src.connect(flt); flt.connect(g);
  } else {
    src = ac.createOscillator(); src.type = type;
    src.frequency.setValueAtTime(f0, t); src.frequency.exponentialRampToValueAtTime(Math.max(20, f1), t + dur);
    src.connect(g);
  }
  g.connect(master); src.start(t); src.stop(t + dur + 0.02);
}

const SYNTH = {
  click: () => tone({ type: "square", f0: 880, f1: 660, dur: 0.05, vol: 0.12 }),
  select: () => { tone({ type: "square", f0: 660, dur: 0.06, vol: 0.12 }); tone({ type: "square", f0: 990, dur: 0.08, vol: 0.12, delay: 0.06 }); },
  bubble: () => tone({ type: "sine", f0: 300 + Math.random() * 300, f1: 900, dur: 0.12, vol: 0.12 }),
  splash: () => { tone({ noise: true, f0: 2000, f1: 300, dur: 0.5, vol: 0.5, q: 0.6 }); tone({ type: "sine", f0: 180, f1: 60, dur: 0.3, vol: 0.3 }); },
  catch: () => { tone({ type: "triangle", f0: 520, f1: 1040, dur: 0.12, vol: 0.25 }); tone({ type: "triangle", f0: 780, f1: 1560, dur: 0.15, vol: 0.2, delay: 0.08 }); },
  pick: () => tone({ type: "triangle", f0: 700, f1: 1200, dur: 0.1, vol: 0.2 }),
  coin: () => { tone({ type: "square", f0: 988, dur: 0.07, vol: 0.12 }); tone({ type: "square", f0: 1319, dur: 0.22, vol: 0.12, delay: 0.07 }); },
  whoosh: () => tone({ noise: true, f0: 400, f1: 3000, dur: 0.35, vol: 0.35, q: 0.8 }),
  slam: () => { tone({ type: "sine", f0: 140, f1: 40, dur: 0.45, vol: 0.6 }); tone({ noise: true, f0: 1200, f1: 200, dur: 0.25, vol: 0.4 }); },
  sizzle: () => tone({ noise: true, f0: 5000, f1: 4000, dur: 0.6, vol: 0.12, q: 2 }),
  hurt: () => { tone({ type: "sawtooth", f0: 300, f1: 90, dur: 0.25, vol: 0.25 }); },
  heartbeat: () => { tone({ type: "sine", f0: 70, f1: 50, dur: 0.12, vol: 0.5 }); tone({ type: "sine", f0: 65, f1: 45, dur: 0.12, vol: 0.4, delay: 0.16 }); },
  blip: () => tone({ type: "square", f0: 1400 + Math.random() * 200, dur: 0.02, vol: 0.05 }),
  fanfare: () => [523, 659, 784, 1047].forEach((f, i) => tone({ type: "square", f0: f, dur: 0.18, vol: 0.13, delay: i * 0.09 })),
  ding: () => { tone({ type: "sine", f0: 1568, dur: 0.6, vol: 0.2 }); tone({ type: "sine", f0: 2093, dur: 0.5, vol: 0.12, delay: 0.02 }); },
};

export function sfx(name) {
  if (!ac || muted) return;
  if (buffers[name]) {
    const s = ac.createBufferSource(); s.buffer = buffers[name];
    s.connect(master); s.start();
    return;
  }
  SYNTH[name]?.();
}
