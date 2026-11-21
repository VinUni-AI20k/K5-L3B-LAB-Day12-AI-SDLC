"""Hái, bắt cá và hồi tài nguyên trong ca Gather."""

import math

from .. import TICK_HZ
from ..ids import id_key, sort_by_id


def _nearest(pos, candidates, radius):
    ranked = ((math.dist(pos, entity["pos"]), id_key(entity["id"]), entity)
              for entity in candidates)
    nearest = min(ranked, default=None)
    if nearest is not None and nearest[0] <= radius:
        return nearest[2]
    return None


def tick_resources(sim, events):
    sim.catch_cd_ticks = max(0, sim.catch_cd_ticks - 1)
    for node in sort_by_id(sim.nodes):
        if node["regrow_ticks"] > 0:
            node["regrow_ticks"] -= 1
            if node["regrow_ticks"] == 0:
                events.append(("node_regrown", {"node_id": node["id"]}))


def harvest(sim, events):
    if not sim._at_surface():
        return
    ready = (node for node in sim.nodes if node["regrow_ticks"] == 0)
    node = _nearest(sim.pos, ready, sim.t["interact_radius"])
    if node is None:
        return

    amount = sim.t["node_yield"]
    if not sim._try_add_to_hold(node["kind"], amount):
        events.append(("hold_full", {"action": "gather", "node_id": node["id"],
                                     "required": amount, "free": sim.t["hold_capacity"] - len(sim.hold)}))
        return

    node["regrow_ticks"] = round(sim.t["regrow_s"] * TICK_HZ)
    events.append(("gather", {"node_id": node["id"], "kind": node["kind"], "amount": amount}))


def catch_fish(sim, events):
    if sim.catch_cd_ticks > 0 or sim._at_surface():
        return
    fish = _nearest(sim.pos, sim.fish, sim.t["catch_radius"])
    if fish is None:
        return

    amount = sim.t["fish_yield"][fish["kind"]]
    if not sim._try_add_to_hold(fish["kind"], amount):
        events.append(("hold_full", {"action": "catch", "fish_id": fish["id"],
                                     "required": amount, "free": sim.t["hold_capacity"] - len(sim.hold)}))
        return

    sim.fish.remove(fish)
    sim.catch_cd_ticks = round(sim.t["catch_cooldown_s"] * TICK_HZ)
    events.append(("fish_caught", {"fish_id": fish["id"], "kind": fish["kind"], "yield": amount}))
