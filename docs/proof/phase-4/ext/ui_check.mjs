// CDP driver for the Phase 4 extensions (SFX captions + GUI leaderboard): launch Chrome headless, open the GUI with ?debug,
// run scripted checks, print JSON results and save screenshots. Needs node >= 22 (global WebSocket) and google-chrome.
// Usage (from repo root, server running: python3 -m http.server 8099 --bind 127.0.0.1):
//   node docs/proof/phase-4/ext/ui_check.mjs <out-dir> "http://127.0.0.1:8099/client/index.html?debug"
import { spawn } from "node:child_process";
import { writeFileSync } from "node:fs";
const OUT = process.argv[2], URL = process.argv[3];
const chrome = spawn("google-chrome", ["--headless=new", "--remote-debugging-port=9333", "--window-size=1280,720", "--no-first-run", "--user-data-dir=" + OUT + "/prof", "--autoplay-policy=no-user-gesture-required", "about:blank"], { stdio: "ignore" });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let ws, id = 0; const pending = new Map(); const logs = [];
async function connect() {
  for (let i = 0; i < 50; i++) { try { const l = await (await fetch("http://127.0.0.1:9333/json")).json(); const p = l.find((t) => t.type === "page"); if (p) return p.webSocketDebuggerUrl; } catch (e) {} await sleep(200); }
  throw new Error("no chrome");
}
const send = (method, params = {}) => new Promise((res) => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); });
const ev = async (expr) => { const r = await send("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); if (r.result.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails).slice(0, 400)); return r.result.result.value; };
const shot = async (name) => { const r = await send("Page.captureScreenshot", { format: "png" }); writeFileSync(`${OUT}/${name}.png`, Buffer.from(r.result.data, "base64")); };
const key = async (k, code) => { for (const type of ["keyDown", "keyUp"]) await send("Input.dispatchKeyEvent", { type, key: k, code: code || k, text: type === "keyDown" && k.length === 1 ? k : undefined, windowsVirtualKeyCode: k === "Enter" ? 13 : k === "Backspace" ? 8 : k.toUpperCase().charCodeAt(0) }); };
try {
  ws = new WebSocket(await connect());
  await new Promise((r) => ws.addEventListener("open", r));
  ws.addEventListener("message", (m) => { const d = JSON.parse(m.data); if (d.id && pending.has(d.id)) { pending.get(d.id)(d); pending.delete(d.id); } if (d.method === "Runtime.consoleAPICalled" && d.params.type === "error") logs.push(d.params.args.map((a) => a.value || a.description).join(" ")); if (d.method === "Runtime.exceptionThrown") logs.push("EXC " + JSON.stringify(d.params.exceptionDetails.exception?.description || d.params.exceptionDetails.text)); });
  await send("Runtime.enable"); await send("Page.enable");
  await send("Page.navigate", { url: URL });
  for (let i = 0; i < 60 && !(await ev("!!window.__chonoi")); i++) await sleep(250);
  const S = "window.__chonoi";
  const res = {};
  await ev(`localStorage.removeItem("chonoi.lb"); localStorage.removeItem("chonoi.cc"); true`);
  // --- captions: off by default; U turns on; sfx() shows caption; gather warnings ---
  await ev(`${S}.go("gather"); ${S}.step(120); true`);
  await key("u", "KeyU"); await ev(`${S}.step(2); true`);
  res.ccStored = await ev(`localStorage.getItem("chonoi.cc")`);
  const C = await ev(`import("./src/captions.js").then(m => { window.__cc = m; return true; })`);
  const A = await ev(`import("./src/audio.js").then(m => { window.__au = m; return true; })`);
  await ev(`__au.sfx("splash"); __au.sfx("hurt", undefined, "[Cá Sấu cắn]"); __au.sfx("hurt", undefined, "[Cá Sấu cắn]"); __au.sfx("click"); ${S}.step(3); true`);
  res.linesOn = await ev(`__cc.captionLines().map(l => l.text + (l.n > 1 ? " x" + l.n : ""))`);
  await sleep(300); await shot("01-gather-captions");
  // oxygen low cue in the real scene
  await ev(`(() => { const sc = ${S}.state.scene; sc.p.d = 6; sc.started = true; sc.oxy = sc.oxyMax * 0.2; ${S}.step(5); return true; })()`);
  res.afterOxy = await ev(`__cc.captionLines().map(l => l.text)`);
  await sleep(200); await shot("02-gather-low-oxygen");
  // high contrast + captions
  await key("h", "KeyH"); await ev(`${S}.step(3); true`); await sleep(200); await shot("03-gather-hc-captions");
  await key("h", "KeyH"); await ev(`${S}.step(2); true`);
  // turn captions off, mute -> auto-on
  await key("u", "KeyU"); await ev(`${S}.step(2); __au.sfx("coin"); true`);
  res.offLines = await ev(`__cc.captionLines().length`);
  await ev(`__au.toggleMute(); __au.sfx("coin"); true`);
  res.mutedLines = await ev(`__cc.captionLines().map(l => l.text)`);
  res.mutedLabel = await ev(`__cc.ccLabel()`);
  await ev(`__au.toggleMute(); true`);
  // quán: angry customer cue
  await ev(`${S}.go("quan"); ${S}.step(90); true`);
  await key("u", "KeyU"); await ev(`${S}.step(2); true`);
  for (let i = 0; i < 40; i++) { const n = await ev(`(${S}.state.scene.customers||[]).filter(c => c.state === "waiting").length`); if (n) break; await ev(`${S}.step(120); true`); }
  res.quanAngry = await ev(`(() => { const sc = ${S}.state.scene; const cu = sc.customers.find(c => c.state === "waiting"); if (!cu) return "no waiting customer (phase " + sc.phase + ")"; cu.patience = cu.patienceMax * 0.2; ${S}.step(3); return __cc.captionLines().map(l => l.text); })()`);
  await sleep(200); await shot("04-quan-angry-caption");
  // --- leaderboard: summary → name → board ---
  await ev(`${S}.go("summary"); ${S}.step(80); true`);
  await sleep(200); await shot("05-summary");
  await key("Enter", "Enter"); await ev(`${S}.step(70); true`); // stats → name (t > 1)
  res.phase1 = await ev(`${S}.state.scene.phase`);
  for (const ch of "Tester") await key(ch, "Key" + ch.toUpperCase());
  await key("t", "KeyT"); await key("Backspace", "Backspace"); await key("h", "KeyH"); await key("Backspace", "Backspace");
  await ev(`${S}.step(5); true`);
  res.typed = await ev(`${S}.state.scene.name`);
  res.hcAfterTyping = await ev(`localStorage.getItem("chonoi.hc")`);
  res.overlay = await ev(`!!${S}.state.overlay`);
  await sleep(150); await shot("06-name-entry");
  await key("Enter", "Enter"); await ev(`${S}.step(40); true`);
  res.phase2 = await ev(`${S}.state.scene.phase`);
  res.lb = await ev(`localStorage.getItem("chonoi.lb")`);
  await sleep(200); await shot("07-leaderboard");
  res.logs = logs;
  console.log(JSON.stringify(res, null, 1));
} catch (e) { console.log("FAIL", e.message, logs); }
finally { try { ws?.close(); } catch (e) {} chrome.kill(); process.exit(0); }
