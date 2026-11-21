// Babble voices for dialogue ("fake speaking", cozy-game style). Each syllable = a soft glottal-ish
// periodic wave through two formant bandpasses, with a pitch contour borrowed from the Vietnamese tone
// marks in the text being typed (sắc rises, huyền falls, hỏi dips, ngã breaks, nặng drops), so lines
// "sound" Vietnamese without saying anything. Per-speaker pitch / timbre / speed.

const rnd = (a, b) => a + Math.random() * (b - a);
const pick = (arr) => arr[(Math.random() * arr.length) | 0];

// formants (Hz) for an adult-ish voice; scaled per speaker
const VOWELS = { a: [760, 1250], e: [520, 1850], i: [330, 2250], o: [560, 900], u: [350, 850], y: [330, 2250], ơ: [500, 1400] };
const VOWEL_KEYS = Object.keys(VOWELS);
// tone contours in semitones across the syllable (start, mid, end)
const TONES = {
  ngang: [0, 0, -0.4], sac: [-0.6, 0.8, 3], huyen: [-0.3, -1.4, -2.6], hoi: [-0.6, -2.4, 0.8],
  nga: [0.2, -1.2, 3.4], nang: [-0.8, -2.5, -4.2],
};
const MARKS = { "́": "sac", "̀": "huyen", "̉": "hoi", "̃": "nga", "̣": "nang" };

const PROFILES = {
  // Út Sen: high, bright, quick
  sen: { f0: 345, form: 1.22, dur: 0.058, every: 2, minGap: 0.05, range: 3, vib: 0, vibRate: 0, wobble: 0, toneAmt: 1, vol: 0.8, cut: 5200 },
  // Bà Tư: lower, warm, a little wobbly (slow vibrato + pitch jitter), slower syllables
  ba: { f0: 192, form: 0.96, dur: 0.092, every: 3, minGap: 0.075, range: 2, vib: 35, vibRate: 6.3, wobble: 0.35, toneAmt: 0.8, vol: 0.9, cut: 2600 },
};

function norm(name) {
  return String(name || "").normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/đ/gi, "d").toLowerCase().trim();
}
function hash(s) { let h = 5381; for (let i = 0; i < s.length; i++) h = ((h << 5) + h + s.charCodeAt(i)) >>> 0; return h; }
function profileFor(name) {
  const n = norm(name);
  if (/\bsen\b/.test(n)) return PROFILES.sen;
  if (n === "ba tu" || n === "ba" || n === "noi" || n === "ba noi") return PROFILES.ba;
  const h = hash(n || "?");
  return {
    f0: 120 + (h % 181), form: 0.88 + ((h >>> 8) % 30) / 100, dur: 0.064 + ((h >>> 4) % 4) * 0.008,
    every: 2 + ((h >>> 12) & 1), minGap: 0.06, range: 2 + ((h >>> 14) % 2), vib: (h >>> 16) % 3 === 0 ? 20 : 0, vibRate: 5.5,
    wobble: ((h >>> 18) % 3) * 0.1, toneAmt: 0.8, vol: 0.85, cut: 2800 + ((h >>> 20) % 6) * 400,
  };
}

const isLetter = (ch) => /\p{L}/u.test(ch);

