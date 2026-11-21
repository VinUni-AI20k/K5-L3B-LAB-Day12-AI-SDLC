"""P2-07: chế độ `day` (Ticket-02 mục 2 và 4), pause và các nút, tham số `--days`, scenario của `day`.

Chạy trong tiến trình qua Session cho từng luật, và qua headless cho phần CLI. Ngày chạy nhanh bằng
time_left_ticks nhỏ: gather 3 tick, quán 5 tick, nên gather_end ở tick 3, quan_end ở tick 8, Shop mở ở tick 8.
Số liệu đọc từ game.contract.json.
"""

import copy
import unittest

from helpers import Workdir, frames, read_jsonl, run_headless, write_json

from chonoi.contract import load_contract
from chonoi.errors import BadInput
from chonoi.inputs import InputPlayer
from chonoi.runner import Session
from chonoi.sim.day import plan_ingredients

T = load_contract()["tuning"]
HZ = T["tick_hz"]
PLAN1 = T["day_plan"][0]
HP1 = T["shop"]["upgrades"]["hp"][0]
OX1 = T["shop"]["upgrades"]["oxygen"][0]
SHOP_MAX = T["shop"]["max_ticks"]

QUICK = {"gather": {"time_left_ticks": 3, "random_fish": False},
         "quan": {"time_left_ticks": 5, "random_customers": False}}
EATING = {"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "eating", "order_status": "served",
          "eat_ticks_left": 100, "base_price": 40, "tip": 8, "reserved": {}}


def scenario(**blocks):
    s = copy.deepcopy(QUICK)
    for name, extra in blocks.items():
        s.setdefault(name, {}).update(extra)
    return s


def play(scn=None, inputs=(), ticks=1000, days=1, seed=1):
    sess = Session("day", T, scn if scn is not None else scenario(), seed, days=days)
    rows = list(sess.start_rows())
    player = InputPlayer(sorted(inputs, key=lambda f: f["tick"]))
    while sess.tick < ticks and not sess.done:
        rows.extend(sess.step(player.advance(sess.tick)))
    return sess, rows


def evs(rows):
    return [(r["tick"], r["phase"], r["day"], r["name"]) for r in rows]


def names(rows, name):
    return [r for r in rows if r["name"] == name]


