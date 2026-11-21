"""Điểm vào soak headless: python3 -m chonoi.soak --seed 7 --days 10 --out soak.json

Chạy N Ngày trong một tiến trình headless bằng script input hoặc bot tất định.
Mỗi Ngày đi qua gather → quan → shop. Kế hoạch D1–D5 lặp ở Ngày 6–10.
Tiền, tổng thu, uy tín, cấp nâng cấp, số Ngày và id cá thể tiếp tục xuyên suốt.
"""

import argparse
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path

from .contract import load_contract
from .errors import BadInput
from .ids import IdAllocator
from .inputs import InputState
from .rng import Streams
from .sim.gather import GatherSim
from .sim.quan import QuanSim


def run_soak(seed: int, days: int) -> dict:
    contract = load_contract()
    tuning = contract["tuning"]

    start_time = time.perf_counter()
    ids = IdAllocator()

    money = 0
    earned = 0
    reputation = float(tuning["quan"]["reputation_initial"])
    upgrades = {"oxygen": 0, "hp": 0}

    day_plans = tuning.get("day_plan", [])
    shop_cfg = tuning.get("shop", {})
    upgrade_defs = shop_cfg.get("upgrades", {})
    score_mult = tuning.get("score", {}).get("reputation_multiplier", 100)

    results = []
    crashes = 0
    days_completed = 0

    idle_input = InputState((0.0, 0.0), {}, set())
    dock_input = InputState((0.0, 0.0), {}, {"interact"})

    for d in range(1, days + 1):
        try:
            day_plan_idx = (d - 1) % len(day_plans) if day_plans else 0
            current_plan = day_plans[day_plan_idx] if day_plans else {}

            # 1. Buổi sáng: Gather
            day_streams = Streams(seed * 1000 + d)

            tuning_day = json.loads(json.dumps(tuning))
            if upgrades["oxygen"] > 0 and "oxygen" in upgrade_defs:
                lvl_idx = min(upgrades["oxygen"] - 1, len(upgrade_defs["oxygen"]) - 1)
                tuning_day["gather"]["oxygen_max_s"] = upgrade_defs["oxygen"][lvl_idx]["oxygen_max_s"]
            if upgrades["hp"] > 0 and "hp" in upgrade_defs:
                lvl_idx = min(upgrades["hp"] - 1, len(upgrade_defs["hp"]) - 1)
                tuning_day["gather"]["hp_max"] = upgrade_defs["hp"][lvl_idx]["hp_max"]

            monsters_cfg = tuning_day["gather"].get("monsters", {})
            spawns = [m for m in monsters_cfg.get("spawns", []) if m.get("from_day", 1) <= d]

            scenario_gather = {
                "player": {"pos": [2, 0]},
                "random_fish": True,
                "monsters": spawns,
            }
            gather_sim = GatherSim(tuning_day, scenario_gather, day_streams, ids)

            # Bot cập bến ở bến [2, 0] để kết thúc buổi sáng an toàn
            gather_sim.step(dock_input)
            if not gather_sim.done:
                for _ in range(300):
                    gather_sim.step(dock_input)
                    if gather_sim.done:
                        break

            inventory = gather_sim.inventory_items()

            # 2. Buổi tối: Quán
            scenario_quan = {
                "day_plan": current_plan,
                "random_customers": True,
            }
            quan_sim = QuanSim(tuning_day, scenario_quan, day_streams, ids, inventory=inventory)
            quan_sim.reputation = reputation

            max_quan_ticks = int(round(tuning_day["quan"]["duration_s"] * 60))
            for _ in range(max_quan_ticks):
                if quan_sim.done:
                    break
                quan_sim.step(idle_input)

            shift_earned = quan_sim.earned
            money += shift_earned
            earned += shift_earned
            reputation = float(quan_sim.reputation)

            # 3. Cuối ngày: Shop
            if "oxygen" in upgrade_defs:
                next_lvl = upgrades["oxygen"]
                if next_lvl < len(upgrade_defs["oxygen"]):
                    cost = upgrade_defs["oxygen"][next_lvl]["price"]
                    if money >= cost:
                        money -= cost
                        upgrades["oxygen"] += 1
            if "hp" in upgrade_defs:
                next_lvl = upgrades["hp"]
                if next_lvl < len(upgrade_defs["hp"]):
                    cost = upgrade_defs["hp"][next_lvl]["price"]
                    if money >= cost:
                        money -= cost
                        upgrades["hp"] += 1

            score = earned + score_mult * math.floor(reputation)
            results.append({
                "day": d,
                "earned": earned,
                "reputation": round(reputation, 2),
                "score": int(score),
            })
            days_completed += 1

        except Exception as e:
            crashes += 1
            sys.stderr.write(f"Lỗi ngày {d}: {e}\n")
            break

    elapsed = time.perf_counter() - start_time
    return {
        "days": days,
        "days_completed": days_completed,
        "crashes": crashes,
        "results": results,
        "duration_s": round(elapsed, 3),
    }


def write_soak(path: Path, data: dict):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=".soak-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(temp_path, path)
    finally:
        if os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except OSError:
                pass


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Soak headless simulation for N days.")
    parser.add_argument("--seed", type=int, required=True, help="RNG seed")
    parser.add_argument("--days", type=int, default=10, help="Số ngày mô phỏng")
    parser.add_argument("--out", type=Path, required=True, help="Đường dẫn file kết quả JSON")
    args = parser.parse_args(argv)

    if args.days <= 0:
        sys.stderr.write("đầu vào sai: --days phải > 0\n")
        return 2

    try:
        data = run_soak(args.seed, args.days)
        write_soak(args.out, data)
    except Exception as e:
        sys.stderr.write(f"Lỗi soak: {e}\n")
        return 1

    print(json.dumps(data, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
