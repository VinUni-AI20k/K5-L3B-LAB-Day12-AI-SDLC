// Bộ phát snapshot mẫu, chỉ dùng trong bản xem Phase 2.
export class MockSimV11Adapter {
  async config() {
    const result = await fetch(new URL("./phase2.preview.json", import.meta.url));
    if (!result.ok) throw new Error("Không tải được dữ liệu mẫu Phase 2.");
    this.contract = await result.json();
    return this.contract;
  }

  play(mode) {
    this.active = mode !== "menu";
    if (!this.active) return;
    this.day = 0;
    this.tick = 0;
    this.session = (this.session ?? 0) + 1;
    this.events = [];
    this.money = 0;
    this.earned = 0;
    this.finished = false;
    this.reputation = this.contract.tuning.quan.reputation_initial;
    this.upgrades = { oxygen: 0, hp: 0 };
    if (mode === "quan") {
      this.mode = mode;
      this.day = 1;
      this.plan = this.contract.tuning.day_plan[0];
      this.activeUpgrades = { ...this.upgrades };
      this.stock = { ...this.plan.ingredients };
      this.enter("quan");
    } else {
      this.mode = mode;
      this.nextDay();
      if (mode === "gather") this.awaiting = null;
    }
  }

  restart() { this.play(this.mode); }

  emit(name, data = {}) {
    this.events.push({ type: "event", tick: this.tick, day: this.day, phase: this.phase, name, data });
    this.events = this.events.slice(-40);
  }

  enter(phase, awaiting = null) {
    this.phase = phase;
    this.awaiting = awaiting;
    this.step = 0;
    this.shift = 0;
    this.paused = false;
    this.clock = null;
    this.tick++;
  }

  nextDay() {
    const tuning = this.contract.tuning;
    if (this.day === tuning.day_plan.length) {
      this.finished = true;
      this.tick++;
      return;
    }
    this.finished = false;
    this.day++;
    this.plan = tuning.day_plan[this.day - 1];
    this.activeUpgrades = { ...this.upgrades };
    this.stock = {};
    this.enter("gather", "day_intro");
    this.emit("day_plan", this.plan);
  }

  continueDay(screen) {
    if (this.awaiting !== screen) return;
    this.awaiting = null;
    if (this.phase === "shop") this.clock = performance.now();
  }

  get shopLeft() {
    const { tick_hz, shop } = this.contract.tuning;
    const at = this.paused ? this.pauseAt : performance.now();
    return Math.max(0, shop.duration_ticks - (this.clock == null ? 0 : Math.floor((at - this.clock) * tick_hz / 1000)));
  }

  input(frame) {
    if (!this.active || this.awaiting || this.finished) return;
    if (frame.pause === true) {
      const now = performance.now();
      this.tick++;
      if (this.paused && this.clock != null) this.clock += now - this.pauseAt;
      this.paused = !this.paused;
      this.pauseAt = now;
      this.emit(this.paused ? "paused" : "resumed");
      return;
    }
    if (this.paused) return;
    if (this.phase === "gather" && (frame.interact || frame.catch)) return this.gatherFrame();
    if (this.phase === "quan" && frame.interact) return this.quanFrame();
    if (this.phase === "shop" && frame.buy) this.buyFrame(frame.buy);
    if (this.phase === "shop" && frame.shop_done) this.nextDay();
  }

  gatherFrame() {
    const g = this.contract.tuning.gather;
    this.tick++;
    this.step++;
    if (this.step === 1) this.emit("gather", { kind: g.nodes[0].kind, amount: 1, node_id: g.nodes[0].id });
    if (this.step === 2) {
      this.emit("fish_spawned", { fish_id: "F7", kind: "ca_keo" });
      this.emit("monster_hit", { monster_id: "M1", hp: 2, lost: [g.nodes[0].kind] });
    }
    if (this.step < 3) return;
    const faint = this.day === 3;
    this.stock = faint ? {} : { ...this.plan.ingredients };
    if (faint) this.emit("faint", { cause: "monster", lost: ["ca_keo"], hp: 0 });
    this.emit("gather_end", { reason: faint ? "fainted" : "docked", inventory: { items: { ...this.stock } } });
    if (this.mode === "gather") this.finished = true;
    else this.enter("quan", "evening_intro");
  }

  orderPrice(dishId) { return this.contract.tuning.menu[dishId].price; }