class Flow(unittest.TestCase):
    def test_start_events_and_first_snapshot(self):
        sess = Session("day", T, scenario(), 1)
        rows = sess.start_rows()
        self.assertEqual(evs(rows), [(0, "gather", 1, "day_start"), (0, "gather", 1, "day_plan"),
                                     (0, "gather", 1, "phase_start")])
        self.assertEqual(rows[1]["data"], {"dishes": PLAN1["dishes"], "ingredients": PLAN1["ingredients"]})
        self.assertEqual([r["data"] for r in (rows[0], rows[2])], [{}, {}])
        s = sess.snapshot()
        self.assertEqual((s["mode"], s["phase"], s["day"], s["state"], s["tick"], s["sim_tick"], s["phase_tick"]),
                         ("day", "gather", 1, "playing", 0, 0, 0))
        self.assertEqual((s["upgrades"], s["active_upgrades"]), ({"oxygen": 0, "hp": 0}, {"oxygen": 0, "hp": 0}))
        self.assertEqual(s["day_plan"], rows[1]["data"])
        self.assertEqual(sess.start_rows(), [])  # chỉ phát một lần

    def test_one_full_day_phase_order_and_same_tick_transitions(self):
        sess, rows = play(inputs=[{"tick": 9, "shop_done": True}])
        self.assertEqual(evs(rows)[3:], [
            (3, "gather", 1, "gather_end"), (3, "quan", 1, "phase_start"),
            (8, "quan", 1, "quan_end"), (8, "shop", 1, "phase_start"),
            (10, "shop", 1, "shop_end")])
        self.assertEqual(names(rows, "shop_end")[0]["data"], {"reason": "done"})
        self.assertTrue(sess.done)
        end = sess.end_row()
        self.assertEqual((end["mode"], end["reason"], end["days_completed"], end["state"]),
                         ("day", "days_complete", 1, "finished"))

    def test_new_phase_starts_gameplay_on_the_next_step(self):
        sess = Session("day", T, scenario(), 1)
        player = InputPlayer([])
        for _ in range(3):
            sess.step(player.advance(sess.tick))
        s = sess.snapshot()
        self.assertEqual((s["phase"], s["phase_tick"], s["sim_tick"], s["tick"]), ("quan", 0, 3, 3))
        sess.step(player.advance(sess.tick))
        self.assertEqual((sess.snapshot()["phase_tick"], sess.snapshot()["sim_tick"]), (1, 4))

    def test_inventory_is_handed_over_in_memory_with_the_v10_schema(self):
        hold = ["ca_loc", "bong_sung", "bong_sung"]
        sess, rows = play(scenario(gather={"hold": hold, "time_left_ticks": 2}), ticks=2)
        end = names(rows, "gather_end")[0]["data"]
        self.assertEqual(end["inventory"], {"items": {"bong_sung": 2, "ca_loc": 1}})
        self.assertEqual(sess.snapshot()["stock"], {"bong_sung": 2, "ca_loc": 1})

    def test_fainted_gather_still_opens_the_shop_floor_with_an_empty_stock(self):
        scn = scenario(gather={"player": {"pos": [20, 5], "hp": 1, "oxygen_ticks": 1}, "hold": ["ca_loc"],
                               "time_left_ticks": 600})
        sess, rows = play(scn, ticks=T["gather"]["choke_interval_ticks"])
        tail = [(r["tick"], r["phase"], r["name"]) for r in rows if r["name"] in ("faint", "gather_end", "phase_start")]
        self.assertEqual(tail[-3:], [(60, "gather", "faint"), (60, "gather", "gather_end"), (60, "quan", "phase_start")])
        self.assertEqual(names(rows, "gather_end")[0]["data"]["reason"], "fainted")
        self.assertEqual(sess.snapshot()["stock"], {})

    def test_shop_closes_by_itself_after_max_ticks(self):
        sess, rows = play(ticks=8 + SHOP_MAX + 5)
        end = names(rows, "shop_end")[0]
        self.assertEqual((end["tick"], end["data"]), (8 + SHOP_MAX, {"reason": "time"}))
        self.assertTrue(sess.done)

    def test_only_planned_dishes_are_offered_even_with_other_ingredients_in_stock(self):
        lau_mam_only = ["ca_linh", "ca_linh", "ca_keo", "keo_neo", "bong_dien_dien"]  # chỉ nấu được lau_mam, ngoài kế hoạch D1
        wait = 2 + T["quan"]["first_customer_tick"] + 2
        scn = {"gather": {"hold": lau_mam_only, "time_left_ticks": 2, "random_fish": False}, "quan": {}}
        _, rows = play(scn, ticks=wait)
        self.assertEqual(names(rows, "customer_arrived"), [])
        self.assertEqual([r["data"] for r in names(rows, "no_dish")], [{}])
        scn["gather"]["hold"] = lau_mam_only + ["ca_loc"]  # thêm nguyên liệu của món trong kế hoạch
        for seed in range(1, 5):
            _, rows = play(scn, ticks=wait, seed=seed)
            self.assertEqual([r["data"]["dish_id"] for r in names(rows, "customer_arrived")], ["ca_loc_nuong_trui"], seed)

    def test_reservation_beyond_the_real_stock_is_rejected_when_the_quan_opens(self):
        scn = scenario(quan={"customers": [{"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung",
                                            "reserved": {"bong_sung": 2}}]})
        with self.assertRaises(BadInput):
            play(scn)
        scn["gather"]["hold"] = ["bong_sung", "bong_sung"]
        play(scn, ticks=4)  # đủ hàng thì mở quán bình thường


