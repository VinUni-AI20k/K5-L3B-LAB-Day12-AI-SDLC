// Splash video before the title screen (assets/video/intro.mp4, 10 s, 1280×720 with sound).
// Browsers block autoplay with sound until the player interacts: if that happens the video plays muted with a
// "bật tiếng" hint and the first press unmutes; after that any key / click / "Bỏ qua" skips. Ends with a fade.
// Skipped automatically with ?debug or ?novideo (tests) and when the file can't be played.
export function playIntroVideo({ src = "assets/video/intro.mp4", onGesture = null } = {}) {
  if (/[?&](debug|novideo)\b/.test(location.search)) return Promise.resolve();
  const stage = document.getElementById("stage") || document.body;
  return new Promise((resolve) => {
    const wrap = document.createElement("div");
    wrap.style.cssText = "position:absolute;inset:0;z-index:20;background:#000;display:flex;align-items:center;justify-content:center;transition:opacity .7s ease;opacity:1;cursor:pointer";
    const v = document.createElement("video");
    v.src = src; v.playsInline = true; v.preload = "auto";
    v.style.cssText = "width:100%;height:100%;object-fit:contain;background:#000";
    const hint = document.createElement("div");
    hint.style.cssText = "position:absolute;left:50%;bottom:4%;transform:translateX(-50%);font:800 15px 'Trebuchet MS',system-ui,sans-serif;color:#fff;background:rgba(10,6,20,.55);border:1px solid rgba(255,210,63,.6);padding:7px 14px;border-radius:999px;text-shadow:0 1px 3px #000;white-space:nowrap;pointer-events:none";
    const skip = document.createElement("button");
    skip.textContent = "Bỏ qua ▸▸";
    skip.style.cssText = "position:absolute;right:2.5%;top:3%;font:800 14px 'Trebuchet MS',system-ui,sans-serif;color:#ffd23f;background:rgba(10,6,20,.55);border:1px solid rgba(255,210,63,.6);padding:6px 12px;border-radius:999px;cursor:pointer";
    wrap.append(v, hint, skip); stage.appendChild(wrap);

    let finished = false, mutedStart = false;
    const setHint = () => { hint.textContent = mutedStart && v.muted ? "🔇 Nhấn phím bất kỳ để bật tiếng · nhấn lần nữa để bỏ qua" : "Nhấn phím bất kỳ để bỏ qua"; };
    const finish = () => {
      if (finished) return; finished = true;
      removeEventListener("keydown", onKey, true); wrap.removeEventListener("pointerdown", onPointer);
      wrap.style.opacity = "0";
      try { v.pause(); } catch (e) {}
      setTimeout(() => { wrap.remove(); resolve(); }, 720);
    };
    const press = () => { try { onGesture?.(); } catch (e) {} if (mutedStart && v.muted) { v.muted = false; setHint(); return; } finish(); };
    const onKey = (e) => { e.preventDefault(); e.stopPropagation(); press(); };
    const onPointer = (e) => { e.preventDefault(); if (e.target === skip) finish(); else press(); };
    addEventListener("keydown", onKey, true); wrap.addEventListener("pointerdown", onPointer);
    v.addEventListener("ended", finish);
    v.addEventListener("error", finish);
    setTimeout(() => { if (!finished && v.readyState < 2) finish(); }, 6000); // never hang on a broken/slow file

    v.play().then(setHint).catch(() => {
      mutedStart = true; v.muted = true;
      v.play().then(setHint).catch(finish);
    });
    setHint();
  });
}
