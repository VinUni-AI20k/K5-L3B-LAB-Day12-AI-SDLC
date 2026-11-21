"""Mô phỏng. Mỗi mode có một lớp với giao diện:

    sim = Sim(tuning, scenario, streams, ids)
    events = sim.step(inp)      # một bước (một tick); inp là chonoi.inputs.InputState
    sim.snapshot() -> dict      # trường riêng của mode (xem PRD-0 mục E)
    sim.done / sim.reason       # kết thúc buổi và lý do
    sim.time_left_ticks, sim.money, sim.earned, sim.reputation

event = (name, data_dict). Runner lo tick, phase, thứ tự ghi và dòng 'end'.
"""

