// Vẽ HUD của chonoi/web/index.html bằng canvas giả (Node, không cần trình duyệt), ghi lại mọi fillText.
// Dùng bởi tools/hud_check.py. In JSON: {state: {width: {error, texts: [{s,x0,x1,y0,y1}]}}}.
//   node tools/hud_harness.js <client.js> <contract.json> <name>=<snapshot.json> [...]
// Bề rộng chữ ước lượng = số ký tự × cỡ chữ × 0.56 (đủ để phát hiện chữ đè / tràn màn hình).
"use strict";
const fs = require("fs");
const [, , jsPath, contractPath, ...pairs] = process.argv;
const tuning = JSON.parse(fs.readFileSync(contractPath, "utf8")).tuning;
let texts = [], font = "12px sans";
const width = (s, size) => [...String(s)].length * size * 0.56;
const ctx = new Proxy({}, {
  get(t, k) {
    if (k === "fillText") return (s, x, y) => {
      const size = +(/(\d+)px/.exec(font) || [0, 12])[1], w = width(s, size);
      const x0 = t.textAlign === "right" ? x - w : t.textAlign === "center" ? x - w / 2 : x;
      texts.push({ s: String(s), x0, x1: x0 + w, y0: y - size, y1: y });
    };
    if (k === "measureText") return (s) => ({ width: width(s, +(/(\d+)px/.exec(font) || [0, 12])[1]) });
    if (k === "createLinearGradient" || k === "createRadialGradient") return () => ({ addColorStop() {} });
    if (k === "font") return font;
    if (k in t) return t[k];
    return () => {};
  },
  set(t, k, v) { if (k === "font") font = v; t[k] = v; return true; },
});
global.document = { getElementById: () => ({ getContext: () => ctx, width: 0, height: 0, style: {} }) };
global.addEventListener = () => {}; global.fetch = () => new Promise(() => {}); global.setTimeout = () => {};
global.requestAnimationFrame = () => {}; global.devicePixelRatio = 1; global.innerWidth = 1280; global.innerHeight = 720;
let src = fs.readFileSync(jsPath, "utf8").replace(/\nframe\(\);?\s*$/m, "\n");
src += "\nglobalThis.__set = (s) => { snap = s; }; globalThis.__draw = { gather: drawGather, quan: drawQuan };";
eval(src);
const out = {};
for (const pair of pairs) {
  const i = pair.indexOf("="), name = pair.slice(0, i);
  const snap = JSON.parse(fs.readFileSync(pair.slice(i + 1), "utf8"));
  snap.meta = tuning[snap.mode];
  out[name] = {};
  for (const W of [1280, 900, 700, 480]) {
    texts = []; __set(snap);
    let error = null;
    try { __draw[snap.mode](W, 720); } catch (e) { error = String(e && e.message || e); }
    out[name][W] = { error, texts };
  }
}
process.stdout.write(JSON.stringify(out));
