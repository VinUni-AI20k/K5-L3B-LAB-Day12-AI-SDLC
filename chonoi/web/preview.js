// Một dãy snapshot mẫu hữu hạn để nghiệm thu UI. Không có luật mô phỏng.
export class PreviewAdapter {
  async config() {
    const get = async (path) => {
      const response = await fetch(new URL(path, import.meta.url));
      if (!response.ok) throw new Error("Mở bản xem bằng máy chủ tĩnh ở thư mục gốc.");
      return response.json();
    };
    const [contract, inventory] = await Promise.all([
      get("../../game.contract.json"),
      get("../../docs/contracts/inventory.sample.json"),
    ]);
    this.tuning = contract.tuning;
    if (!Array.isArray(this.tuning.gather.fish_initial)) {
      const { tuning: sample } = await get("./phase2.preview.json");
      this.tuning = { ...this.tuning, gather: { ...this.tuning.gather, fish_initial: sample.gather.fish_initial } };
    }
    this.sampleItems = inventory.items;
    this.serial = 0;
    return this.tuning;
  }

  play(choice) {
    if (choice === "menu") return;
    const mode = choice === "quan" ? "quan" : "gather";
    this.enter(mode, this.sampleItems);
  }

  enter(mode, items) {
    this.mode = mode;
    this.items = items;
    this.serial += 1;
    this.down = {};
    this.step = 0;
    this.frames = mode === "gather" ? gatherFrames(this.tuning) : quanFrames(this.tuning, items);
  }

  continueDay() {
    const end = this.frames.at(-1).events.find((event) => event.name === "gather_end");
    this.enter("quan", end.data.inventory.items);
  }

  restart() {
    this.enter(this.mode, this.items);
  }

  input(frame) {
    const pressed = ["interact", "catch"].some((name) => frame[name] && !this.down[name]);
    Object.assign(this.down, frame);
    if (pressed) this.step = Math.min(this.step + 1, this.frames.length - 1);
  }

  state() {
    return { ...this.frames[this.step], session_id: this.serial };
  }
}

function event(name, data = {}) {
  return { name, data };
}

function reel(tuning, mode, frames) {
  const history = [];
  const hz = tuning.tick_hz;
  const initialReputation = tuning.quan.reputation_initial;
  return frames.map(({ tick = 0, events = [], reason = null, ...state }) => {
    history.push(...events.map((entry) => ({ ...entry, tick, type: "event", phase: mode })));
    const score = tuning.score.reputation_multiplier * Math.floor(initialReputation);
    return {
      type: "snapshot", mode, phase: mode, tick, sim_tick: tick, phase_tick: tick,
      state: reason ? "finished" : "playing", finished: Boolean(reason), reason, error: null,
      time_left_ticks: reason === "time" ? 0 : tuning[mode].duration_s * hz - tick,
      meta: tuning[mode], events: [...history],
      money: 0, earned: 0, reputation: initialReputation, score,
      ...state,
    };
  });
}

function gatherFrames(tuning) {
  const g = tuning.gather;
  const hz = tuning.tick_hz;
  const vegetables = g.nodes.filter((node) => node.kind === "bong_sung");
  const [first, second] = vegetables;
  const fish = g.fish_initial.find((item) => item.kind === "ca_loc");
  const oxygenMax = g.oxygen_max_s * hz;
  const frame = ({ pos = g.start_pos, hold = [], picked = [], caught = false, player = {}, ...rest } = {}) => ({
    player: {
      pos, vel: [0, 0], heading_deg: g.start_heading_deg, at_surface: pos[1] <= g.surface_depth,
      oxygen_ticks: oxygenMax, oxygen_max_ticks: oxygenMax, hp: g.hp_max, hp_max: g.hp_max,
      zero_oxy_ticks: 0, catch_cd_ticks: 0, ...player,
    },
    nodes: g.nodes.map((node) => ({
      ...node, ready: !picked.includes(node.id), regrow_ticks: picked.includes(node.id) ? g.regrow_s * hz : 0,
    })),
    fish: g.fish_initial.filter((item) => !caught || item.id !== fish.id),
    hold, hold_count: hold.length, hold_capacity: g.hold_capacity,
    ...rest,
  });
  const picked = [first.id, second.id];
  const firstHarvest = Array(g.node_yield).fill(first.kind);
  const hold = [...firstHarvest, ...Array(g.node_yield).fill(second.kind)];
  const fullHaul = [...hold, ...Array(g.fish_yield[fish.kind]).fill(fish.kind)];
  return reel(tuning, "gather", [
    frame({ pos: first.pos }),
    frame({ tick: hz * 8, pos: second.pos, hold: firstHarvest, picked: picked.slice(0, 1),
      events: [event("gather", { node_id: first.id, kind: first.kind, amount: g.node_yield })] }),
    frame({ tick: hz * 17, pos: fish.pos, hold, picked, player: { oxygen_ticks: oxygenMax / 2, heading_deg: 30 },
      events: [event("gather", { node_id: second.id, kind: second.kind, amount: g.node_yield })] }),
    frame({ tick: hz * 19, pos: fish.pos, hold: fullHaul, picked, caught: true,
      player: { oxygen_ticks: oxygenMax / 3, catch_cd_ticks: g.catch_cooldown_s * hz },
      events: [event("fish_caught", { fish_id: fish.id, kind: fish.kind, yield: g.fish_yield[fish.kind] })] }),
    frame({ tick: hz * 35, pos: fish.pos, hold: fullHaul, picked, caught: true,
      player: { oxygen_ticks: 0, hp: g.hp_max - 1 },
      events: [event("oxygen_empty", { oxygen_ticks: 0 }), event("choke", { hp: g.hp_max - 1 })] }),
    frame({ tick: hz * 55, pos: g.dock_pos, hold: fullHaul, caught: true, reason: "docked",
      events: [event("gather_end", { reason: "docked", inventory: { items: { [first.kind]: hold.length, [fish.kind]: g.fish_yield[fish.kind] } } })] }),
  ]);
}

