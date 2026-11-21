"""Kiểm tra HUD kho và sprite Quán trong Chrome trên localhost."""
import json
import sys
from pathlib import Path

from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from chonoi.contract import load_contract
from chonoi.live import LiveGame, LiveServer


def close_live_page(page, url):
    # Let the current poll finish before closing the connection.
    with page.expect_response(lambda res: res.url == url + "state" and res.status == 204):
        page.route(url + "state", lambda route: route.fulfill(status=204))
    page.close()


def observe_motion(page, filename):
    page.add_init_script("""(filename => {
        window.motionFrames = new Set();
        const drawImage = CanvasRenderingContext2D.prototype.drawImage;
        CanvasRenderingContext2D.prototype.drawImage = function (image, ...args) {
            if (image.src?.endsWith("/" + filename) && args.length === 8) {
                const [x, y, width, height] = args;
                const facing = Math.sign(this.getTransform().a);
                const [row, column] = [y / height, x / width];
                window.motionPose = {row, column, facing};
                window.motionFrames.add([row, column, facing].join(":"));
            }
            return drawImage.call(this, image, ...args);
        };
    })(""" + json.dumps(filename) + ")")


def verify_controls(page, url, itemized):
    observe_motion(page, "ba-ut-nhip-boi.webp")
    page.goto(url)
    expect(page.locator("#hint")).to_contain_text("Cập bến")
    if itemized:
        expect(page.locator("#hold-summary").get_by_role("listitem")).to_contain_text("I14")
        expect(page.locator("#hold-summary").get_by_text("Ươn", exact=True)).to_be_visible()
    for key, field, value in (
        ("d", "move", [1, 0]), ("a", "move", [-1, 0]), ("s", "move", [0, 1]), ("w", "move", [0, -1]),
        ("Space", "catch", True), ("e", "interact", True),
    ):
        with page.expect_response(lambda res: res.url == url + "input" and res.ok
                                  and res.request.post_data_json[field] == value):
            page.keyboard.press(key)
    expect(page.locator("#overlay")).to_be_visible()
    with page.expect_response(lambda res: res.url == url + "restart" and res.ok):
        page.keyboard.press("r")
    expect(page.locator("#overlay")).to_be_hidden()
    print("Gather localhost: di chuyển, Space, E cập bến và R chơi lại PASS")
    page.wait_for_function("canPlay()")
    page.keyboard.down("s")
    page.wait_for_function("window.motionFrames.size >= 3", timeout=4000)
    assert page.request.get(url + "state").json()["player"]["at_surface"] is False
    page.keyboard.up("s")
    page.wait_for_function("window.motionPose.row === 0 && window.motionPose.column === 0")
    for key, facing in (("d", -1), ("a", 1)):
        page.keyboard.down(key)
        page.wait_for_function("""facing => window.motionPose.facing === facing
            && (window.motionPose.row > 0 || window.motionPose.column > 0)""", arg=facing)
        page.keyboard.up(key)
    print("Gather localhost: lặn, đổi khung bơi, về dáng lướt và quay trái/phải PASS")


def verify_live_quan(browser, tuning):
    items = [{"id": "I7", "kind": "ca_loc", "fresh": 95}, {"id": "I8", "kind": "ca_linh", "fresh": 28}]
    server = LiveServer(LiveGame("quan", tuning, {}, 1, inventory=items), port=0)
    server.start()
    try:
        page = browser.new_page()
        observe_motion(page, "ba-ut-di-bo.webp")
        page.goto(server.url)
        stock = page.locator("#stock")
        expect(stock.get_by_role("listitem")).to_have_count(2)
        expect(stock.get_by_role("listitem").filter(has_text="Ươn")).to_contain_text("I8")
        expect(stock.get_by_role("listitem").filter(has_text="Đã giữ")).to_contain_text("I7")
        verify_walking(page, server.url, tuning["quan"]["bounds"]["x"][1])
        close_live_page(page, server.url)
        print("Quán localhost: đọc kho cá thể và hàng ươn từ /state PASS")
    finally:
        server.stop()


def verify_walking(page, url, right_edge):
    page.wait_for_function("window.motionPose?.row === 0 && window.motionPose.column === 0", timeout=4000)
    page.keyboard.down("d")
    page.wait_for_function("""[...window.motionFrames].filter(key =>
        key.startsWith("2:") && key.endsWith(":1") && key !== "2:0:1").length >= 2""")
    page.wait_for_function("window.motionPose.row === 2 && window.motionPose.column === 0")
    assert page.request.get(url + "state").json()["player"]["pos"][0] == right_edge
    page.keyboard.up("d")
    for key, row, facing in (("a", 2, -1), ("w", 1, 1), ("s", 0, 1)):
        page.keyboard.down(key)
        page.wait_for_function("""([row, facing]) => window.motionPose.row === row
            && window.motionPose.facing === facing && window.motionPose.column > 0""", arg=[row, facing])
        page.keyboard.up(key)
        page.wait_for_function("""([row, facing]) => window.motionPose.row === row
            && window.motionPose.facing === facing && window.motionPose.column === 0""", arg=[row, facing])
    page.emulate_media(reduced_motion="reduce")
    page.evaluate("window.motionFrames.clear()")
    page.keyboard.down("a")
    page.wait_for_function("""window.motionPose.row === 2 && window.motionPose.facing === -1
        && window.motionPose.column === 0""")
    page.keyboard.up("a")
    assert page.evaluate("""[...window.motionFrames].every(key => key.split(":")[1] === "0")""")
    print("Quán localhost: bốn hướng, nhiều khung bước, dừng khi thả phím hoặc chạm mép PASS")


