import { MockSimV11Adapter } from "./phase2-preview.js";
import { isSpoiled } from "./inventory-view.js";

// Chuyển các tình huống xem thử có sẵn sang payload cá thể. Chỉ chạy trong bản xem Phase 3.
export class MockSimV12Adapter extends MockSimV11Adapter {
  async config() {
    const [base, response] = await Promise.all([super.config(), fetch(new URL("./phase3.preview.json", import.meta.url))]);
    if (!response.ok) throw new Error("Không tải được dữ liệu mẫu Phase 3.");
    this.contract = { ...base, ...await response.json() };
    return this.contract;
  }

  lot() {
    const { fixture, tuning } = this.contract;
    const items = [];
    for (const [kind, amount] of Object.entries(this.plan.ingredients)) {
      for (let i = 0; i < amount; i++) {
        items.push({ id: "I" + (this.day * 100 + items.length + 1), kind, fresh: fixture.lot_values[i % fixture.lot_values.length] });
      }
    }
    if (this.day === 1 && items.length < tuning.gather.hold_capacity) {
      const edge = items.find(({ kind }) => kind === "bong_sung");
      if (edge) {
        edge.fresh = fixture.stock_edge;
        items.push({ id: "I" + (this.day * 100 + items.length + 1), kind: "ca_linh", fresh: fixture.hold_spoiled });
      }
    }
    return items;
  }

  firstPick() {
    return { id: "I" + (this.day * 100 + 99), kind: this.contract.tuning.gather.nodes[0].kind, fresh: this.contract.freshness.initial };
  }

  orderItems(orderId) {
    const lot = this.lot();
    const recipe = this.contract.tuning.menu[this.plan.dishes[0]].recipe;
    const second = orderId === "C2";
    const meals = Object.entries(recipe).sort(([a], [b]) => a.localeCompare(b)).flatMap(([kind, amount]) => {
      const items = lot.filter((item) => item.kind === kind && !isSpoiled(item, this.contract.freshness));
      return items.slice(second ? amount : 0, second ? 2 * amount : amount);
    });
    return meals;
  }

  orderPrice(dishId, orderId) {
    const items = this.orderItems(orderId);
    const listed = super.orderPrice(dishId);
    const average = items.reduce((sum, item) => sum + item.fresh, 0) / items.length;
    return items.length ? Math.floor(listed * average / this.contract.freshness.initial) : listed;
  }

  stockItems(cooked) {
    if (this.day === 3 && this.mode === "day") return [];
    const used = new Set(cooked ? [...this.orderItems("C1"), ...this.orderItems("C2")].map(({ id }) => id) : []);
    const edge = this.contract.fixture.stock_edge;
    return this.lot().filter(({ id }) => !used.has(id)).map((item) => cooked && this.day === 1 && item.fresh === edge
      ? { ...item, fresh: this.contract.fixture.stock_spoiled } : item);
  }

  emit(name, data = {}) {
    if (name === "monster_hit") {
      super.emit(name, { ...data, lost: [this.firstPick()] });
      const spoiled = this.lot().find((item) => isSpoiled(item, this.contract.freshness));
      if (spoiled) super.emit("spoiled", { ...spoiled, location: "hold" });
      return;
    }
    if (name === "faint") data = { ...data, lost: this.lot().reverse() };
    if (name === "gather_end") data = { ...data, inventory: { items: data.reason === "fainted" ? [] : this.lot() } };
    if (name === "cook_started") {
      data = { ...data, items: this.orderItems(data.order_id) };
      const spoiled = this.stockItems(true).find((item) => item.fresh === this.contract.fixture.stock_spoiled);
      if (spoiled) super.emit("spoiled", { ...spoiled, location: "stock" });
    }
    super.emit(name, data);
  }

  gatherSnapshot(tuning) {
    const snapshot = super.gatherSnapshot(tuning);
    const hold = this.step === 0 ? [] : this.step === 1 ? [this.firstPick()] : this.lot();
    return { ...snapshot, hold, hold_count: hold.length };
  }

  quanSnapshot(tuning) {
    const snapshot = super.quanSnapshot(tuning);
    const stock = this.stockItems(this.step > 0);
    const priceDish = (dish) => ({ ...dish, base_price: this.orderPrice(dish.dish_id, dish.order_id) });
    const customers = snapshot.customers.map((customer) => {
      if (customer.id === "C3") {
        const reserved = stock.filter((item) => item.kind === "bong_sung").map(({ id }) => id);
        const waitingForGoi = this.day === 1 && this.step === 0;
        return { ...customer, dish_id: "goi_bong_sung", reserved: waitingForGoi ? reserved : [],
          order_status: waitingForGoi ? "reserved" : "unfulfillable" };
      }
      return { ...customer, reserved: this.step === 0 ? this.orderItems(customer.id).map(({ id }) => id) : [],
        base_price: customer.state === "eating" ? this.orderPrice(customer.dish_id, customer.id) : null };
    });
    return { ...snapshot, stock, customers, hand: snapshot.hand ? priceDish(snapshot.hand) : null,
      stoves: snapshot.stoves.map((stove) => stove.dish ? { ...stove, dish: priceDish(stove.dish) } : stove) };
  }

  state() {
    const snapshot = super.state();
    return snapshot.phase === "shop" ? { ...snapshot, stock: this.stockItems(true) } : snapshot;
  }
}
