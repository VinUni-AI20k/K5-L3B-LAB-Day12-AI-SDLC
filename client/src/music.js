// Generative, chill music engine (original, no samples). WebAudio only. Moods: theme / underwater / restaurant,
// plus cutscene cues cut_dawn / cut_dusk (sectioned 0-2, see cue()).
// Instruments: detuned sine/triangle pads -> lowpass, Karplus-Strong pluck (đàn tranh-ish, with "nhấn" bends
// and late vibrato), soft sub bass, FM electric piano, brushed noise drums, water / vinyl / bubble textures,
// generated-noise convolution reverbs. All melodies use the Vietnamese pentatonic (0,2,5,7,9 -> e.g. C D F G A).
// Timing: a lookahead scheduler that only *wakes* on a timer; every event time comes from ac.currentTime math.

const mtof = (m) => 440 * Math.pow(2, (m - 69) / 12);
const rnd = (a, b) => a + Math.random() * (b - a);
const pick = (arr) => arr[(Math.random() * arr.length) | 0];
const chance = (p) => Math.random() < p;
const PENTA = [0, 2, 5, 7, 9];
const FADE = 1.5;

// chord = { b: bass midi, p: pad midi notes }
const MOODS = {
  // dawn on the river: slow, airy, hopeful. Key of C, scale C D F G A.
  theme: {
    bpm: 70, swing: 0.5, barsPerChord: 2, tonic: 60, mel: [62, 86], density: 0.32, playProb: 0.7,
    send: { dry: 0.9, s: 0.35, l: 0.25 }, padCut: 1500, padVel: 0.045, wow: 3,
    prog: [
      { b: 41, p: [57, 60, 64, 67] }, // Fmaj9
      { b: 36, p: [55, 60, 62, 64] }, // Cadd9
      { b: 45, p: [55, 60, 64, 71] }, // Am9
      { b: 43, p: [53, 57, 60, 62] }, // G9sus4
    ],
    alt: { 1: [{ b: 40, p: [55, 60, 62, 64] }], 2: [{ b: 38, p: [53, 57, 60, 64] }], 3: [{ b: 43, p: [55, 59, 62, 64] }] },
    layers: { pad: 1, sub: 0.7, melody: 1, gliss: 0.6, water: 0.035, vinyl: 0.006 },
  },
  // dive: no percussion, deep pads, slow arpeggio with long reverb, bubbles. D "oán" colour, same pitch set.
  underwater: {
    bpm: 60, swing: 0.5, barsPerChord: 2, tonic: 62, mel: [62, 84], density: 0, playProb: 0,
    send: { dry: 0.7, s: 0.15, l: 0.7 }, padCut: 750, padVel: 0.05, wow: 0,
    prog: [
      { b: 38, p: [53, 57, 60, 64] }, // Dm9
      { b: 34, p: [50, 53, 57, 60] }, // Bbmaj9
      { b: 41, p: [52, 55, 57, 60] }, // Fmaj9
      { b: 36, p: [50, 55, 60, 62] }, // Csus2
    ],
    alt: { 2: [{ b: 45, p: [52, 55, 60, 62] }], 3: [{ b: 43, p: [50, 53, 57, 58] }] },
    layers: { pad: 1.1, sub: 0.8, arp: 1, bubbles: 1, rumble: 0.05 },
  },
  // night raft restaurant: lo-fi groove, IV-iii-ii-V in F, scale F G Bb C D.
  restaurant: {
    bpm: 84, swing: 0.6, barsPerChord: 1, tonic: 65, mel: [65, 86], density: 0.34, playProb: 0.6,
    send: { dry: 1, s: 0.3, l: 0.08 }, padCut: 1100, padVel: 0.022, wow: 6,
    prog: [
      { b: 46, p: [57, 60, 62, 65] }, // Bbmaj9
      { b: 45, p: [55, 60, 64, 67] }, // Am7
      { b: 43, p: [53, 57, 58, 62] }, // Gm9
      { b: 48, p: [53, 55, 58, 62] }, // C9sus4
    ],
    alt: { 1: [{ b: 38, p: [53, 57, 60, 64] }], 3: [{ b: 41, p: [52, 55, 57, 60] }] },
    layers: { pad: 0.6, bass: 1, ep: 1, drums: 1, melody: 0.9, gliss: 0.2, vinyl: 0.02, water: 0.012 },
  },
  // ---- cutscene cues (sections 0 calm / 1 pulse / 2 build; auto by bar count, or forced by cue(level)) ----
  // opening at dawn: slow swelling string pads, rising đàn tranh glissandi, frame-drum then taiko pulse
  cut_dawn: {
    cine: "dawn", bpm: 72, swing: 0.5, barsPerChord: 2, tonic: 60, mel: [62, 84], density: 0.24, playProb: 0.45,
    send: { dry: 0.85, s: 0.4, l: 0.45 }, padCut: 2600, padVel: 0.03, wow: 2, auto: [[3, 1], [11, 2]],
    prog: [
      { b: 45, p: [55, 60, 64, 71] }, // Am9
      { b: 41, p: [57, 60, 64, 67] }, // Fmaj9
      { b: 36, p: [55, 60, 62, 64] }, // Cadd9
      { b: 43, p: [55, 60, 62, 67] }, // Gsus4
    ],
    alt: { 2: [{ b: 40, p: [55, 59, 62, 64] }] },
    layers: { strings: 1, sub: 0.6, melody: 0.7, rise: 0.6, water: 0.03 },
  },
  // dusk & lanterns: warm pads + bell/kalimba arpeggios; cue(2) restarts the grid into a celebratory groove
  // (C F Am G, all-pentatonic voicings) with a bright FM brass chord on the downbeat for "MỞ CỬA!"
  cut_dusk: {
    cine: "dusk", bpm: 78, swing: 0.56, barsPerChord: 1, tonic: 60, mel: [64, 86], density: 0.22, playProb: 0.4,
    send: { dry: 0.9, s: 0.35, l: 0.4 }, padCut: 1600, padVel: 0.04, wow: 3, auto: [[8, 1]],
    prog: [
      { b: 41, p: [57, 60, 64, 67] }, // Fmaj9
      { b: 40, p: [55, 59, 62, 64] }, // Em7
      { b: 38, p: [53, 57, 60, 64] }, // Dm9
      { b: 43, p: [53, 57, 60, 62] }, // G9sus4
    ],
    prog2: [
      { b: 36, p: [60, 62, 67, 69] }, // C6/9
      { b: 41, p: [57, 60, 62, 65] }, // F6/9
      { b: 45, p: [57, 60, 62, 67] }, // Am11
      { b: 43, p: [55, 60, 62, 67] }, // Gsus4
    ],
    alt: { 1: [{ b: 45, p: [55, 60, 64, 67] }] },
    layers: { pad: 0.9, sub: 0.6, melody: 0.6, bells: 1, water: 0.02, vinyl: 0.004 },
  },
};

