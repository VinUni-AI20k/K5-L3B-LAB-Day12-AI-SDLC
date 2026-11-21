"""Sổ quán: quản lý tiền, doanh thu và uy tín (có kẹp biên và làm tròn chống trôi float).

Chủ: Phạm Quốc Huy (Lát 4). Chỉ module này được ghi money / earned / shift_earned / reputation.
"""


def add_money(sim, amount: int) -> None:
    sim.money += amount
    sim.earned += amount
    sim.shift_earned += amount


def add_reputation(sim, delta: float) -> None:
    lo = sim.t["reputation_min"]
    hi = sim.t["reputation_max"]
    sim.reputation = round(max(lo, min(hi, sim.reputation + delta)), 6)
