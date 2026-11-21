import unittest
from types import SimpleNamespace

from chonoi.sim.quan_service import (
    advance_stoves_and_eating,
    cancel_customer_order,
    compute_score,
    find_interact_target,
    handle_closing,
    handle_finished_eating,
    handle_interact,
)


class MockInput:
    def __init__(self, pressed_keys=None):
        self._pressed = set(pressed_keys or [])

    def pressed(self, key):
        return key in self._pressed


def create_mock_sim(**kwargs):
    tuning = {
        "interact_radius": 1.5,
        "patience_s": 60,
        "eat_s": 10,
        "tip_rate": 0.2,
        "tip_min_patience_ratio": 0.5,
        "tip_reputation": 0.2,
        "left_reputation_delta": -0.5,
        "reputation_min": 0.0,
        "reputation_max": 5.0,
    }
    menu = {
        "ca_loc_nuong_trui": {"recipe": {"ca_loc": 1}, "cook_s": 6, "price": 60},
        "goi_bong_sung": {"recipe": {"bong_sung": 2}, "cook_s": 4, "price": 40},
        "lau_ca_linh_dien_dien": {
            "recipe": {"ca_linh": 3, "bong_dien_dien": 1},
            "cook_s": 10,
            "price": 120,
        },
    }
    sim = SimpleNamespace(
        t=tuning,
        menu=menu,
        pos=[2.0, 8.0],
        stock={"ca_loc": 2, "ca_linh": 5, "bong_dien_dien": 2, "bong_sung": 4},
        hand=None,
        stoves=[{"id": "B1", "pos": [2.0, 8.0], "state": "idle", "dish": None, "cook_ticks_left": 0, "ready_ticks": 0}],
        tables=[{"id": "T1", "pos": [3.0, 8.0]}],
        customers=[],
        money=0,
        earned=0,
        shift_earned=0,
        reputation=3.0,
        time_left_ticks=1000,
        done=False,
        reason=None,
    )
    for k, v in kwargs.items():
        setattr(sim, k, v)
    return sim