export function createMusic(ac, dest) {
  const sr = ac.sampleRate;
  const bus = ac.createGain();
  const warm = ac.createBiquadFilter(); warm.type = "lowpass"; warm.frequency.value = 7500; warm.Q.value = 0.5;
  const comp = ac.createDynamicsCompressor();
  comp.threshold.value = -20; comp.knee.value = 12; comp.ratio.value = 3; comp.attack.value = 0.02; comp.release.value = 0.4;
  bus.connect(warm); warm.connect(comp); comp.connect(dest);

  // ---- shared buffers ----
  const noise = ac.createBuffer(1, sr * 2, sr);
  { const d = noise.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; }
  const crackle = ac.createBuffer(1, sr * 4, sr);
  {
    const d = crackle.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * 0.02;
    for (let k = 0; k < 90; k++) {
      const at = (Math.random() * (d.length - 200)) | 0, a = rnd(0.2, 1) * (chance(0.5) ? 1 : -1);
      for (let j = 0; j < 40; j++) d[at + j] += a * Math.exp(-j / 6);
    }
  }

  // ---- reverbs: stereo decaying noise, progressively darker ----
  function makeVerb(dur, pow) {
    const len = Math.floor(sr * dur), ir = ac.createBuffer(2, len, sr);
    for (let c = 0; c < 2; c++) {
      const d = ir.getChannelData(c); let lp = 0;
      for (let i = 0; i < len; i++) {
        const k = i / len, coef = 0.9 - 0.75 * k; // brighter early, darker tail
        lp += coef * ((Math.random() * 2 - 1) - lp);
        d[i] = lp * Math.pow(1 - k, pow);
      }
    }
    const hp = ac.createBiquadFilter(); hp.type = "highpass"; hp.frequency.value = 220;
    const conv = ac.createConvolver(); conv.buffer = ir;
    const ret = ac.createGain(); ret.gain.value = 0.9;
    hp.connect(conv); conv.connect(ret); ret.connect(bus);
    return hp;
  }
  const verbS = makeVerb(2.8, 2.2), verbL = makeVerb(6.5, 1.5);

  // ---- Karplus-Strong pluck buffers (cached by loop length) ----
  const ks = new Map();
  function ksBuffer(N, bright, damp) {
    const key = N + "|" + bright + "|" + damp;
    if (ks.has(key)) return ks.get(key);
    const len = Math.floor(sr * 2.4), buf = ac.createBuffer(1, len, sr), d = buf.getChannelData(0);
    let lp = 0, mean = 0;
    for (let i = 0; i < N; i++) { lp += bright * ((Math.random() * 2 - 1) - lp); d[i] = lp; mean += lp; }
    mean /= N; for (let i = 0; i < N; i++) d[i] -= mean;
    d[N] = d[0] * damp;
    for (let i = N + 1; i < len; i++) d[i] = damp * 0.5 * (d[i - N] + d[i - N - 1]);
    let peak = 0; for (let i = 0; i < len; i++) peak = Math.max(peak, Math.abs(d[i]));
    if (peak > 0) for (let i = 0; i < len; i++) d[i] *= 0.8 / peak;
    ks.set(key, buf);
    return buf;
  }

  // ---- instances (one per playing mood) ----
  let cur = null;
  const live = new Set();

  function makeInst(name) {
    const def = MOODS[name];
    const inst = { name, def, step: 0, next: 0, chord: null, chordIdx: -1, cycle: null, phrase: null, prevPhrase: null, deg: 0, arpI: 0, nodes: [] };
    // fade gains (dry + 2 reverb sends) -> ramped together
    const dry = ac.createGain(), sS = ac.createGain(), sL = ac.createGain();
    dry.connect(bus); sS.connect(verbS); sL.connect(verbL);
    inst.fades = [[dry, def.send.dry], [sS, def.send.s], [sL, def.send.l]];
    for (const [g] of inst.fades) g.gain.value = 0;
    const track = (d, s, l, pre) => { // returns the node voices connect into
      const g = ac.createGain();
      const a = ac.createGain(); a.gain.value = d; g.connect(a); a.connect(dry);
      const b = ac.createGain(); b.gain.value = s; g.connect(b); b.connect(sS);
      const c = ac.createGain(); c.gain.value = l; g.connect(c); c.connect(sL);
      if (pre) { pre[pre.length - 1].connect(g); return pre[0]; }
      return g;
    };
    // pad: lowpass with a slow breathing LFO on cutoff
    const padLp = ac.createBiquadFilter(); padLp.type = "lowpass"; padLp.frequency.value = def.padCut; padLp.Q.value = 0.7;
    const lfo = ac.createOscillator(); lfo.frequency.value = rnd(0.05, 0.09);
    const lfoG = ac.createGain(); lfoG.gain.value = def.padCut * 0.35; lfo.connect(lfoG); lfoG.connect(padLp.frequency);
    inst.pad = track(1, 1, 1, [padLp]);
    const plLp = ac.createBiquadFilter(); plLp.type = "lowpass"; plLp.frequency.value = 3200;
    const plBody = ac.createBiquadFilter(); plBody.type = "peaking"; plBody.frequency.value = 450; plBody.gain.value = 3; plBody.Q.value = 1;
    plLp.connect(plBody);
    inst.pluck = track(1, 1.2, 1, [plLp, plBody]);
    inst.bass = track(1, 0.05, 0, null);
    inst.ep = track(1, 0.8, 0.3, null);
    const drLp = ac.createBiquadFilter(); drLp.type = "lowpass"; drLp.frequency.value = 5200;
    inst.drums = track(1, 0.5, 0, [drLp]);
    inst.tex = track(1, 0, 0, null);
    inst.fx = track(0.6, 0.6, 1.2, null);
    if (def.cine) {
      inst.bell = track(0.9, 0.8, 0.7, null);
      const brLp = ac.createBiquadFilter(); brLp.type = "lowpass"; brLp.frequency.value = 4200;
      inst.brass = track(1, 0.6, 0.35, [brLp]);
      inst.level = 0; inst.cued = 0; inst.bars = 0;
    }
    // lo-fi tape "wow": a shared slow LFO wired into oscillator detunes
    inst.wow = ac.createGain(); inst.wow.gain.value = def.wow || 0;
    const wowO = ac.createOscillator(); wowO.frequency.value = rnd(0.25, 0.45); wowO.connect(inst.wow);
    const t = ac.currentTime;
    lfo.start(t); wowO.start(t);
    inst.loops = [lfo, wowO];
    // textures
    const L = def.layers;
    if (L.water) inst.loops.push(loopNoise(inst, noise, "lowpass", 520, 0.6, L.water, 0.07));
    if (L.rumble) inst.loops.push(loopNoise(inst, noise, "lowpass", 260, 0.8, L.rumble, 0.05));
    if (L.vinyl) inst.loops.push(loopNoise(inst, crackle, "bandpass", 2600, 0.5, L.vinyl, 0));
    return inst;
  }

  function loopNoise(inst, buf, type, freq, q, vol, lfoRate) {
    const s = ac.createBufferSource(); s.buffer = buf; s.loop = true;
    s.playbackRate.value = rnd(0.9, 1.1);
    const f = ac.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
    const g = ac.createGain(); g.gain.value = vol;
    s.connect(f); f.connect(g); g.connect(inst.tex);
    if (lfoRate) { // slow swell, like water lapping
      const o = ac.createOscillator(); o.frequency.value = lfoRate;
      const og = ac.createGain(); og.gain.value = vol * 0.6; o.connect(og); og.connect(g.gain);
      o.start(ac.currentTime); inst.loops.push(o);
    }
    s.start(ac.currentTime, Math.random() * buf.duration);
    return s;
  }

  // ---- voices ----
  function env(g, t, a, peak, hold, rel) {
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(peak, t + a);
    g.gain.setValueAtTime(peak, t + Math.max(a, hold));
    g.gain.linearRampToValueAtTime(0, t + Math.max(a, hold) + rel);
  }
  function wowTo(inst, node, param) {
    if (!inst.def.wow) return;
    inst.wow.connect(param);
    node.onended = () => { try { inst.wow.disconnect(param); } catch (e) {} };
  }
  function pad(inst, m, t, dur, vel) {
    const g = ac.createGain(); g.connect(inst.pad);
    const att = inst.name === "underwater" ? 2.2 : 1.4, rel = inst.name === "underwater" ? 3.5 : 2.4;
    env(g, t, att, vel, dur, rel);
    const end = t + dur + rel + 0.1;
    [["sine", -7], ["triangle", 7], ["sine", 1200 + rnd(-4, 4)]].forEach(([type, det], i) => {
      const o = ac.createOscillator(); o.type = type; o.frequency.value = mtof(m); o.detune.value = det + rnd(-3, 3);
      wowTo(inst, o, o.detune);
      const og = ac.createGain(); og.gain.value = i === 2 ? 0.12 : 0.5; // faint octave shimmer
      o.connect(og); og.connect(g); o.start(t); o.stop(end);
    });
  }
  function sub(inst, m, t, dur, vel, att = 0.06) {
    const g = ac.createGain(); g.connect(inst.bass);
    g.gain.setValueAtTime(0, t);
    g.gain.linearRampToValueAtTime(vel, t + att);
    g.gain.setTargetAtTime(vel * 0.6, t + att, 0.4);
    g.gain.setValueAtTime(vel * 0.55, t + dur);
    g.gain.linearRampToValueAtTime(0, t + dur + 0.25);
    const lo = ac.createOscillator(); lo.frequency.value = mtof(m - 12);
    const hi = ac.createOscillator(); hi.frequency.value = mtof(m);
    const hg = ac.createGain(); hg.gain.value = 0.45;
    lo.connect(g); hi.connect(hg); hg.connect(g);
    lo.start(t); hi.start(t); lo.stop(t + dur + 0.3); hi.stop(t + dur + 0.3);
  }
  function pluck(inst, m, t, vel, o = {}) {
    const f = mtof(m), N = Math.max(2, Math.floor(sr / f - 0.5));
    const rate = f / (sr / (N + 0.5));
    const buf = ksBuffer(N, o.bright ?? 0.45, o.damp ?? 0.996);
    const s = ac.createBufferSource(); s.buffer = buf;
    if (o.bend) { // "nhấn": press the string up into the note
      s.playbackRate.setValueAtTime(rate * Math.pow(2, -o.bend / 12), t);
      s.playbackRate.exponentialRampToValueAtTime(rate, t + 0.11);
    } else s.playbackRate.setValueAtTime(rate, t);
    if (o.vib) { // "rung": late vibrato on long notes
      const lfo = ac.createOscillator(); lfo.frequency.value = rnd(4.8, 5.8);
      const lg = ac.createGain(); lg.gain.setValueAtTime(0, t); lg.gain.linearRampToValueAtTime(0, t + 0.25);
      lg.gain.linearRampToValueAtTime(rate * 0.009, t + 0.7);
      lfo.connect(lg); lg.connect(s.playbackRate); lfo.start(t); lfo.stop(t + 2.4);
    }
    const g = ac.createGain();
    const len = o.len ?? 2.3;
    g.gain.setValueAtTime(vel, t);
    g.gain.setValueAtTime(vel, t + len - 0.3);
    g.gain.linearRampToValueAtTime(0, t + len);
    s.connect(g); g.connect(inst.pluck);
    s.start(t); s.stop(t + len + 0.02);
  }
  function ep(inst, m, t, dur, vel) { // soft FM electric piano
    const f = mtof(m), end = t + dur + 0.8;
    const c = ac.createOscillator(); c.frequency.value = f;
    const mo = ac.createOscillator(); mo.frequency.value = f;
    const mg = ac.createGain();
    mg.gain.setValueAtTime(f * 1.1, t); mg.gain.exponentialRampToValueAtTime(f * 0.12, t + 0.7);
    mo.connect(mg); mg.connect(c.frequency);
    wowTo(inst, c, c.detune);
    const g = ac.createGain();
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vel, t + 0.006);
    g.gain.setTargetAtTime(vel * 0.35, t + 0.006, 0.5);
    g.gain.setValueAtTime(vel * 0.3, t + dur);
    g.gain.linearRampToValueAtTime(0, end);
    const lp = ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 2400;
    c.connect(lp); lp.connect(g); g.connect(inst.ep);
    c.start(t); mo.start(t); c.stop(end + 0.05); mo.stop(end + 0.05);
  }
  function noiseHit(inst, t, type, freq, q, vel, att, dec, dest) {
    const s = ac.createBufferSource(); s.buffer = noise;
    const f = ac.createBiquadFilter(); f.type = type; f.frequency.value = freq; f.Q.value = q;
    const g = ac.createGain();
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vel, t + att);
    g.gain.exponentialRampToValueAtTime(0.0001, t + att + dec);
    s.connect(f); f.connect(g); g.connect(dest || inst.drums);
    s.start(t, Math.random() * 1.5); s.stop(t + att + dec + 0.05);
  }
  function kick(inst, t, vel) {
    const o = ac.createOscillator();
    o.frequency.setValueAtTime(115, t); o.frequency.exponentialRampToValueAtTime(46, t + 0.13);
    const g = ac.createGain();
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vel, t + 0.005);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.38);
    o.connect(g); g.connect(inst.drums); o.start(t); o.stop(t + 0.42);
    noiseHit(inst, t, "lowpass", 260, 0.7, vel * 0.25, 0.002, 0.05);
  }
  function brushSnare(inst, t, vel) {
    noiseHit(inst, t, "bandpass", 2100, 0.7, vel, 0.012, 0.24);
    noiseHit(inst, t, "highpass", 5500, 0.5, vel * 0.3, 0.03, 0.18);
    const o = ac.createOscillator(); o.frequency.value = 185;
    const g = ac.createGain(); g.gain.setValueAtTime(vel * 0.25, t); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.09);
    o.connect(g); g.connect(inst.drums); o.start(t); o.stop(t + 0.1);
  }
  // ---- cutscene instruments ----
  // string-like pad: two detuned triangles + faint detuned saws, all under a slow-opening heavy lowpass
  function strings(inst, m, t, dur, vel) {
    const att = 2.6, rel = 2.8, end = t + dur + rel + 0.1;
    const g = ac.createGain(); env(g, t, att, vel, dur, rel); g.connect(inst.pad);
    const lp = ac.createBiquadFilter(); lp.type = "lowpass"; lp.Q.value = 0.9;
    lp.frequency.setValueAtTime(420, t);
    lp.frequency.linearRampToValueAtTime(1300 + 350 * (inst.level || 0), t + att);
    lp.frequency.linearRampToValueAtTime(800, t + dur + rel);
    lp.connect(g);
    [["triangle", -8, 0.5], ["triangle", 8, 0.5], ["sawtooth", 4, 0.1], ["sawtooth", -13, 0.07]].forEach(([type, det, lv]) => {
      const o = ac.createOscillator(); o.type = type; o.frequency.value = mtof(m); o.detune.value = det + rnd(-3, 3);
      wowTo(inst, o, o.detune);
      const og = ac.createGain(); og.gain.value = lv;
      o.connect(og); og.connect(lp); o.start(t); o.stop(end);
    });
  }
  function frameDrum(inst, t, vel, hi) {
    const f0 = hi ? 255 : 170;
    const o = ac.createOscillator();
    o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f0 * 0.62, t + 0.14);
    const g = ac.createGain();
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vel, t + 0.003);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.22);
    o.connect(g); g.connect(inst.drums); o.start(t); o.stop(t + 0.25);
    noiseHit(inst, t, "bandpass", hi ? 1600 : 900, 1.1, vel * 0.5, 0.002, 0.07);
  }
  function taiko(inst, t, vel) {
    const o = ac.createOscillator();
    o.frequency.setValueAtTime(110, t); o.frequency.exponentialRampToValueAtTime(44, t + 0.5);
    const g = ac.createGain();
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vel, t + 0.004);
    g.gain.exponentialRampToValueAtTime(0.0001, t + 0.8);
    const o2 = ac.createOscillator(); o2.type = "triangle";
    o2.frequency.setValueAtTime(200, t); o2.frequency.exponentialRampToValueAtTime(70, t + 0.1);
    const g2 = ac.createGain();
    g2.gain.setValueAtTime(0, t); g2.gain.linearRampToValueAtTime(vel * 0.3, t + 0.003);
    g2.gain.exponentialRampToValueAtTime(0.0001, t + 0.12);
    o.connect(g); o2.connect(g2); g.connect(inst.drums); g2.connect(inst.drums);
    o.start(t); o.stop(t + 0.85); o2.start(t); o2.stop(t + 0.15);
    noiseHit(inst, t, "lowpass", 420, 0.9, vel * 0.6, 0.003, 0.14);
  }
  // bell / kalimba: FM sine, inharmonic 3.5 ratio, bright index that decays to a pure tone
  function bellFM(inst, m, t, vel, dur = 2.2) {
    const f = mtof(m), end = t + dur;
    const c = ac.createOscillator(); c.frequency.value = f;
    const mo = ac.createOscillator(); mo.frequency.value = f * 3.5;
    const mg = ac.createGain();
    mg.gain.setValueAtTime(f * 1.8, t); mg.gain.exponentialRampToValueAtTime(f * 0.02, t + 0.6);
    mo.connect(mg); mg.connect(c.frequency);
    const g = ac.createGain();
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vel, t + 0.003);
    g.gain.exponentialRampToValueAtTime(0.0001, end);
    c.connect(g); g.connect(inst.bell);
    c.start(t); mo.start(t); c.stop(end + 0.05); mo.stop(end + 0.05);
  }
  // bright brass-like FM chord (ratio 1, modulation index swells with the attack)
  function brassFM(inst, notes, t, dur, vel) {
    notes.forEach((m, k) => {
      const f = mtof(m), s = t + k * 0.006, end = s + dur + 0.35;
      const c = ac.createOscillator(); c.frequency.value = f;
      const mo = ac.createOscillator(); mo.frequency.value = f; mo.detune.value = rnd(-5, 5);
      const mg = ac.createGain();
      mg.gain.setValueAtTime(f * 0.4, s); mg.gain.linearRampToValueAtTime(f * 2.8, s + 0.06);
      mg.gain.exponentialRampToValueAtTime(f * 1.0, s + dur);
      mo.connect(mg); mg.connect(c.frequency);
      const g = ac.createGain();
      g.gain.setValueAtTime(0, s); g.gain.linearRampToValueAtTime(vel, s + 0.035);
      g.gain.setTargetAtTime(vel * 0.6, s + 0.035, 0.25);
      g.gain.setValueAtTime(vel * 0.55, s + dur);
      g.gain.linearRampToValueAtTime(0, end);
      c.connect(g); g.connect(inst.brass);
      c.start(s); mo.start(s); c.stop(end + 0.05); mo.stop(end + 0.05);
    });
  }
  function bubble(inst, t, vol) {
    const o = ac.createOscillator(), f0 = rnd(280, 520), d = rnd(0.05, 0.11);
    o.frequency.setValueAtTime(f0, t); o.frequency.exponentialRampToValueAtTime(f0 * rnd(2.2, 3.2), t + d);
    const g = ac.createGain();
    g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(vol, t + 0.008);
    g.gain.exponentialRampToValueAtTime(0.0001, t + d);
    o.connect(g); g.connect(inst.fx); o.start(t); o.stop(t + d + 0.02);
  }

  // ---- harmony / melody helpers ----
  function pitchList(def) {
    const out = [];
    for (let m = def.mel[0]; m <= def.mel[1]; m++) if (PENTA.includes(((m - def.tonic) % 12 + 12) % 12)) out.push(m);
    return out;
  }
  function chooseCycle(def, prog = def.prog) { // light re-harmonisation each time round
    return prog.map((c, i) => (prog === def.prog && def.alt[i] && chance(0.3) ? pick(def.alt[i]) : c)).map((c) => {
      let p = c.p.slice();
      if (chance(0.25)) p = p.slice(1).concat(p[0] + 12); // inversion
      return { b: c.b, p };
    });
  }
  function genPhrase(def, prev) {
    if (prev && chance(0.45)) return { r: prev.r, mv: prev.mv.map((v) => (chance(0.25) ? v + pick([-1, 1]) : v)) };
    const r = new Array(16).fill(0), mv = new Array(16).fill(0);
    for (let s = 0; s < 13; s++) r[s] = chance(def.density * (s % 2 === 0 ? 1.4 : 0.55)) ? 1 : 0;
    if (chance(0.6)) r[0] = 1;
    if (r.reduce((a, b) => a + b, 0) < 2) { r[0] = 1; r[4] = 1; r[6] = 1; }
    for (let s = 0; s < 16; s++) mv[s] = pick([-2, -1, -1, -1, 0, 1, 1, 1, 2, -3, 3]);
    return { r, mv };
  }
  function snapToChord(list, i, chord) {
    const pcs = chord.p.concat(chord.b).map((m) => m % 12);
    for (const d of [0, -1, 1]) { const j = i + d; if (list[j] !== undefined && pcs.includes(list[j] % 12)) return j; }
    return i;
  }

  // ---- per-step scheduling ----
  function scheduleStep(inst, i, t) {
    const def = inst.def, L = def.layers;
    const spb = 60 / def.bpm, stepInBar = i % 8, bar = Math.floor(i / 8);
    const barDur = spb * 4, chordDur = barDur * def.barsPerChord;
    if (!inst.list) { inst.list = pitchList(def); inst.deg = Math.floor(inst.list.length * 0.45); }
    const list = inst.list;

    if (def.cine && stepInBar === 0) { // section level: max(auto by bars played, cued)
      inst.bars++;
      let auto = 0; for (const [b, l] of def.auto || []) if (inst.bars > b) auto = Math.max(auto, l);
      inst.level = Math.max(inst.cued, auto);
    }
    if (stepInBar === 0 && bar % def.barsPerChord === 0) {
      const prog = def.prog2 && inst.level >= 2 ? def.prog2 : def.prog;
      const ci = Math.floor(bar / def.barsPerChord) % prog.length;
      if (ci === 0 || !inst.cycle || inst.cycleProg !== prog) { inst.cycle = chooseCycle(def, prog); inst.cycleProg = prog; }
      const ch = inst.cycle[ci]; inst.chord = ch; inst.chordIdx = ci;
      if (L.pad) for (const m of ch.p) pad(inst, m, t, chordDur, def.padVel * L.pad);
      if (L.strings) {
        for (const m of ch.p) strings(inst, m, t, chordDur, 0.05 * L.strings);
        if (inst.level >= 2) strings(inst, ch.p[ch.p.length - 1] + 12, t, chordDur, 0.03 * L.strings); // high line joins
      }
      // rising đàn tranh glissando into each chord, longer and faster as the cue builds
      if (L.rise && bar > 0 && chance(L.rise + 0.15 * inst.level)) {
        const lv = inst.level, start = (Math.random() * 3) | 0, n = 6 + lv * 2 + ((Math.random() * 3) | 0), sp = 0.075 - 0.012 * lv;
        for (let k = 0; k < n && start + k < list.length; k++) pluck(inst, list[start + k], t + sp * k, 0.04 + 0.01 * k, { bright: 0.6, len: 1.8 });
      }
      if (L.sub) sub(inst, ch.b, t, chordDur * 0.98, 0.16 * L.sub, inst.name === "underwater" ? 1.2 : 0.3);
      // đàn tranh glissando ripple into a new progression cycle
      if (L.gliss && ci === 0 && bar > 0 && chance(L.gliss)) {
        const start = Math.max(0, Math.floor(rnd(0, list.length * 0.35))), n = 5 + ((Math.random() * 3) | 0);
        for (let k = 0; k < n && start + k < list.length; k++) pluck(inst, list[start + k], t + 0.055 * k, 0.05 + 0.012 * k, { bright: 0.55, len: 1.6 });
      }
    }
    const ch = inst.chord;

    // melody (phrases of 2 bars; call / rest / answer)
    if (L.melody && def.playProb) {
      if (i % 16 === 0) {
        inst.phrase = chance(def.playProb) ? genPhrase(def, inst.prevPhrase) : null;
        if (inst.phrase) inst.prevPhrase = inst.phrase;
        if (bar < 1) inst.phrase = null; // let the bed breathe first
      }
      const ph = inst.phrase, s = i % 16;
      if (ph && ph.r[s]) {
        const mid = list.length * 0.5;
        let d = inst.deg + ph.mv[s] + (inst.deg > mid + 3 ? -1 : inst.deg < mid - 4 ? 1 : 0);
        d = Math.max(0, Math.min(list.length - 1, d));
        if (s % 4 === 0) d = snapToChord(list, d, ch);
        let gap = 1; while (s + gap < 16 && !ph.r[s + gap]) gap++;
        const up = d > inst.deg; inst.deg = d;
        const m = list[d];
        pluck(inst, m, t + rnd(0, 0.012), 0.16 * L.melody * rnd(0.8, 1.05), {
          bend: up && chance(0.3) ? (chance(0.5) ? 2 : 1) : 0,
          vib: gap >= 3,
          bright: 0.42, damp: 0.9965,
        });
        if (gap >= 4 && chance(0.3)) pluck(inst, m - 12, t + 0.01, 0.06 * L.melody, { bright: 0.3 }); // octave below
      }
    }

    // underwater slow arpeggio (quarter notes, ping-pong)
    if (L.arp && stepInBar % 2 === 0 && ch && chance(0.8)) {
      const notes = ch.p.map((m) => m + 12).concat(ch.p[0] + 24).sort((a, b) => a - b);
      const seq = notes.concat(notes.slice(1, -1).reverse());
      const m = seq[inst.arpI++ % seq.length];
      pluck(inst, m, t + rnd(0, 0.02), 0.085 * L.arp * rnd(0.75, 1), { bright: 0.22, damp: 0.9975, vib: chance(0.2) });
    }
    if (L.bubbles && chance(0.11)) {
      const n = chance(0.3) ? 3 : 1;
      for (let k = 0; k < n; k++) bubble(inst, t + rnd(0, spb / 2) + k * rnd(0.05, 0.12), 0.03 * L.bubbles);
    }

    if (def.cine) cineStep(inst, i, t, spb, ch, list);

    // restaurant groove
    if (L.drums && bar >= 2) {
      if (stepInBar === 0) inst.drop = bar % 8 === 7 && chance(0.35); // breathe: no kick some bars
      const kv = 0.42 * L.drums;
      if (!inst.drop) {
        if (stepInBar === 0) kick(inst, t, kv);
        if (stepInBar === 3 && chance(0.35)) kick(inst, t, kv * 0.6);
        if (stepInBar === 5 && chance(0.55)) kick(inst, t, kv * 0.8);
      }
      if (stepInBar === 2 || stepInBar === 6) brushSnare(inst, t + 0.008, 0.11 * L.drums);
      if (stepInBar === 7 && chance(0.15)) brushSnare(inst, t, 0.035 * L.drums);
      if (chance(0.85)) noiseHit(inst, t, "highpass", 7000, 0.6, (stepInBar % 2 ? 0.018 : 0.03) * L.drums, 0.006, stepInBar % 2 ? 0.05 : 0.09);
    }
    if (L.bass && ch) {
      const e = spb / 2;
      if (stepInBar === 0) sub(inst, ch.b, t, e * 2.6, 0.2 * L.bass, 0.02);
      if (stepInBar === 3 && chance(0.5)) sub(inst, ch.b + pick([7, 12, 0]), t, e * 0.9, 0.12 * L.bass, 0.02);
      if (stepInBar === 5 && chance(0.6)) sub(inst, ch.b + pick([0, 7]), t, e * 1.6, 0.15 * L.bass, 0.02);
      if (stepInBar === 7 && chance(0.3)) sub(inst, ch.b + pick([-1, 2, -2]), t, e * 0.8, 0.1 * L.bass, 0.02); // approach note
    }
    if (L.ep && ch) {
      if (stepInBar === 0) inst.comp = pick([
        [[0, 3, 1], [3, 5, 0.7]],
        [[0, 2, 1], [3, 1, 0.6], [6, 2, 0.75]],
        [[1, 3, 0.85], [5, 3, 0.7]],
        [[0, 8, 0.9]],
        [[0, 2, 0.9], [4, 3, 0.8]],
      ]);
      const hit = inst.comp && inst.comp.find((c) => c[0] === stepInBar);
      if (hit) {
        const e = spb / 2, voicing = chance(0.3) ? ch.p.slice(1).concat(ch.p[0] + 12) : ch.p;
        voicing.forEach((m, k) => ep(inst, m, t + k * rnd(0.004, 0.012), hit[1] * e, 0.05 * hit[2] * L.ep));
      }
    }
  }

  // cutscene layers per eighth-note step: drums build by section; dusk adds bell arps, groove, bass, brass
  function cineStep(inst, i, t, spb, ch, list) {
    const def = inst.def, lv = inst.level, s8 = i % 8, bar = Math.floor(i / 8), e = spb / 2;
    if (def.cine === "dawn") {
      if (lv >= 1) {
        if (s8 === 0) frameDrum(inst, t, lv >= 2 ? 0.26 : 0.2, false);
        if (s8 === 3) frameDrum(inst, t, 0.1, true);
        if (s8 === 4) frameDrum(inst, t, 0.14, false);
        if (s8 === 7 && chance(0.4)) frameDrum(inst, t, 0.07, true);
      }
      if (lv >= 2) {
        if (s8 === 0) taiko(inst, t, 0.42);
        if (s8 === 4) taiko(inst, t, 0.28);
        if (s8 % 2 === 1) frameDrum(inst, t, 0.06 + 0.012 * s8, true);
        if (bar % 4 === 3 && s8 >= 6) { taiko(inst, t, 0.22); taiko(inst, t + e / 2, 0.3); } // fill into the next phrase
      }
      return;
    }
    // dusk: bell / kalimba arpeggio over the pads (chord tones, kept to the pentatonic where possible)
    if (ch) {
      let notes = ch.p.map((m) => m + 12).filter((m) => PENTA.includes(((m - def.tonic) % 12 + 12) % 12));
      if (notes.length < 3) notes = ch.p.map((m) => m + 12);
      notes = notes.sort((a, b) => a - b).concat(notes[0] + 12);
      const pat = [0, 1, 2, 3, 2, 1, 3, 2];
      const p = pat[s8] % notes.length;
      const play = lv === 0 ? s8 % 2 === 0 && chance(0.75) : lv === 1 ? chance(0.85) : s8 % 2 === 0 || chance(0.5);
      if (play) bellFM(inst, notes[p], t + rnd(0, 0.01), (lv >= 2 ? 0.045 : 0.055) * rnd(0.75, 1), lv >= 2 ? 1.2 : 2.2);
    }
    if (lv === 1) {
      if (s8 === 0) frameDrum(inst, t, 0.16, false);
      if (s8 === 4) frameDrum(inst, t, 0.1, false);
      if (s8 % 2 === 1) noiseHit(inst, t, "highpass", 6500, 0.6, 0.016, 0.01, 0.06); // shaker
    }
    if (lv >= 2) {
      if (inst.burst && s8 === 0) { // "MỞ CỬA!": big brass chord + taiko + crash on the first downbeat
        inst.burst = false;
        if (ch) brassFM(inst, ch.p.concat(ch.p[0] + 12, ch.b + 12), t, 1.4, 0.06);
        taiko(inst, t, 0.5);
        noiseHit(inst, t, "highpass", 5500, 0.5, 0.07, 0.003, 1.4);
      } else if (ch) {
        if (s8 === 0) brassFM(inst, ch.p.concat(ch.p[0] + 12), t, e * 1.6, 0.032);
        if (s8 === 3 && chance(0.5)) brassFM(inst, ch.p.slice(1).concat(ch.p[0] + 12), t, e * 0.7, 0.024);
      }
      if (s8 === 0) kick(inst, t, 0.42);
      if (s8 === 3 && chance(0.5)) kick(inst, t, 0.26);
      if (s8 === 5) kick(inst, t, 0.34);
      if (s8 === 2 || s8 === 6) { brushSnare(inst, t + 0.006, 0.12); frameDrum(inst, t, 0.1, true); }
      noiseHit(inst, t, "highpass", 7000, 0.6, s8 % 2 ? 0.022 : 0.034, 0.005, s8 % 2 ? 0.05 : 0.08);
      if (ch) {
        if (s8 === 0) sub(inst, ch.b, t, e * 2.4, 0.2, 0.02);
        if (s8 === 3) sub(inst, ch.b + 12, t, e * 0.8, 0.12, 0.02);
        if (s8 === 5) sub(inst, ch.b + 7, t, e * 1.4, 0.15, 0.02);
      }
    }
  }

  // ---- scheduler: wakes on a timer, schedules by ac.currentTime ----
  let timer = null;
  function tick() {
    timer = null;
    const ahead = typeof document !== "undefined" && document.hidden ? 1.5 : 0.3;
    for (const inst of live) {
      if (inst.dead) continue;
      const now = ac.currentTime;
      if (inst.restartAt) { // cue(2) in cut_dusk: restart the bar grid on the title impact
        inst.next = Math.max(inst.restartAt, now + 0.02); inst.step = 0; inst.cycle = null; inst.restartAt = 0; inst.burst = true;
      }
      if (inst.next < now - 0.2) inst.next = now + 0.05; // resync after a stall instead of a burst
      while (inst.next < now + ahead) {
        scheduleStep(inst, inst.step, inst.next);
        const e = 60 / inst.def.bpm / 2, sw = inst.def.swing || 0.5;
        inst.next += (inst.step % 2 === 0 ? sw : 1 - sw) * 2 * e;
        inst.step++;
      }
    }
    if (live.size) timer = setTimeout(tick, 40);
  }

  function fadeIn(inst) {
    const t = ac.currentTime;
    for (const [g, v] of inst.fades) { g.gain.cancelScheduledValues(t); g.gain.setValueAtTime(0, t); g.gain.linearRampToValueAtTime(v, t + FADE); }
  }
  function kill(inst) {
    inst.dead = true;
    const t = ac.currentTime;
    for (const [g] of inst.fades) { g.gain.cancelScheduledValues(t); g.gain.setValueAtTime(g.gain.value, t); g.gain.linearRampToValueAtTime(0, t + FADE); }
    for (const s of inst.loops) { try { s.stop(t + FADE + 0.1); } catch (e) {} }
    setTimeout(() => { for (const [g] of inst.fades) g.disconnect(); live.delete(inst); }, (FADE + 6) * 1000);
  }

  return {
    has: (name) => !!MOODS[name],
    play(name) {
      if (cur && cur.name === name) return true;
      if (cur) kill(cur);
      cur = null;
      if (!MOODS[name]) return false;
      cur = makeInst(name);
      cur.next = ac.currentTime + 0.08;
      live.add(cur); fadeIn(cur);
      if (!timer) tick();
      return true;
    },
    stop() { if (cur) kill(cur); cur = null; },
    // cutscene section cue (cut_dawn / cut_dusk only): 0 calm, 1 pulse, 2 build; dusk 2 restarts into the groove
    cue(level) {
      if (!cur || !cur.def.cine) return false;
      const lv = Math.max(0, Math.min(2, level | 0));
      if (lv >= 2 && cur.level < 2 && cur.def.prog2) cur.restartAt = ac.currentTime + 0.14;
      cur.cued = lv; cur.level = Math.max(cur.level, lv);
      return true;
    },
    current: () => (cur ? cur.name : null),
  };
}
