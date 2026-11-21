// Bench v1.3 (TICKET-04). Loaded ONLY by client/bench.html (never by index.html / main.js).
// URL: bench.html?debug&novideo&seed=42&duration=30[&warmup=3][&t0=<launch epoch ms>]
// Seeds Math.random before the game modules run, opens the morning gather scene (fresh-ness, fish, Cá Sấu,
// default effects; Út Sen idle at the dock), warms up, records requestAnimationFrame timestamps for
// `duration` s, then POSTs {avg_fps, p1_low_fps, frames, measured_s, load_ms} to /bench-result.
const q = new URLSearchParams(location.search);
const SEED = Number(q.get("seed") || 42) >>> 0;
const DURATION = Number(q.get("duration") || 30);
const WARMUP = Number(q.get("warmup") || 3);
const T0 = Number(q.get("t0") || 0); // launch time from the runner (epoch ms); 0 -> navigation start

let s = SEED || 1;
Math.random = function () { // mulberry32: same seed -> same scene
  s = (s + 0x6d2b79f5) >>> 0;
  let t = s;
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
};

function report(obj) {
  const body = JSON.stringify(obj);
  console.log("BENCH_RESULT " + body);
  fetch("/bench-result", { method: "POST", headers: { "Content-Type": "application/json" }, body }).catch(() => {});
}

function nextFrame() { return new Promise((r) => requestAnimationFrame(r)); }

async function run() {
  const deadline = performance.now() + 60000;
  while (!window.__chonoi) {
    if (performance.now() > deadline) return report({ error: "game did not boot (window.__chonoi missing)" });
    await new Promise((r) => setTimeout(r, 20));
  }
  const g = window.__chonoi;
  g.go("gather");
  while (g.state.mode !== "gather") {
    if (performance.now() > deadline) return report({ error: "gather scene never opened" });
    await nextFrame();
  }
  const firstFrame = await nextFrame(); // first frame of the measured scene
  const loadMs = T0 ? Date.now() - T0 : firstFrame; // performance time origin = navigation start
  const warmEnd = firstFrame + WARMUP * 1000;
  let t = firstFrame;
  while (t < warmEnd) t = await nextFrame();
  const start = t;
  const end = start + DURATION * 1000;
  const dts = [];
  let prev = start;
  while (prev < end) {
    const now = await nextFrame();
    dts.push((now - prev) / 1000);
    prev = now;
  }
  const frames = dts.length;
  const measured = (prev - start) / 1000;
  const k = Math.max(1, Math.ceil(0.01 * frames));
  const slow = [...dts].sort((a, b) => b - a).slice(0, k);
  const meanSlow = slow.reduce((a, b) => a + b, 0) / k;
  report({
    avg_fps: +(frames / measured).toFixed(3),
    p1_low_fps: +(1 / meanSlow).toFixed(3),
    frames,
    measured_s: +measured.toFixed(3),
    load_ms: Math.round(loadMs),
  });
}
run().catch((e) => report({ error: String(e && e.stack || e) }));