class MoneyAndUpgrades(unittest.TestCase):
    def two_days(self, buy="hp", money=300):
        """Chạy đến ĐÚNG lúc Ngày 2 bắt đầu (tick 11): shop_done ở frame 10 đóng Shop, Ngày 2 dựng cùng tick."""
        scn = scenario(quan={"customers": [EATING]})
        scn["day"] = {"money": money, "earned": money}
        return play(scn, inputs=[{"tick": 9, "buy": buy}, {"tick": 10, "shop_done": True}], days=2, ticks=11)

    def test_money_earned_and_reputation_carry_across_phases_and_days(self):
        sess, rows = self.two_days("hp")
        paid = names(rows, "paid")[0]["data"]
        self.assertEqual(paid["amount"], 48)
        bought = names(rows, "bought")[0]
        self.assertEqual(bought["data"], {"upgrade": "hp", "level": 1, "price": HP1["price"],
                                          "money": 300 + 48 - HP1["price"]})
        s = sess.snapshot()
        self.assertEqual((s["money"], s["earned"]), (300 + 48 - HP1["price"], 348))  # mua chỉ trừ money
        self.assertAlmostEqual(s["reputation"], T["quan"]["reputation_initial"] + T["quan"]["tip_reputation"])

    def test_purchase_is_visible_at_once_but_takes_effect_from_the_next_day(self):
        sess = Session("day", T, {**scenario(quan={"customers": [EATING]}), "day": {"money": 300, "earned": 300}}, 1,
                       days=2)
        player = InputPlayer([{"tick": 8, "buy": "oxygen"}])
        while sess.snapshot()["phase"] != "shop":
            sess.step(player.advance(sess.tick))
        sess.step(player.advance(sess.tick))  # bước đầu tiên của Shop đọc frame 8: mua
        s = sess.snapshot()
        self.assertEqual((s["upgrades"]["oxygen"], s["active_upgrades"]["oxygen"]), (1, 0))
        self.assertEqual(sess.sim.current.snapshot()["upgrades"], {"oxygen": 1, "hp": 0})  # snapshot Shop cũng hiện ngay
        player = InputPlayer([{"tick": sess.tick, "shop_done": True}])
        sess.step(player.advance(sess.tick))
        s = sess.snapshot()
        self.assertEqual((s["day"], s["phase"], s["active_upgrades"]["oxygen"]), (2, "gather", 1))
        self.assertEqual(s["player"]["oxygen_max_ticks"], OX1["oxygen_max_s"] * HZ)
        self.assertEqual(s["player"]["oxygen_ticks"], s["player"]["oxygen_max_ticks"])

    def test_hp_upgrade_refills_the_next_day_to_the_new_maximum(self):
        sess, rows = self.two_days("hp")
        end_day1 = names(rows, "shop_end")[0]
        starts = [r for r in rows if r["name"] == "day_start"]
        self.assertEqual([(r["day"], r["tick"]) for r in starts], [(1, 0), (2, end_day1["tick"])])  # cùng tick
        p = sess.snapshot()["player"]
        self.assertEqual((p["hp"], p["hp_max"]), (HP1["hp_max"], HP1["hp_max"]))

    def test_buy_fails_without_funds_and_for_unknown_commands(self):
        scn = scenario()
        scn["day"] = {"money": HP1["price"] - 1, "earned": HP1["price"] - 1}
        sess, rows = play(scn, inputs=[{"tick": 9, "buy": "hp"}, {"tick": 10, "shop_done": True}])
        self.assertEqual(names(rows, "buy_failed")[0]["data"], {"action": "hp", "reason": "funds"})
        self.assertEqual(sess.snapshot()["money"], HP1["price"] - 1)  # tiền và cấp giữ nguyên
        _, rows = play(inputs=[{"tick": 9, "buy": "weapon"}, {"tick": 10, "shop_done": True}])
        self.assertEqual(names(rows, "buy_failed")[0]["data"], {"action": "weapon", "reason": "unknown"})

    def test_buy_runs_only_at_its_own_frame_and_before_shop_done(self):
        scn = scenario()
        scn["day"] = {"money": 1000, "earned": 1000}
        _, rows = play(scn, inputs=[{"tick": 9, "buy": "hp", "shop_done": True}])
        self.assertEqual([(r["tick"], r["name"]) for r in rows if r["phase"] == "shop" and r["name"] != "phase_start"],
                         [(10, "bought"), (10, "shop_end")])
        _, rows = play(scn, inputs=[{"tick": 9, "buy": "hp"}, {"tick": 20, "shop_done": True}])
        self.assertEqual(len(names(rows, "bought")), 1)  # không lặp lại ở các tick sau (không kế thừa)

    def test_day_scenario_sets_the_starting_state(self):
        scn = scenario()
        scn["day"] = {"money": 120, "earned": 200, "reputation": 4.0, "upgrades": {"oxygen": 1, "hp": 2}}
        sess = Session("day", T, scn, 1)
        s = sess.snapshot()
        self.assertEqual((s["money"], s["earned"], s["reputation"]), (120, 200, 4.0))
        self.assertEqual((s["upgrades"], s["active_upgrades"]), ({"oxygen": 1, "hp": 2}, {"oxygen": 1, "hp": 2}))
        self.assertEqual(s["player"]["hp_max"], T["shop"]["upgrades"]["hp"][1]["hp_max"])

    def test_day_plan_override_by_day_number_recomputes_ingredients(self):
        scn = scenario()
        scn["day"] = {"day_plan": [{"dishes": {"lau_mam": 1, "goi_bong_sung": 2}}]}
        sess = Session("day", T, scn, 1)
        plan = sess.snapshot()["day_plan"]
        self.assertEqual(plan["dishes"], {"lau_mam": 1, "goi_bong_sung": 2})
        self.assertEqual(plan["ingredients"], plan_ingredients(T["menu"], plan["dishes"]))
        self.assertEqual(plan["ingredients"]["bong_sung"], 4)

    def test_later_days_follow_the_tuning_plan(self):
        sess, rows = play(inputs=[{"tick": 9, "shop_done": True}, {"tick": 10, "shop_done": False},
                                  {"tick": 26, "shop_done": True}], days=3, ticks=120)
        plans = [r["data"]["dishes"] for r in names(rows, "day_plan")]
        self.assertEqual(plans[:2], [T["day_plan"][0]["dishes"], T["day_plan"][1]["dishes"]])