class TestQuanService(unittest.TestCase):
    def test_target_priority_distance_stove_table_id(self):
        # 1. Khoảng cách gần nhất
        sim = create_mock_sim(
            pos=[0.0, 0.0],
            stoves=[{"id": "B1", "pos": [1.0, 0.0]}],
            tables=[{"id": "T1", "pos": [0.5, 0.0]}],
        )
        target = find_interact_target(sim)
        self.assertEqual(target["type"], "table")
        self.assertEqual(target["entity"]["id"], "T1")

        # 2. Khoảng cách bằng nhau: ưu tiên bếp trước bàn
        sim = create_mock_sim(
            pos=[0.0, 0.0],
            stoves=[{"id": "B1", "pos": [1.0, 0.0]}],
            tables=[{"id": "T1", "pos": [1.0, 0.0]}],
        )
        target = find_interact_target(sim)
        self.assertEqual(target["type"], "stove")
        self.assertEqual(target["entity"]["id"], "B1")

        # 3. Cùng loại: id nhỏ trước (id_key)
        sim = create_mock_sim(
            pos=[0.0, 0.0],
            stoves=[{"id": "B2", "pos": [1.0, 0.0]}, {"id": "B1", "pos": [1.0, 0.0]}],
            tables=[],
        )
        target = find_interact_target(sim)
        self.assertEqual(target["type"], "stove")
        self.assertEqual(target["entity"]["id"], "B1")

        # 4. Ngoài bán kính: không chọn
        sim = create_mock_sim(
            pos=[0.0, 0.0],
            stoves=[{"id": "B1", "pos": [2.0, 0.0]}],
            tables=[],
        )
        self.assertIsNone(find_interact_target(sim))

    def test_turn_dropping(self):
        # Bếp đang nấu dở -> bỏ lượt
        sim = create_mock_sim(
            pos=[0.0, 0.0],
            stoves=[{"id": "B1", "pos": [0.5, 0.0], "state": "cooking"}],
            tables=[{"id": "T1", "pos": [1.0, 0.0]}],
        )
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(events, [])

        # Bếp ready nhưng tay đang bận -> bỏ lượt
        sim = create_mock_sim(
            pos=[0.0, 0.0],
            hand={"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
            stoves=[{"id": "B1", "pos": [0.5, 0.0], "state": "ready"}],
        )
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(events, [])

        # Bàn nhưng tay không cầm món -> bỏ lượt
        sim = create_mock_sim(
            pos=[0.0, 0.0],
            hand=None,
            stoves=[],
            tables=[{"id": "T1", "pos": [0.5, 0.0]}],
            customers=[{"id": "C1", "table_id": "T1", "state": "waiting"}],
        )
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(events, [])

        # Bàn nhưng món không khớp order_id -> bỏ lượt
        sim = create_mock_sim(
            pos=[0.0, 0.0],
            hand={"order_id": "C2", "dish_id": "goi_bong_sung", "base_price": 40},
            stoves=[],
            tables=[{"id": "T1", "pos": [0.5, 0.0]}],
            customers=[{"id": "C1", "table_id": "T1", "state": "waiting"}],
        )
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(events, [])

    def test_cook_started_and_stock_deduction(self):
        sim = create_mock_sim(
            pos=[2.0, 8.0],
            stoves=[{"id": "B1", "pos": [2.0, 8.0], "state": "idle"}],
            customers=[
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "lau_ca_linh_dien_dien",
                    "state": "waiting",
                    "order_status": "reserved",
                    "order_tick": 10,
                    "reserved": {"ca_linh": 3, "bong_dien_dien": 1},
                }
            ],
            stock={"ca_linh": 3, "bong_dien_dien": 2},
        )
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(len(events), 1)
        name, data = events[0]
        self.assertEqual(name, "cook_started")
        self.assertEqual(data["stove_id"], "B1")
        self.assertEqual(data["order_id"], "C1")
        self.assertEqual(data["dish_id"], "lau_ca_linh_dien_dien")
        # items sorted alphabet: bong_dien_dien trước ca_linh
        self.assertEqual(data["items"], ["bong_dien_dien", "ca_linh", "ca_linh", "ca_linh"])
        self.assertEqual(data["base_price"], 120)

        # Kiểm tra kho: ca_linh về 0 bị xóa, bong_dien_dien còn 1
        self.assertNotIn("ca_linh", sim.stock)
        self.assertEqual(sim.stock["bong_dien_dien"], 1)

        # Kiểm tra bếp
        stove = sim.stoves[0]
        self.assertEqual(stove["state"], "cooking")
        self.assertEqual(stove["cook_ticks_left"], 600)  # 10s * 60
        self.assertEqual(stove["ready_ticks"], 0)

        # Kiểm tra customer
        c = sim.customers[0]
        self.assertEqual(c["order_status"], "assigned")
        self.assertEqual(c["reserved"], {})

    def test_stoves_advance_ready_ticks_lifecycle(self):
        sim = create_mock_sim(
            stoves=[
                {"id": "B1", "state": "cooking", "cook_ticks_left": 2, "ready_ticks": 0, "order_id": "C1", "dish": "d1"}
            ]
        )
        # Tick 1: cook_ticks_left 2 -> 1
        events = advance_stoves_and_eating(sim)
        self.assertEqual(events, [])
        self.assertEqual(sim.stoves[0]["cook_ticks_left"], 1)
        self.assertEqual(sim.stoves[0]["state"], "cooking")

        # Tick 2: cook_ticks_left 1 -> 0 => dish_ready, ready_ticks = 0 (CHƯA tăng trong tick này)
        events = advance_stoves_and_eating(sim)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], "dish_ready")
        self.assertEqual(sim.stoves[0]["state"], "ready")
        self.assertEqual(sim.stoves[0]["ready_ticks"], 0)

        # Tick 3: Vì bếp đã ready ở ĐẦU BƯỚC, ready_ticks tăng lên 1
        events = advance_stoves_and_eating(sim)
        self.assertEqual(events, [])
        self.assertEqual(sim.stoves[0]["ready_ticks"], 1)

    def test_dish_picked(self):
        sim = create_mock_sim(
            pos=[2.0, 8.0],
            hand=None,
            stoves=[
                {"id": "B1", "pos": [2.0, 8.0], "state": "ready", "order_id": "C1", "dish": "goi_bong_sung", "base_price": 40}
            ],
        )
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(len(events), 1)
        name, data = events[0]
        self.assertEqual(name, "dish_picked")
        self.assertEqual(data["stove_id"], "B1")
        self.assertEqual(data["order_id"], "C1")
        self.assertEqual(data["dish_id"], "goi_bong_sung")

        # Hand populated
        self.assertEqual(sim.hand, {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40})
        # Stove reset
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertIsNone(sim.stoves[0]["dish"])

    def test_served_and_tip_calculation(self):
        # Trường hợp 1: Tỷ lệ kiên nhẫn >= 0.5 -> có tip
        sim = create_mock_sim(
            pos=[3.0, 8.0],
            hand={"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40},
            tables=[{"id": "T1", "pos": [3.0, 8.0]}],
            customers=[
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "goi_bong_sung",
                    "state": "waiting",
                    "patience_ticks_left": 2000,  # 2000 / 3600 > 0.5
                }
            ],
        )
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(len(events), 1)
        name, data = events[0]
        self.assertEqual(name, "served")
        self.assertEqual(data["tip"], 8)  # floor(40 * 0.2) = 8
        self.assertEqual(sim.customers[0]["state"], "eating")
        self.assertEqual(sim.customers[0]["eat_ticks_left"], 600)
        self.assertIsNone(sim.hand)

        # Trường hợp 2: Tỷ lệ kiên nhẫn < 0.5 -> không tip
        sim = create_mock_sim(
            pos=[3.0, 8.0],
            hand={"order_id": "C2", "dish_id": "goi_bong_sung", "base_price": 40},
            tables=[{"id": "T1", "pos": [3.0, 8.0]}],
            customers=[
                {
                    "id": "C2",
                    "table_id": "T1",
                    "dish_id": "goi_bong_sung",
                    "state": "waiting",
                    "patience_ticks_left": 1000,  # 1000 / 3600 < 0.5
                }
            ],
        )
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(events[0][1]["tip"], 0)

        # Trường hợp 3: Kiên nhẫn đúng bằng 0 -> vẫn served hợp lệ, tip = 0
        sim = create_mock_sim(
            pos=[3.0, 8.0],
            hand={"order_id": "C3", "dish_id": "goi_bong_sung", "base_price": 40},
            tables=[{"id": "T1", "pos": [3.0, 8.0]}],
            customers=[
                {
                    "id": "C3",
                    "table_id": "T1",
                    "dish_id": "goi_bong_sung",
                    "state": "waiting",
                    "patience_ticks_left": 0,
                }
            ],
        )
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][1]["tip"], 0)
        self.assertEqual(sim.customers[0]["state"], "eating")

    def test_eating_finished_and_payment(self):
        sim = create_mock_sim(
            reputation=3.0,
            customers=[
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "goi_bong_sung",
                    "state": "eating",
                    "eat_ticks_left": 0,
                    "base_price": 40,
                    "tip": 8,
                }
            ],
        )
        events = handle_finished_eating(sim)
        self.assertEqual(len(events), 1)
        name, data = events[0]
        self.assertEqual(name, "paid")
        self.assertEqual(data["order_id"], "C1")
        self.assertEqual(data["amount"], 48)
        self.assertEqual(data["reason"], "finished_eating")

        self.assertEqual(sim.money, 48)
        self.assertEqual(sim.earned, 48)
        self.assertEqual(sim.shift_earned, 48)
        # tip > 0 -> reputation +0.2 -> 3.2
        self.assertAlmostEqual(sim.reputation, 3.2)
        # Customer removed
        self.assertEqual(sim.customers, [])

    def test_closing(self):
        sim = create_mock_sim(
            time_left_ticks=0,
            reputation=3.0,
            customers=[
                {
                    "id": "C1",
                    "table_id": "T1",
                    "state": "eating",
                    "base_price": 40,
                    "tip": 0,
                },
                {
                    "id": "C2",
                    "table_id": "T2",
                    "state": "waiting",
                },
            ],
        )
        events = handle_closing(sim)
        event_names = [e[0] for e in events]
        self.assertIn("paid", event_names)
        self.assertIn("customer_left", event_names)
        self.assertIn("quan_end", event_names)

        paid_event = [e[1] for e in events if e[0] == "paid"][0]
        self.assertEqual(paid_event["reason"], "closing")
        self.assertEqual(paid_event["order_id"], "C1")

        left_event = [e[1] for e in events if e[0] == "customer_left"][0]
        self.assertEqual(left_event["reason"], "closing")
        self.assertEqual(left_event["order_id"], "C2")

        end_event = [e[1] for e in events if e[0] == "quan_end"][0]
        self.assertEqual(end_event["reason"], "time")

        self.assertTrue(sim.done)
        self.assertEqual(sim.customers, [])

    def test_compute_score(self):
        # score = earned + mult * floor(reputation)
        self.assertEqual(compute_score(150, 3.8), 150 + 100 * 3)
        self.assertEqual(compute_score(200, 4.0), 200 + 100 * 4)

    def test_cancel_customer_order(self):
        sim = create_mock_sim(
            hand={"order_id": "C1", "dish_id": "d1", "base_price": 40},
            stoves=[
                {"id": "B1", "order_id": "C1", "state": "cooking", "dish": "d1", "cook_ticks_left": 100, "ready_ticks": 0}
            ],
        )
        cancel_customer_order(sim, "C1")
        self.assertIsNone(sim.hand)
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertIsNone(sim.stoves[0]["dish"])

    def test_drop_turn_never_tries_second_candidate(self):
        # Bếp B1 gần hơn (0.5m) đang nấu dở.
        # Bếp B2 xa hơn (1.0m) idle và có đơn chờ nấu.
        sim = create_mock_sim(
            pos=[0.0, 0.0],
            stoves=[
                {"id": "B1", "pos": [0.5, 0.0], "state": "cooking", "cook_ticks_left": 50},
                {"id": "B2", "pos": [1.0, 0.0], "state": "idle"},
            ],
            customers=[
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "goi_bong_sung",
                    "state": "waiting",
                    "order_status": "reserved",
                    "order_tick": 5,
                }
            ],
            stock={"bong_sung": 10},
        )
        events = handle_interact(sim, MockInput(["interact"]))
        # Bỏ lượt ngay vì B1 đang nấu dở -> Không có event nào phát sinh
        self.assertEqual(events, [])
        # B2 tuyệt đối không được thử sang
        self.assertEqual(sim.stoves[1]["state"], "idle")
        self.assertEqual(sim.customers[0]["order_status"], "reserved")

    def test_oldest_reserved_order_tie_breaker(self):
        # 3 khách đang chờ:
        # C1: order_tick 20, table_id T1
        # C2: order_tick 10, table_id T3
        # C3: order_tick 10, table_id T2  -> C3 thắng vì order_tick 10 nhỏ nhất và T2 < T3
        sim = create_mock_sim(
            pos=[2.0, 8.0],
            stoves=[{"id": "B1", "pos": [2.0, 8.0], "state": "idle"}],
            customers=[
                {"id": "C1", "table_id": "T1", "dish_id": "goi_bong_sung", "state": "waiting", "order_status": "reserved", "order_tick": 20},
                {"id": "C2", "table_id": "T3", "dish_id": "goi_bong_sung", "state": "waiting", "order_status": "reserved", "order_tick": 10},
                {"id": "C3", "table_id": "T2", "dish_id": "goi_bong_sung", "state": "waiting", "order_status": "reserved", "order_tick": 10},
            ],
            stock={"bong_sung": 10},
        )
        events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], "cook_started")
        self.assertEqual(events[0][1]["order_id"], "C3")
        self.assertEqual(sim.customers[2]["order_status"], "assigned")
        self.assertEqual(sim.customers[1]["order_status"], "reserved")

    def test_dish_picked_and_served_and_eating_flow(self):
        # 1. Bếp B1 ready với món của khách C1
        sim = create_mock_sim(
            pos=[2.0, 8.0],
            hand=None,
            stoves=[
                {"id": "B1", "pos": [2.0, 8.0], "state": "ready", "dish": "goi_bong_sung", "order_id": "C1", "base_price": 40}
            ],
            tables=[{"id": "T1", "pos": [9.0, 2.0]}],
            customers=[
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "goi_bong_sung",
                    "state": "waiting",
                    "order_status": "assigned",
                    "patience_ticks_left": 3000,
                }
            ],
        )

        # 2. Người chơi tương tác với bếp -> dish_picked
        pick_events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(len(pick_events), 1)
        self.assertEqual(pick_events[0][0], "dish_picked")
        self.assertEqual(pick_events[0][1], {"stove_id": "B1", "order_id": "C1", "dish_id": "goi_bong_sung"})
        self.assertEqual(sim.hand, {"order_id": "C1", "dish_id": "goi_bong_sung", "base_price": 40})
        self.assertEqual(sim.stoves[0]["state"], "idle")
        self.assertIsNone(sim.stoves[0]["dish"])

        # 3. Người chơi di chuyển tới bàn T1 và tương tác -> served
        sim.pos = [9.0, 2.0]
        serve_events = handle_interact(sim, MockInput(["interact"]))
        self.assertEqual(len(serve_events), 1)
        self.assertEqual(serve_events[0][0], "served")
        served_data = serve_events[0][1]
        self.assertEqual(served_data["order_id"], "C1")
        self.assertEqual(served_data["table_id"], "T1")
        self.assertEqual(served_data["dish_id"], "goi_bong_sung")
        self.assertEqual(served_data["patience_ticks_left"], 3000)
        self.assertEqual(served_data["base_price"], 40)
        self.assertEqual(served_data["tip"], 8)  # 3000/3600 >= 0.5 -> floor(40 * 0.2) = 8
        self.assertIsNone(sim.hand)

        # 4. Khách ăn: eat_ticks_left = 600, giảm dần mỗi tick
        c = sim.customers[0]
        self.assertEqual(c["state"], "eating")
        self.assertEqual(c["eat_ticks_left"], 600)

        # Tua 600 tick
        c["eat_ticks_left"] = 1
        advance_stoves_and_eating(sim)
        self.assertEqual(c["eat_ticks_left"], 0)

        # 5. Khách ăn xong trả tiền
        pay_events = handle_finished_eating(sim)
        self.assertEqual(len(pay_events), 1)
        self.assertEqual(pay_events[0][0], "paid")
        paid_data = pay_events[0][1]
        self.assertEqual(paid_data["order_id"], "C1")
        self.assertEqual(paid_data["table_id"], "T1")
        self.assertEqual(paid_data["base_price"], 40)
        self.assertEqual(paid_data["tip"], 8)
        self.assertEqual(paid_data["amount"], 48)
        self.assertEqual(paid_data["reason"], "finished_eating")

        self.assertEqual(sim.money, 48)
        self.assertEqual(sim.earned, 48)
        self.assertEqual(sim.shift_earned, 48)
        self.assertAlmostEqual(sim.reputation, 3.2)  # 3.0 + 0.2 tip_reputation
        self.assertEqual(sim.customers, [])  # Bàn được giải phóng

        # Tính điểm
        self.assertEqual(compute_score(sim.earned, sim.reputation), 48 + 100 * 3)

    def test_closing_immediate_payment_for_just_served(self):
        # Khách C1 vừa được giao món trong tick cuối, khách C2 vẫn đang chờ
        sim = create_mock_sim(
            time_left_ticks=0,
            reputation=3.0,
            customers=[
                {
                    "id": "C1",
                    "table_id": "T1",
                    "dish_id": "lau_ca_linh_dien_dien",
                    "state": "eating",
                    "order_status": "served",
                    "eat_ticks_left": 600,  # Vừa mới giao
                    "base_price": 120,
                    "tip": 24,
                },
                {
                    "id": "C2",
                    "table_id": "T2",
                    "dish_id": "goi_bong_sung",
                    "state": "waiting",
                    "order_status": "reserved",
                    "patience_ticks_left": 1500,
                },
            ],
        )
        events = handle_closing(sim)
        # Kiểm tra C1 trả tiền ngay lập tức
        paid_events = [e[1] for e in events if e[0] == "paid"]
        self.assertEqual(len(paid_events), 1)
        self.assertEqual(paid_events[0]["order_id"], "C1")
        self.assertEqual(paid_events[0]["reason"], "closing")
        self.assertEqual(paid_events[0]["amount"], 144)  # 120 + 24

        # Kiểm tra C2 rời không bị trừ uy tín
        left_events = [e[1] for e in events if e[0] == "customer_left"]
        self.assertEqual(len(left_events), 1)
        self.assertEqual(left_events[0]["order_id"], "C2")
        self.assertEqual(left_events[0]["reason"], "closing")
        # Uy tín chỉ tăng do C1 có tip (+0.2), C2 không trừ
        self.assertAlmostEqual(left_events[0]["reputation"], 3.2)
        self.assertAlmostEqual(sim.reputation, 3.2)

        # Sự kiện quan_end phát đúng 1 lần
        end_events = [e[1] for e in events if e[0] == "quan_end"]
        self.assertEqual(len(end_events), 1)
        self.assertEqual(end_events[0]["reason"], "time")
        self.assertEqual(end_events[0]["money"], 144)
        self.assertEqual(end_events[0]["earned"], 144)
        self.assertEqual(end_events[0]["shift_earned"], 144)
        self.assertAlmostEqual(end_events[0]["reputation"], 3.2)

        self.assertTrue(sim.done)
        self.assertEqual(sim.reason, "time")
        self.assertEqual(sim.customers, [])




if __name__ == "__main__":
    unittest.main()