  quanFrame() {
    const tuning = this.contract.tuning;
    const dishId = this.plan.dishes[0];
    const { recipe } = tuning.menu[dishId];
    const price = this.orderPrice(dishId, "C1");
    const secondPrice = this.orderPrice(dishId, "C2");
    const tableId = tuning.quan.tables[0].id;
    const order = { table_id: tableId, order_id: "C1", dish_id: dishId };
    this.tick++;
    this.step++;
    if (!Object.keys(this.stock).length) {
      this.emit("no_dish");
      this.closeShift();
      return;
    }
    if (this.step === 1) this.emit("cook_started", { ...order, stove_id: "B1", base_price: price });
    if (this.step === 2) {
      this.emit("dish_ready", { ...order, stove_id: "B1" });
      this.emit("dish_picked", { ...order, stove_id: "B1" });
      this.emit("dish_ready", { ...order, order_id: "C2", table_id: "T2", stove_id: "B2" });
    }
    if (this.step === 3) this.emit("served", { ...order, base_price: price, tip: 15 });
    if (this.step !== 4) return;
    this.shift = price + secondPrice + 30;
    this.earned += this.shift;
    this.money += this.shift;
    this.reputation = Number((this.reputation + .2).toFixed(1));
    for (const [id, table, basePrice] of [["C1", "T1", price], ["C2", "T2", secondPrice]]) {
      if (id === "C2") this.emit("served", { ...order, order_id: id, table_id: table, base_price: basePrice, tip: 15 });
      this.emit("paid", { ...order, order_id: id, table_id: table, base_price: basePrice, tip: 15, amount: basePrice + 15, reason: "finished_eating" });
    }
    this.emit("customer_left", { order_id: "C3", table_id: "T3", reason: "patience", reputation: this.reputation });
    this.stock = this.shiftStock(recipe);
    this.closeShift();
  }

  shiftStock(recipe) {
    return Object.fromEntries(Object.entries(this.stock).flatMap(([id, amount]) => {
      const remaining = amount - 2 * (recipe[id] ?? 0);
      return remaining > 0 ? [[id, remaining]] : [];
    }));
  }

  closeShift() {
    this.emit("quan_end", { reason: "time", earned: this.earned, money: this.money, shift_earned: this.shift, reputation: this.reputation });
    if (this.mode === "quan") this.finished = true;
    else {
      const shift = this.shift;
      this.enter("shop", "day_result");
      this.shift = shift;
    }
  }

  buyFrame(id) {
    const options = this.contract.tuning.shop.upgrades[id];
    if (!options) return;
    const upgrade = options.find((item) => item.level === this.upgrades[id] + 1);
    this.tick++;
    if (!upgrade || upgrade.price > this.money) {
      this.emit("buy_failed", { upgrade: id, reason: upgrade ? "funds" : "max_level" });
      return;
    }
    this.money -= upgrade.price;
    this.upgrades[id] = upgrade.level;
    this.emit("bought", { upgrade: id, level: upgrade.level, price: upgrade.price, money: this.money });
  }

  gatherSnapshot(tuning) {
    const g = tuning.gather;
    const oxygen = tuning.shop.upgrades.oxygen.find((item) => item.level === this.activeUpgrades.oxygen)?.oxygen_max_s ?? g.oxygen_max_s;
    const hp = tuning.shop.upgrades.hp.find((item) => item.level === this.activeUpgrades.hp)?.hp_max ?? g.hp_max;
    const max = oxygen * tuning.tick_hz;
    const pos = [g.nodes[0].pos, [47, 11], [75, 21]][Math.min(this.step, 2)];
    const hold = this.step === 2 ? Object.entries(this.plan.ingredients).flatMap(([id, amount]) => Array(amount).fill(id))
      : this.step === 1 ? [g.nodes[0].kind] : [];
    const state = ["patrol", "chase", "recoil"][Math.min(this.step, 2)];
    const monsters = [{ id: "M1", kind: "ca_sau", pos: [pos[0] + 5, 14 + this.step], heading_deg: 180, state }];
    if (this.day >= 3) monsters.push({ id: "M2", kind: "ca_sau", pos: [82, 25], heading_deg: 0, state: "patrol" });
    const fish = g.fish_initial.map((item, i) => ({ ...item, pos: [item.pos[0] + this.step * (i % 2 ? -1 : 1), item.pos[1]] }));
    if (this.step >= 2) fish.push({ id: "F7", kind: "ca_keo", pos: [74, 23], heading_deg: 0 });
    return {
      player: { pos, vel: this.step ? [1, 1] : [0, 0], heading_deg: this.step ? 35 : 0, at_surface: this.step === 0,
        oxygen_ticks: Math.floor(max * [1, .23, 0][Math.min(this.step, 2)]), oxygen_max_ticks: max,
        hp: hp - (this.step > 1 ? 1 : 0), hp_max: hp, invuln_ticks: this.step === 2 ? 60 : 0,
        zero_oxy_ticks: this.step === 2 ? 43 : 0, catch_cd_ticks: this.step === 2 ? 21 : 0 },
      hold, hold_count: hold.length, hold_capacity: g.hold_capacity,
      nodes: g.nodes.map((node, i) => ({ ...node, ready: !(this.step && i === 0), regrow_ticks: this.step && i === 0 ? 310 : 0 })),
      fish,
      monsters,
    };
  }

