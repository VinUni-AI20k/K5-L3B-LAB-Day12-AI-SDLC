"""Đo FPS cảnh chuẩn có render (PRD Phase 4 §1).

    python3 tools/bench.py --seed 42 --duration 30 --out bench.json

Đường chạy (tự chọn):
  1. Playwright (khuyến nghị — nhóm dùng cái này): `pip install playwright && playwright install chromium`
  2. obscura (headless browser có sẵn trên một số máy): `obscura scrape -e`
  3. chrome/chromium trên PATH nếu Playwright không có

Quy trình: dựng `chonoi.live` (cảnh sáng lõi, Út Sen đứng yên ở bến) → mở 1280×720 →
làm nóng 3 s → đo `duration` giây bằng requestAnimationFrame trong trang → ghi 5 trường.

Mã thoát: 0 OK · 2 không có trình duyệt / tham số sai · 1 lỗi chạy.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time

ROOT = __import__("os").path.dirname(__import__("os").path.dirname(__import__("os").path.abspath(__file__)))
WARMUP_S = 3.0

MEASURE_JS = r"""
(async () => {
  const warmup = __WARMUP_MS__, measure = __MEASURE_MS__;
  const start = performance.now();
  const deltas = [];
  let last = null, warmDone = false, t0 = 0;
  await new Promise((resolve) => {
    function tick(ts) {
      if (last === null) last = ts;
      if (!warmDone) {
        if (ts - start >= warmup) { warmDone = true; t0 = ts; last = ts; }
      } else {
        deltas.push(ts - last);
        last = ts;
        if (ts - t0 >= measure) { resolve(); return; }
      }
      requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  });
  const measured = deltas.reduce((a, b) => a + b, 0) / 1000;
  const n = Math.max(1, Math.ceil(0.01 * deltas.length));
  const worst = deltas.slice().sort((a, b) => b - a).slice(0, n);
  const worstAvg = worst.reduce((a, b) => a + b, 0) / worst.length / 1000;
  return {
    frames: deltas.length,
    measured_s: measured,
    avg_fps: deltas.length / measured,
    p1_low_fps: 1 / worstAvg,
    width: innerWidth,
    height: innerHeight,
  };
})()
"""


def measure_js(duration_s):
    return MEASURE_JS.replace("__WARMUP_MS__", str(int(WARMUP_S * 1000))).replace(
        "__MEASURE_MS__", str(int(duration_s * 1000)))


def start_server(seed):
    proc = subprocess.Popen(
        [sys.executable, "-m", "chonoi.live", "--mode", "gather", "--seed", str(seed),
         "--host", "127.0.0.1", "--port", "0"],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    deadline = time.time() + 20
    while time.time() < deadline:
        line = proc.stdout.readline()
        if not line:
            break
        m = re.search(r"(http://127\.0\.0\.1:\d+/)", line)
        if m:
            return proc, m.group(1)
    proc.kill()
    raise RuntimeError("không đọc được địa chỉ server từ chonoi.live")


def via_playwright(url, duration_s, timeout_s):
    from playwright.sync_api import sync_playwright  # noqa: PLC0415 - import muộn có chủ đích

    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=["--headless=new"])
        page = browser.new_page(viewport={"width": 1280, "height": 720})
        page.goto(url, wait_until="load", timeout=timeout_s * 1000)
        result = page.evaluate(measure_js(duration_s))
        browser.close()
    return result


def via_obscura(binary, url, duration_s, timeout_s):
    p = subprocess.run(
        [binary, "scrape", "--allow-private-network", "--timeout", str(timeout_s),
         "-e", measure_js(duration_s), url],
        cwd=ROOT, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"obscura lỗi {p.returncode}: {p.stderr.strip()[:300]}")
    return json.loads(p.stdout[p.stdout.find("{"):])["results"][0]["eval"]


def pick_runner():
    try:
        import playwright  # noqa: F401,PLC0415
        return "playwright", None
    except ImportError:
        pass
    for name in ("obscura", "chromium", "chromium-browser", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return name, path
    return None, None


def main(argv=None):
    ap = argparse.ArgumentParser(prog="bench")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--duration", type=int, default=30)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    if a.duration <= 0:
        sys.stderr.write("--duration phải > 0\n")
        return 2

    runner, path = pick_runner()
    if runner is None:
        sys.stderr.write(
            "không có trình duyệt. Cài Playwright: pip install playwright && playwright install chromium\n"
            "(hoặc đặt một binary chromium/chrome trên PATH, hoặc dùng obscura)\n")
        return 2

    t0 = time.perf_counter()
    server = None
    try:
        server, url = start_server(a.seed)
        timeout_s = int(WARMUP_S + a.duration + 90)
        if runner == "playwright":
            result = via_playwright(url, a.duration, timeout_s)
        elif runner == "obscura":
            result = via_obscura(path, url, a.duration, timeout_s)
        else:  # chrome/chromium: chưa hỗ trợ CDP trực tiếp
            sys.stderr.write(f"{runner} cần Playwright để đo; cài: pip install playwright\n")
            return 2
    except Exception as e:  # noqa: BLE001 - báo lỗi chạy, không nuốt
        sys.stderr.write(f"bench lỗi: {e}\n")
        return 1
    finally:
        if server is not None:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()
        wall_s = time.perf_counter() - t0

    frames = int(result.get("frames", 0))
    measured = float(result.get("measured_s", 0))
    if frames < 2 or measured <= 0:
        sys.stderr.write(f"đo không hợp lệ: {result}\n")
        return 1

    out = {
        "avg_fps": round(frames / measured, 3),
        "p1_low_fps": round(float(result["p1_low_fps"]), 3),
        "frames": frames,
        "measured_s": round(measured, 3),
        # từ lúc khởi chạy bench (gồm cả dựng server) tới khi hết phần làm nóng
        "load_ms": max(0, int(round(wall_s * 1000 - (WARMUP_S + a.duration) * 1000))),
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write("\n")
    print(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