function quanFrames(tuning, items) {
  const q = tuning.quan;
  const hz = tuning.tick_hz;
  const [stove] = q.stoves;
  const [table] = q.tables;
  const dishId = "goi_bong_sung";
  const menu = tuning.menu[dishId];
  const dish = { order_id: "C1", dish_id: dishId, base_price: menu.price };
  const tip = Math.floor(menu.price * q.tip_rate);
  const paid = menu.price + tip;
  const patience = Math.round(q.patience_s * hz * .7);
  const emptyStove = { ...stove, state: "idle", dish: null, cook_ticks_left: 0, ready_ticks: 0 };
  const reserved = {
    id: dish.order_id, dish_id: dishId, table_id: table.id, order_tick: q.first_customer_tick,
    state: "waiting", order_status: "reserved", reserved: menu.recipe, patience_ticks_left: q.patience_s * hz,
    eat_ticks_left: 0, base_price: null, tip: null,
  };
  const assigned = { ...reserved, order_status: "assigned", reserved: {}, patience_ticks_left: patience };
  const eating = {
    ...assigned, state: "eating", order_status: "served", eat_ticks_left: q.eat_s * hz / 2,
    base_price: menu.price, tip,
  };
  const remainingStock = Object.fromEntries(Object.entries(items).flatMap(([kind, count]) => {
    const remaining = count - (menu.recipe[kind] ?? 0);
    return remaining > 0 ? [[kind, remaining]] : [];
  }));
  const frame = ({ tick, pos = q.start_pos, customer, st = emptyStove, hand = null, stock = items, ...rest } = {}) => ({
    tick,
    player: { pos, vel: [0, 0] }, stock, hand, stoves: [st],
    tables: [{ ...table, customer_id: customer?.id ?? null }], customers: customer ? [customer] : [],
    ...rest,
  });
  const order = { order_id: dish.order_id, dish_id: dishId };
  const atStove = { ...order, stove_id: stove.id };
  const atTable = { ...order, table_id: table.id };
  const reputation = q.reputation_initial + q.tip_reputation;
  const totals = { money: paid, earned: paid, reputation, score: paid + tuning.score.reputation_multiplier * Math.floor(reputation) };
  return reel(tuning, "quan", [
    frame({ tick: 0 }),
    frame({ tick: q.first_customer_tick, pos: stove.pos, customer: reserved, events: [event("customer_arrived", atTable)] }),
    frame({ tick: hz * 6, pos: stove.pos, stock: remainingStock, customer: assigned,
      st: { ...emptyStove, state: "cooking", dish, cook_ticks_left: menu.cook_s * hz / 2 },
      events: [event("cook_started", { ...atStove, base_price: menu.price,
        items: Object.entries(menu.recipe).sort().flatMap(([kind, n]) => Array(n).fill(kind)) })] }),
    frame({ tick: hz * 10, pos: stove.pos, stock: remainingStock, customer: assigned,
      st: { ...emptyStove, state: "ready", dish }, events: [event("dish_ready", atStove)] }),
    frame({ tick: hz * 12, pos: table.pos, stock: remainingStock, customer: assigned, hand: dish,
      events: [event("dish_picked", atStove)] }),
    frame({ tick: hz * 18, pos: table.pos, stock: remainingStock, customer: eating,
      events: [event("served", { ...atTable, base_price: menu.price, tip, patience_ticks_left: patience })] }),
    frame({ tick: hz * 24, stock: remainingStock, ...totals,
      events: [event("paid", { order_id: dish.order_id, table_id: table.id, base_price: menu.price, tip, amount: paid, reason: "finished_eating" })] }),
    frame({ tick: hz * q.duration_s, stock: remainingStock, ...totals, reason: "time",
      events: [event("quan_end", { reason: "time", money: paid, earned: paid, shift_earned: paid, reputation })] }),
  ]);
}
