"""Vòng ngày `--mode day` (Test Contract v1.1, Ticket-02 mục 2, 4.4, 4.5). C viết. KHUNG: giao diện cố định.

DaySession phải có CÙNG giao diện với runner.Session để headless (`runner.run`) và cửa sổ chơi (`live.py`) dùng
chung:

    sess = DaySession(tuning, scenario, seed, days, contract=None)
    sess.tick, sess.done
    sess.snapshot() -> dict        # thêm day, day_plan, upgrades, active_upgrades; phase gather|quan|shop
    sess.step(inp) -> list[dict]   # dòng event, vỏ có thêm "day"
    sess.end_row() -> dict         # thêm days_completed; đủ Ngày thì reason "days_complete"
    sess.write_inventory_if_done(path)  # day không dùng file kho: không làm gì

Gợi ý dựng (xem docs/contracts/README.md, mục v1.1):
- `scenario` là {"gather": ..., "quan": ..., "day": ...} (scenario.load_scenario với mode "day").
- Một Streams(seed) và một IdAllocator cho cả lượt; một runner.PauseGate cho pause.
- Ngày mới: active_upgrades = copy(upgrades); phát day_start -> day_plan -> phase_start(gather) ở tick đó;
  GatherSim(tuning, scenario["gather"], streams, ids, day=day, active_upgrades=active_upgrades).
- gather_end (kể cả fainted): dựng QuanSim(tuning, scenario["quan"], streams, ids, inventory=kho bàn giao,
  plan_dishes=list(day_plan["dishes"]), carry={money, earned, reputation}); phát phase_start(quan) cùng tick.
- quan_end: dựng shop.ShopSim, phát phase_start(shop) cùng tick.
- shop_end: days_completed += 1; còn Ngày thì dựng Ngày kế ngay tick đó, hết thì done, reason "days_complete".
- Snapshot đổi pha ghi pha mới với phase_tick 0. Event kết thúc pha mang pha cũ.
- Một Ngày không pause tối đa 22.200 tick phải chạy headless dưới 20 s.
"""

from .errors import BadInput


class DaySession:
    def __init__(self, tuning, scenario, seed, days, contract=None):
        # TODO(C): thay bằng vòng ngày thật. Tạm thời báo mã 2 để --mode day không chạy nửa vời.
        raise BadInput("--mode day chưa làm xong (DaySession, chonoi/day.py)")