class PauseAndInputs(unittest.TestCase):
    def pause_frames(self):
        return [{"tick": 5, "pause": True}, {"tick": 6, "pause": False}, {"tick": 7, "interact": True},
                {"tick": 8, "interact": False}, {"tick": 10, "pause": True}, {"tick": 11, "pause": False}]

    def run_session(self, mode, scn):
        sess = Session(mode, T, scn, 1)
        player = InputPlayer(self.pause_frames())
        rows, states = [], []
        for _ in range(12):
            rows.extend(sess.step(player.advance(sess.tick)))
            states.append((sess.tick, sess.sim_ticks, sess.snapshot()["state"]))
        return sess, rows, states

    def check(self, mode, scn):
        sess, rows, states = self.run_session(mode, scn)
        self.assertEqual([(r["tick"], r["name"]) for r in rows], [(6, "paused"), (11, "resumed")])
        self.assertEqual([r["data"] for r in rows], [{}, {}])
        by_tick = {t: (s, st) for t, s, st in states}
        self.assertEqual(by_tick[6], (5, "paused"))   # vào pause: chỉ tick ngoài tăng
        self.assertEqual(by_tick[10], (5, "paused"))  # sim_tick đứng yên suốt lúc pause, cạnh interact bị bỏ qua
        self.assertEqual(by_tick[11], (6, "playing"))  # hết pause: gameplay chạy ngay trong bước đó
        self.assertFalse(sess.done)

    def test_pause_in_standalone_gather(self):
        self.check("gather", {"random_fish": False})  # interact ở tick 7 sẽ cập bến nếu không bị bỏ qua

    def test_pause_in_standalone_quan(self):
        self.check("quan", {"random_customers": False})

    def test_pause_in_day_marks_events_with_phase_and_day(self):
        sess, rows, _ = self.run_session("day", scenario(gather={"time_left_ticks": 600}))
        self.assertEqual([(r["name"], r["phase"], r["day"]) for r in rows], [("paused", "gather", 1), ("resumed", "gather", 1)])

    def test_pause_freezes_the_shop_timer(self):
        sess = Session("day", T, scenario(), 1)
        player = InputPlayer([{"tick": 8, "pause": True}, {"tick": 9, "pause": False}, {"tick": 13, "pause": True}])
        while sess.tick < 8:
            sess.step(player.advance(sess.tick))
        self.assertEqual((sess.snapshot()["phase"], sess.snapshot()["time_left_ticks"]), ("shop", SHOP_MAX))
        for _ in range(5):  # k = 8 vào pause, k = 9..12 vẫn pause
            sess.step(player.advance(sess.tick))
        self.assertEqual((sess.snapshot()["state"], sess.snapshot()["time_left_ticks"]), ("paused", SHOP_MAX))
        sess.step(player.advance(sess.tick))  # k = 13: hết pause, Shop chạy ngay trong bước đó
        self.assertEqual((sess.snapshot()["state"], sess.snapshot()["time_left_ticks"]), ("playing", SHOP_MAX - 1))

    def test_attack_and_photo_stay_unsupported_without_the_extensions(self):
        with Workdir() as w:
            for button in ("attack", "photo"):
                inp = write_json(w.path("i.json"), frames({"tick": 0, button: True}))
                code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "1", "--inputs", inp,
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, button)

    def test_buy_must_be_a_non_empty_string_and_is_ignored_outside_the_shop(self):
        with Workdir() as w:
            for bad in ("", 5, ["hp"], None):
                inp = write_json(w.path("i.json"), frames({"tick": 0, "buy": bad}))
                code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "1", "--inputs", inp,
                                       "--out", w.path("o.jsonl"))
                self.assertEqual(code, 2, repr(bad))
            ok = write_json(w.path("ok.json"), frames({"tick": 0, "buy": "hp"}))
            self.assertEqual(run_headless("--mode", "gather", "--seed", "1", "--ticks", "2", "--inputs", ok,
                                          "--out", w.path("g.jsonl"))[0], 0)


