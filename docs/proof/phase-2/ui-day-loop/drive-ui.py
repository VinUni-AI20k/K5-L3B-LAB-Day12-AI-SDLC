import sys, os, re, subprocess, time, json
sys.path.insert(0, os.path.join(os.environ["TEMP"], "pw"))
from playwright.sync_api import sync_playwright
ROOT = r"e:\vin\K5-L3B-LAB-Day12-AI-SDLC-MMMMV"
OUT = os.path.join(os.environ["TEMP"], "cv")
proc = subprocess.Popen([sys.executable, "-m", "chonoi.live", "--mode", "day", "--days", "2", "--seed", "3",
    "--port", "0", "--scenario", os.path.join(OUT, "sc.json")], cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
url = None
for _ in range(50):
    line = proc.stdout.readline()
    m = re.search(r"(http://127\.0\.0\.1:\d+/)", line)
    if m: url = m.group(1); break
print("url", url)
errs = []
def st(page):
    return page.evaluate("fetch('/state').then(r=>r.json()).then(s=>({phase:s.phase,state:s.state,tick:s.sim_tick,pt:s.phase_tick,day:s.day,money:s.money,up:s.upgrades,act:s.active_upgrades,tl:s.time_left_ticks,fin:s.finished,ev:(s.events||[]).slice(-4).map(e=>e.name)}))")
def shot(page, name): page.screenshot(path=os.path.join(OUT, name + ".png"))
try:
  with sync_playwright() as pw:
    b = pw.chromium.launch(channel="chrome", args=["--headless=new"])
    page = b.new_page(viewport={"width": 1280, "height": 720})
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    page.goto(url); time.sleep(1.2)
    shot(page, "1-menu"); print("menu", st(page))
    page.keyboard.press("Enter"); time.sleep(1.0)
    shot(page, "2-intro"); print("intro", st(page))
    time.sleep(4.3)
    print("after-intro", st(page)); shot(page, "3-gather")
    page.keyboard.press("Escape"); time.sleep(0.6)
    s1 = st(page); shot(page, "4-pause"); time.sleep(1.0); s2 = st(page)
    print("paused", s1["state"], "frozen:", s1["tick"] == s2["tick"] and s1["tl"] == s2["tl"])
    page.keyboard.press("Escape"); time.sleep(1.0)
    s3 = st(page); print("resumed", s3["state"], s3["tick"] > s2["tick"])
    # đợi sang quán
    for _ in range(60):
        s = st(page)
        if s["phase"] != "gather": break
        time.sleep(0.5)
    print("phase now", s["phase"]); time.sleep(0.8)
    shot(page, "5-evening-intro")
    page.keyboard.press("x"); time.sleep(0.5); shot(page, "6-quan")
    for _ in range(60):
        s = st(page)
        if s["phase"] == "shop": break
        time.sleep(0.5)
    time.sleep(0.5); shot(page, "7-shop")
    page.keyboard.press("1"); time.sleep(0.4); page.keyboard.press("1"); time.sleep(0.4)
    page.keyboard.press("3"); time.sleep(0.4)
    s = st(page); print("shop after buys", s); shot(page, "8-shop-bought")
    page.keyboard.press("Escape"); time.sleep(0.5); s1 = st(page); time.sleep(1); s2 = st(page)
    print("shop pause frozen", s1["state"], s1["tl"] == s2["tl"]); shot(page, "9-shop-pause")
    page.keyboard.press("Escape"); time.sleep(0.5)
    page.keyboard.press("Enter"); time.sleep(0.8)
    s = st(page); print("after shop_done", s); shot(page, "10-day2")
    print("ERRORS", errs)
    b.close()
finally:
    proc.kill()
