"""QA Phase 3: kiểm giá chốt theo độ tươi trong output headless (quan hoặc day).

Mỗi cook_started: base_price == floor(giá niêm yết × avg(fresh của items) / 100), items sắp (kind, id).
Mỗi served: tip == floor(base_price × tip_rate) hoặc 0. Mỗi paid: amount == base_price + tip.

    python3 tools/qa_check_quan_prices.py docs/proof/phase-3/integration-quan.jsonl
"""
import json
import math
import sys
from fractions import Fraction

sys.path.insert(0, ".")
from chonoi.ids import id_key  # noqa: E402

t = json.load(open("game.contract.json", encoding="utf-8"))["tuning"]
menu, tip_rate = t["menu"], Fraction(str(t["quan"]["tip_rate"]))
rows = [json.loads(line) for line in open(sys.argv[1], encoding="utf-8")]
bad, n = [], 0
locked = {}
for r in rows:
    if r["type"] != "event":
        continue
    d = r["data"]
    if r["name"] == "cook_started":
        n += 1
        its = d["items"]
        avg = sum(Fraction(str(x["fresh"])) for x in its) / len(its)
        raw = Fraction(menu[d["dish_id"]]["price"]) * avg / 100
        exp = math.floor(raw)
        # fresh trong JSON là float: nếu raw sát mép số nguyên (≤ 1e-6) thì chấp nhận cả hai phía
        allowed = {exp, round(raw) - 1} if abs(raw - round(raw)) <= Fraction(1, 10**6) else {exp}
        order_ok = [(x["kind"], id_key(x["id"])) for x in its] == sorted((x["kind"], id_key(x["id"])) for x in its)
        ok = d["base_price"] in allowed and order_ok
        locked[d["order_id"]] = d["base_price"]
        print(f'tick {r["tick"]} cook {d["dish_id"]} avg_fresh {float(avg):.3f} '
              f'price {menu[d["dish_id"]]["price"]} -> base {d["base_price"]} (expect {exp}) items_sorted={order_ok} ok={ok}')
        if not ok:
            bad.append(r)
    elif r["name"] == "served":
        tip_ok = d["tip"] in (0, math.floor(d["base_price"] * tip_rate))
        same = locked.get(d["order_id"], d["base_price"]) == d["base_price"]
        print(f'tick {r["tick"]} served {d["order_id"]} base {d["base_price"]} tip {d["tip"]} ok={tip_ok and same}')
        if not (tip_ok and same):
            bad.append(r)
    elif r["name"] == "paid":
        if d["amount"] != d["base_price"] + d["tip"]:
            bad.append(r)
print(f"cook_started checked: {n}; bad: {bad}")