  quanSnapshot(tuning) {
    const q = tuning.quan;
    const id = this.plan.dishes[0];
    const recipe = tuning.menu[id];
    const dish = { order_id: "C1", dish_id: id, base_price: recipe.price };
    const hasStock = !this.finished && Object.keys(this.stock).length > 0;
    const c = { id: "C1", table_id: "T1", dish_id: id, order_tick: 0, state: this.step === 3 ? "eating" : "waiting",
      order_status: ["reserved", "assigned", "assigned", "served"][this.step],
      patience_ticks_left: tuning.tick_hz * (this.step ? 35 : 55), eat_ticks_left: this.step === 3 ? 210 : 0,
      reserved: this.step === 0 ? recipe.recipe : {}, base_price: recipe.price, tip: this.step === 3 ? 15 : null };
    const customers = hasStock ? [c,
      { ...c, id: "C2", table_id: "T2", state: "waiting", order_status: this.step ? "assigned" : "reserved", eat_ticks_left: 0, tip: null },
      { ...c, id: "C3", table_id: "T3", state: "waiting", order_status: "unfulfillable", patience_ticks_left: 360, reserved: {}, eat_ticks_left: 0, tip: null },
    ] : [];
    return {
      player: { pos: [q.stoves[0].pos, q.stoves[1].pos, q.tables[0].pos, q.tables[0].pos][this.step] ?? q.start_pos, vel: [0, 0] },
      stock: this.step > 0 && !this.finished ? this.shiftStock(recipe.recipe) : { ...this.stock }, customers,
      stoves: q.stoves.map((stove, index) => {
        const state = hasStock && this.step === 1 ? "cooking" : hasStock && this.step === 2 && index === 1 ? "ready" : "idle";
        return { ...stove, state, dish: state === "idle" ? null : { ...dish, order_id: index ? "C2" : "C1" },
          cook_ticks_left: state === "cooking" ? tuning.tick_hz * (2 + index) : 0, ready_ticks: 0 };
      }),
      tables: q.tables.map((table) => ({ ...table, customer_id: customers.find((customer) => customer.table_id === table.id)?.id ?? null })),
      hand: hasStock && this.step === 2 ? dish : null,
    };
  }

  state() {
    const tuning = this.contract.tuning;
    if (this.phase === "shop" && !this.awaiting && !this.paused && !this.finished && this.shopLeft === 0) this.nextDay();
    const phase = this.phase;
    const extra = phase === "gather" ? this.gatherSnapshot(tuning) : phase === "quan" ? this.quanSnapshot(tuning) : { stock: { ...this.stock } };
    const phaseTick = phase === "shop" ? tuning.shop.duration_ticks - this.shopLeft : this.step * 60;
    const elapsed = phase === "gather" ? ([0, 55, 160][this.step] ?? tuning.gather.duration_s) : this.step * 45;
    const left = phase === "shop" ? this.shopLeft : Math.max(0, (tuning[phase].duration_s - elapsed) * tuning.tick_hz);
    return {
      type: "snapshot", mode: this.mode, phase, day: this.day, tick: this.tick, sim_tick: this.tick,
      phase_tick: phaseTick, state: this.finished ? "finished" : this.paused ? "paused" : "playing",
      finished: this.finished, time_left_ticks: left, session_id: this.session, awaiting: this.awaiting,
      day_plan: this.plan, meta: tuning[phase], money: this.money, earned: this.earned,
      shift_earned: this.shift, reputation: this.reputation,
      score: this.earned + tuning.score.reputation_multiplier * Math.floor(this.reputation),
      upgrades: { ...this.upgrades }, active_upgrades: { ...this.activeUpgrades }, events: [...this.events], ...extra,
    };
  }
}