export function createVoice(ac, dest) {
  const out = ac.createGain(); out.gain.value = 0.5;
  out.connect(dest);
  // glottal-ish source: harmonics falling ~1/n^1.5 (softer than saw, more voice-like than sine)
  const real = new Float32Array(28), imag = new Float32Array(28);
  for (let n = 1; n < 28; n++) imag[n] = 1 / Math.pow(n, 1.5);
  const wave = ac.createPeriodicWave(real, imag);
  const states = new Map();
  const cache = new Map();

  const prof = (speaker) => { if (!cache.has(speaker)) cache.set(speaker, profileFor(speaker)); return cache.get(speaker); };
  const stateOf = (speaker) => {
    if (!states.has(speaker)) states.set(speaker, { count: 0, every: 2, last: -1, tone: null, vowel: null, loud: false });
    return states.get(speaker);
  };

  function syllable(p, t, o = {}) {
    const dur = p.dur * (o.durMul || 1) * rnd(0.85, 1.15);
    const semis = (o.offset || 0) + rnd(-p.range, p.range) * 0.5 + rnd(-p.wobble, p.wobble);
    const f0 = p.f0 * Math.pow(2, semis / 12);
    const contour = (o.contour || TONES.ngang).map((c) => c * (p.toneAmt ?? 1));
    const osc = ac.createOscillator(); osc.setPeriodicWave(wave);
    const fq = (k) => f0 * Math.pow(2, contour[k] / 12);
    osc.frequency.setValueAtTime(fq(0), t);
    osc.frequency.linearRampToValueAtTime(fq(1), t + dur * 0.45);
    osc.frequency.linearRampToValueAtTime(fq(2), t + dur);
    if (p.vib) {
      const l = ac.createOscillator(); l.frequency.value = p.vibRate * rnd(0.9, 1.1);
      const lg = ac.createGain(); lg.gain.value = p.vib; l.connect(lg); lg.connect(osc.detune);
      l.start(t); l.stop(t + dur + 0.03);
    }
    const [F1, F2] = VOWELS[o.vowel] || VOWELS[pick(VOWEL_KEYS)];
    const env = ac.createGain();
    const vol = p.vol * (o.volMul || 1);
    env.gain.setValueAtTime(0, t);
    env.gain.linearRampToValueAtTime(vol, t + 0.008);
    env.gain.linearRampToValueAtTime(vol * 0.75, t + dur * 0.65);
    env.gain.linearRampToValueAtTime(0, t + dur);
    const b1 = ac.createBiquadFilter(); b1.type = "bandpass"; b1.frequency.value = F1 * p.form; b1.Q.value = 4;
    const b2 = ac.createBiquadFilter(); b2.type = "bandpass"; b2.Q.value = 6;
    b2.frequency.setValueAtTime(F2 * p.form, t);
    b2.frequency.linearRampToValueAtTime(F2 * p.form * rnd(0.88, 1.1), t + dur); // tiny diphthong glide
    const g1 = ac.createGain(); g1.gain.value = 1.4;
    const g2 = ac.createGain(); g2.gain.value = 0.7;
    const body = ac.createBiquadFilter(); body.type = "lowpass"; body.frequency.value = f0 * 2.2;
    const g0 = ac.createGain(); g0.gain.value = 0.35;
    const lp = ac.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = p.cut;
    osc.connect(b1); b1.connect(g1); g1.connect(env);
    osc.connect(b2); b2.connect(g2); g2.connect(env);
    osc.connect(body); body.connect(g0); g0.connect(env);
    env.connect(lp); lp.connect(out);
    osc.start(t); osc.stop(t + dur + 0.03);
  }

  // look ahead to the end of the current sentence: "!" => a bit louder and higher
  function sentenceEnd(text, idx) {
    if (typeof text !== "string" || idx == null) return null;
    for (let k = idx; k < text.length; k++) { const c = text[k]; if (c === "!" || c === "?" || c === ".") return c; }
    return null;
  }

  // process one revealed character at time `when`
  function feedAt(speaker, ch, text, idx, when) {
    if (!ch) return;
    const p = prof(speaker), st = stateOf(speaker);
    if (idx === 0) { st.count = p.every - 1; st.every = p.every; st.tone = null; st.vowel = null; } // new line: speak on 1st letter
    if (ch === "?") {
      if (when - st.last > p.minGap * 0.8) { syllable(p, when, { contour: [0, 2, 6], durMul: 1.5, volMul: 0.85, offset: 1 }); st.last = when; }
      st.count = 0; return;
    }
    if (ch === "!" && text == null) { syllable(p, when, { contour: [1, 0, -1.5], volMul: 1.3, offset: 2 }); st.last = when; st.count = 0; return; }
    if (!isLetter(ch)) { if (/[.,;:…!]/.test(ch)) st.count = 0; return; }
    const d = ch.normalize("NFD");
    for (const c of d) if (MARKS[c]) st.tone = MARKS[c];
    const base = norm(d[0]);
    if (VOWELS[base]) st.vowel = base;
    if (d.includes("\u031B")) st.vowel = "ơ"; // ơ / ư (horn)
    st.count++;
    if (st.count < st.every) return;
    st.count = 0; st.every = p.every + (Math.random() < 0.35 ? 1 : 0);
    if (when - st.last < p.minGap) return;
    st.last = when;
    const loud = sentenceEnd(text, idx) === "!";
    syllable(p, when, {
      contour: TONES[st.tone || (Math.random() < 0.25 ? pick(["sac", "huyen", "ngang"]) : "ngang")],
      vowel: st.vowel && Math.random() < 0.75 ? st.vowel : null,
      volMul: loud ? 1.3 : 1, offset: loud ? 1.5 : 0, durMul: st.tone === "nang" ? 0.7 : 1,
    });
    st.tone = null; st.vowel = null;
  }

  return {
    // call once per revealed character; text/idx are optional context (whole line + char index)
    feed(speaker, ch, text, idx) { feedAt(speaker, ch, text, idx, ac.currentTime + 0.005); },
    // schedule a whole line of babble at typing speed; returns its duration in seconds
    line(speaker, text, cps = 42) {
      const s = String(text || "").slice(0, 110), t0 = ac.currentTime + 0.01;
      const key = speaker + "\u0000line"; // own state so it never collides with a typing dialogue box
      cache.set(key, prof(speaker)); states.delete(key);
      for (let i = 0; i < s.length; i++) feedAt(key, s[i], s, i, t0 + i / cps);
      return s.length / cps;
    },
  };
}