class Cli(unittest.TestCase):
    def test_headless_day_writes_day_envelope_and_end_row(self):
        with Workdir() as w:
            scn = write_json(w.path("s.json"), {"gather": QUICK["gather"], "quan": QUICK["quan"]})
            inp = write_json(w.path("i.json"), frames({"tick": 9, "shop_done": True}))
            code, err = run_headless("--mode", "day", "--days", "1", "--seed", "4", "--ticks", "50",
                                     "--scenario", scn, "--inputs", inp, "--out", w.path("o.jsonl"),
                                     "--snapshot-every", "1")
            self.assertEqual(code, 0, err)
            rows = read_jsonl(w.path("o.jsonl"))
        self.assertEqual(rows[0]["type"], "snapshot")
        self.assertEqual([(r["tick"], r["name"]) for r in rows[1:4]], [(0, "day_start"), (0, "day_plan"), (0, "phase_start")])
        self.assertTrue(all("day" in r for r in rows if r["type"] == "event"))
        self.assertTrue(all("day" in r and "active_upgrades" in r for r in rows if r["type"] == "snapshot"))
        end = rows[-1]
        self.assertEqual((end["type"], end["reason"], end["days_completed"], end["ticks"]), ("end", "days_complete", 1, 10))

    def test_tick_limit_before_the_days_finish(self):
        with Workdir() as w:
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "30", "--out", w.path("o.jsonl"))
            end = read_jsonl(w.path("o.jsonl"))[-1]
        self.assertEqual(code, 0)
        self.assertEqual((end["reason"], end["days_completed"], end["state"]), ("tick_limit", 0, "playing"))

    def test_days_flag_rules(self):
        with Workdir() as w:
            base = ("--seed", "1", "--ticks", "1", "--out", w.path("o.jsonl"))
            for args in (("--mode", "day", "--days", "0"), ("--mode", "day", "--days", "6"),
                         ("--mode", "gather", "--days", "2"), ("--mode", "quan", "--days", "1")):
                self.assertEqual(run_headless(*args, *base)[0], 2, args)
            self.assertEqual(run_headless("--mode", "day", "--days", "5", *base)[0], 0)
            kho = write_json(w.path("kho.json"), {"items": {}})
            self.assertEqual(run_headless("--mode", "day", *base, "--inventory", kho)[0], 2)
            self.assertEqual(run_headless("--mode", "day", *base, "--inventory-out", w.path("k.json"))[0], 2)

    def test_day_scenario_contradictions_exit_2(self):
        bad = {
            "quan.stock": {"quan": {"stock": {"ca_loc": 1}}},
            "quan.reputation": {"quan": {"reputation": 3}},
            "money không có earned": {"day": {"money": 10}},
            "money lớn hơn earned": {"day": {"money": 10, "earned": 5}},
            "reputation ngoài miền": {"day": {"money": 0, "earned": 0, "reputation": 9}},
            "cấp quá lớn": {"day": {"upgrades": {"hp": 9}}},
            "ingredients sai": {"day": {"day_plan": [{"dishes": {"goi_bong_sung": 1}, "ingredients": {"bong_sung": 9}}]}},
            "món lạ trong kế hoạch": {"day": {"day_plan": [{"dishes": {"pho_bo": 1}}]}},
            "trường lạ": {"day": {"bonus": 1}},
            "khối lạ": {"night": {}},
            "gather sai": {"gather": {"time_left_ticks": 0}},
        }
        with Workdir() as w:
            for name, scn in bad.items():
                path = write_json(w.path("s.json"), scn)
                code, err = run_headless("--mode", "day", "--seed", "1", "--ticks", "1", "--scenario", path,
                                         "--out", w.path(f"o-{len(name)}.jsonl"))
                self.assertEqual(code, 2, f"{name}: {err}")

    def test_reservation_beyond_real_stock_exits_2_when_the_quan_opens(self):
        scn = {"gather": QUICK["gather"], "quan": {"time_left_ticks": 5, "random_customers": False, "customers": [
            {"id": "K1", "table_id": "T1", "dish_id": "goi_bong_sung", "reserved": {"bong_sung": 2}}]}}
        with Workdir() as w:
            path = write_json(w.path("s.json"), scn)
            code, _ = run_headless("--mode", "day", "--seed", "1", "--ticks", "20", "--scenario", path,
                                   "--out", w.path("o.jsonl"))
        self.assertEqual(code, 2)

    def test_day_is_deterministic_to_the_byte(self):
        outs = []
        with Workdir() as w:
            inp = write_json(w.path("i.json"), frames({"tick": 0, "move": [1, 1]}, {"tick": 9, "shop_done": True},
                                                      {"tick": 40, "move": [0, 0]}))
            for k in (1, 2):
                code, err = run_headless("--mode", "day", "--days", "2", "--seed", "9", "--ticks", "600",
                                         "--inputs", inp, "--out", w.path(f"o{k}.jsonl"), "--snapshot-every", "7")
                self.assertEqual(code, 0, err)
                with open(w.path(f"o{k}.jsonl"), "rb") as f:
                    outs.append(f.read())
        self.assertEqual(outs[0], outs[1])


if __name__ == "__main__":
    unittest.main()
