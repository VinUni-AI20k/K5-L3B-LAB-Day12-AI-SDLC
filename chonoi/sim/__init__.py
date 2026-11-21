"""Mô phỏng. Mỗi mode có một lớp với giao diện:

    sim = Sim(tuning, scenario, streams, ids)
    events = sim.step(inp)      # một bước (một tick); inp là chonoi.inputs.InputState
    sim.snapshot() -> dict      # trường riêng của mode (xem PRD-0 mục E)
    sim.done / sim.reason       # kết thúc buổi và lý do
    sim.time_left_ticks, sim.money, sim.earned, sim.reputation

event = (name, data_dict). Runner lo tick, phase, thứ tự ghi và dòng 'end'.
"""

from .day import DaySim, DEFAULT_DAILY_MENU
from .gather import GatherSim
from .kitchen import interact_stove, step_stoves
from .quan import QuanSim
from .service import handle_table_interact, update_dining, update_patience, update_service
from .shop import ShopSim, UPGRADE_CATALOG

__all__ = [
    "DaySim",
    "DEFAULT_DAILY_MENU",
    "GatherSim",
    "QuanSim",
    "ShopSim",
    "UPGRADE_CATALOG",
    "handle_table_interact",
    "update_dining",
    "update_patience",
    "update_service",
    "step_stoves",
    "interact_stove",
]