def verify(page, url, tuning, evidence):
    items = [
        {"id": "I2", "kind": "ca_linh", "fresh": 30},
        {"id": "I9", "kind": "ca_linh", "fresh": 29.99},
        {"id": "I10", "kind": "bong_sung", "fresh": 97.5},
    ]
    gather = dict(json.loads(LiveGame("gather", tuning, {}, 1).state_json()),
                  hold=items, hold_capacity=12)
    quan = dict(json.loads(LiveGame("quan", tuning, {}, 1).state_json()), stock=items,
                customers=[{"id": "C1", "table_id": "T1", "state": "waiting", "order_status": "reserved",
                            "dish_id": "goi_bong_sung", "reserved": ["I10"], "patience_ticks_left": 900}])
    state = gather
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script("""(() => {
        window.quanSprites = {};
        const drawImage = CanvasRenderingContext2D.prototype.drawImage;
        CanvasRenderingContext2D.prototype.drawImage = function (image, ...args) {
            const name = image.src?.split("/").pop();
            if (name?.startsWith("bep-") || name?.startsWith("ban-")) {
                const { e, f } = this.getTransform();
                window.quanSprites[name.slice(0, -5)] = [e / this.canvas.width, f / this.canvas.height];
            }
            return drawImage.call(this, image, ...args);
        };
    })()""")
    page.route("**/state", lambda route: route.fulfill(json=state))
    page.goto(url, wait_until="domcontentloaded")

    def check_items(panel):
        rows = panel.get_by_role("listitem")
        expect(rows).to_have_count(3)
        for row, (identifier, fresh) in zip(rows.all(), (("I2", "30%"), ("I9", "29,99%"), ("I10", "97,5%"))):
            expect(row).to_contain_text(identifier)
            expect(row).to_contain_text(fresh)
        expect(rows.filter(has_text="Ươn")).to_have_count(1)
        expect(rows.filter(has_text="Ươn")).to_contain_text("I9")
        assert page.evaluate("document.documentElement.scrollWidth === innerWidth")

    check_items(page.locator("#hold-summary"))
    expect(page.locator("#hold-title")).to_have_text("Giỏ · 3/12")
    if evidence:
        page.screenshot(path=evidence / "p3-05-gather.png", full_page=True)
    state = dict(gather, hold=[])
    expect(page.locator("#hold-summary")).to_have_text("Giỏ trống")
    state = gather
    check_items(page.locator("#hold-summary"))

    state = quan
    stock = page.locator("#stock")
    check_items(stock)
    expect(stock.get_by_text("Đã giữ", exact=True)).to_have_count(1)
    expect(stock.get_by_role("listitem").filter(has_text="Đã giữ")).to_contain_text("I10")
    sprites = ["bep-mot", "bep-hai", "ban-mot", "ban-hai", "ban-ba", "ban-bon"]
    page.wait_for_function("names => names.every(name => name in window.quanSprites)", arg=sprites, timeout=3000)
    before = page.evaluate("window.quanSprites")
    if evidence:
        page.screenshot(path=evidence / "p3-05-quan-sprites.png", full_page=True, animations="disabled")

    state = dict(quan,
                 stoves=[dict(stove, pos=[6, 8]) if stove["id"] == "B2" else stove for stove in quan["stoves"]],
                 tables=[dict(table, pos=[9, 5]) if table["id"] == "T3" else table for table in quan["tables"]])
    page.wait_for_function("""before => window.quanSprites["bep-hai"][0] > before["bep-hai"][0]
                            && window.quanSprites["ban-ba"][1] > before["ban-ba"][1]""", arg=before)
    after = page.evaluate("window.quanSprites")
    for sprite in ("bep-mot", "ban-mot", "ban-hai", "ban-bon"):
        assert after[sprite] == before[sprite], (sprite, before[sprite], after[sprite])

    state = dict(mode="day", screen="evening_intro", day=1, days=1, inventory=items,
                 spoil_threshold=30, cookable=[])
    check_items(page.locator("#flow-content"))

    state = dict(quan, stock=[])
    expect(stock.get_by_text("Kho trống.", exact=True)).to_be_visible()
    assert not errors, errors


def main():
    evidence = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if evidence:
        evidence.mkdir(parents=True, exist_ok=True)
    tuning = load_contract()["tuning"]
    itemized = "inventory" in tuning
    scenario = {"hold": [{"id": "I14", "kind": "ca_loc", "fresh": 28}]} if itemized else {}
    server = LiveServer(LiveGame("gather", tuning, scenario, 1), port=0)
    server.start()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="chrome")
            page = browser.new_page()
            verify_controls(page, server.url, itemized)
            close_live_page(page, server.url)
            if itemized:
                verify_live_quan(browser, tuning)
            for width in (1440, 1024, 768, 390):
                page = browser.new_page(viewport={"width": width, "height": 900})
                verify(page, server.url, tuning, evidence if width == 1440 else None)
                page.close()
                print(f"HUD kho và sprite Quán Chrome {width}px: PASS")
    finally:
        server.stop()


if __name__ == "__main__":
    main()
