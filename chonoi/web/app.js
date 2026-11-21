import { liveAdapter } from "./adapter.js";
import { createRenderer, findAction } from "./scenes.js";

const $ = (id) => document.getElementById(id);
const preview = new URLSearchParams(location.search).get("preview") === "1";
const adapter = preview ? new (await import("./preview.js")).PreviewAdapter() : liveAdapter;
const controls = [...document.querySelectorAll("button")];
const number = new Intl.NumberFormat("vi-VN");
const decimal = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 1 });
const ingredients = {
  ca_loc: ["Cá lóc", "#a4be7a"],
  ca_linh: ["Cá linh", "#c6e6de"],
  bong_dien_dien: ["Bông điên điển", "#f2c16b"],
  bong_sung: ["Bông súng", "#ee9aa7"],
};
const dishNames = {
  ca_loc_nuong_trui: "Cá lóc nướng trui",
  goi_bong_sung: "Gỏi bông súng",
  lau_ca_linh_dien_dien: "Lẩu cá linh bông điên điển",
};
const movement = {
  KeyW: "north", ArrowUp: "north", KeyS: "south", ArrowDown: "south",
  KeyA: "west", ArrowLeft: "west", KeyD: "east", ArrowRight: "east",
};
const actionKeys = { KeyE: "interact", Space: "catch" };
const down = new Set();
const memo = new Map();
const money = (amount) => number.format(amount) + "k";
const ingredient = (kind) => ingredients[kind]?.[0] ?? kind;
const dishName = (id) => dishNames[id] ?? id;
const percent = (part, total) => Math.min(100, Math.max(0, (100 * part / total) || 0));

let tuning;
let screen = "menu";
let choice;
let snapshot;
let busy = false;
let revision = 0;
let lastTick = -1;
let sessionId;
let toasts = [];
let damageTimer;
let input = Promise.resolve();
const renderer = createRenderer($("cover"), $("world"));

function tell(message = "") {
  write("notice", message);
  $("notice").hidden = !message;
}

function write(id, value) {
  const target = $(id);
  const label = String(value);
  if (target.textContent !== label) target.textContent = label;
}

function element(tag, text = "", className = "") {
  const node = document.createElement(tag);
  node.textContent = text;
  node.className = className;
  return node;
}

function update(id, value, draw) {
  const signature = JSON.stringify(value);
  if (memo.get(id) === signature) return;
  memo.set(id, signature);
  draw($(id));
}

function ticks(seconds) {
  return Math.round(seconds * tuning.tick_hz);
}

function seconds(count) {
  return Math.ceil(count / tuning.tick_hz);
}

function time(count) {
  const left = seconds(count);
  return String(Math.floor(left / 60)).padStart(2, "0") + ":" + String(left % 60).padStart(2, "0");
}

function meter(id, fill, alert = false) {
  const bar = $(id);
  bar.style.width = fill + "%";
  bar.parentElement.classList.toggle("alert", alert);
}

function itemMark(kind) {
  const mark = element("i", "", "ingredient-marker");
  mark.style.setProperty("--ingredient", ingredients[kind]?.[1] ?? "#bfd1be");
  mark.setAttribute("aria-hidden", "true");
  return mark;
}

function itemList(id, counts) {
  update(id, counts, (list) => {
    const rows = Object.entries(counts).map(([kind, count]) => {
      const title = element("dt");
      title.append(itemMark(kind), ingredient(kind));
      const row = element("div", "", count === 0 ? "empty" : "");
      row.append(title, element("dd", number.format(count)));
      return row;
    });
    list.replaceChildren(...rows);
  });
}

function show(next) {
  const changed = screen !== next;
  if (screen === "game" && changed) down.clear();
  screen = next;
  for (const page of ["menu", "game", "result"]) $(page).hidden = page !== next;
  $("to-menu").hidden = next !== "game";
  $("restart").hidden = next !== "game";
  if (changed) {
    const focus = { menu: "menu-title", game: "world", result: "result-title" };
    if (next === "result") $("result-reason").after($("toasts"));
    if (next === "game") $("prompt").before($("toasts"));
    $(focus[next]).focus({ preventScroll: true });
  }
}

function drawGather(state) {
  const p = state.player;
  const config = state.meta;
  const oxy = percent(p.oxygen_ticks, p.oxygen_max_ticks);
  const empty = p.oxygen_ticks === 0 && !p.at_surface;
  write("world-label", (p.at_surface ? "Mặt nước" : "Độ sâu") + " · " + decimal.format(p.pos[1]) + " m");
  write("oxygen-value", seconds(p.oxygen_ticks) + " giây");
  meter("oxygen-bar", oxy, oxy <= 20);
  write("health", "♥".repeat(p.hp) + "♡".repeat(p.hp_max - p.hp));
  $("health").setAttribute("aria-label", p.hp + "/" + p.hp_max + " máu");
  $("oxygen-alert").hidden = !empty;
  if (empty) {
    const remaining = config.choke_interval_ticks - p.zero_oxy_ticks % config.choke_interval_ticks;
    const countdown = Math.ceil(remaining * 10 / tuning.tick_hz) / 10;
    write("oxygen-alert", "Cạn oxy! Ngoi lên thở cái Út ơi! Còn " + decimal.format(countdown) + " giây trước lần mất máu kế.");
  }

  const hold = state.hold;
  const capacity = state.hold_capacity;
  write("bag-capacity", state.hold_count + " / " + capacity);
  update("slots", [hold, capacity], (slots) => {
    slots.replaceChildren(...Array.from({ length: capacity }, (_, i) => {
      const kind = hold[i];
      const cell = element("li", "", kind ? "filled" : "");
      cell.setAttribute("aria-label", kind ? ingredient(kind) : "Ô trống");
      if (kind) {
        cell.title = ingredient(kind);
        cell.append(itemMark(kind));
      }
      return cell;
    }));
  });
  const counts = Object.fromEntries(Object.keys(ingredients).map((kind) => [kind, 0]));
  for (const kind of hold) counts[kind] = (counts[kind] ?? 0) + 1;
  itemList("bag-items", counts);

  const cooldown = ticks(config.catch_cooldown_s);
  meter("catch-bar", cooldown ? 100 - percent(p.catch_cd_ticks, cooldown) : 100);
  write("catch-status", p.catch_cd_ticks > 0 ? "Hồi " + decimal.format(p.catch_cd_ticks / tuning.tick_hz) + " giây" : "Sẵn sàng");
}

function stationCard(title, status, dishId, timer) {
  const card = element("article", "", "station");
  const heading = element("div", "", "station-title");
  heading.append(element("strong", title), element("span", status));
  card.append(heading);
  if (dishId) card.append(element("p", dishName(dishId)));
  if (timer) {
    const caption = element("p", "", "station-timer");
    caption.append(element("b", timer.label), document.createTextNode(" · " + seconds(timer.left) + " giây"));
    const track = element("div", "", "meter");
    const fill = element("i");
    fill.style.width = timer.fill + "%";
    track.append(fill);
    if (timer.threshold !== undefined) {
      const mark = element("span", "", "threshold");
      mark.style.left = timer.threshold * 100 + "%";
      mark.title = "Mốc kiên nhẫn để nhận boa";
      track.append(mark);
    }
    card.append(caption, track);
  }
  return card;
}

function drawQuan(state) {
  write("money", money(state.money));
  write("reputation", decimal.format(state.reputation) + " / " + state.meta.reputation_max.toFixed(1));
  write("score", number.format(state.score));
  write("hand", state.hand ? dishName(state.hand.dish_id) : "Tay trống");

  const counts = Object.fromEntries(Object.keys(ingredients).map((kind) => [kind, state.stock[kind] ?? 0]));
  for (const customer of state.customers) {
    for (const [kind, amount] of Object.entries(customer.reserved ?? {})) counts[kind] -= amount;
  }
  itemList("stock", counts);
  update("dishes", counts, (list) => {
    list.replaceChildren(...Object.entries(tuning.menu).map(([id, recipe]) => {
      const available = Object.entries(recipe.recipe).every(([kind, amount]) => counts[kind] >= amount);
      const row = element("li", "", available ? "available" : "");
      const desc = element("div");
      const requires = Object.entries(recipe.recipe).map(([kind, amount]) => amount + " " + ingredient(kind).toLowerCase()).join(" + ");
      desc.append(element("strong", dishName(id)), element("small", requires + " · " + money(recipe.price)));
      row.append(desc, element("span", available ? "Đủ kho" : "Thiếu kho", "eligibility"));
      return row;
    }));
  });

  update("stations", [state.stoves, state.tables, state.customers], (strip) => {
    const stoveLabels = { idle: "Bếp trống", cooking: "Đang nấu", ready: "Món sẵn sàng" };
    const stoves = state.stoves.map((stove) => {
      const dishId = stove.dish?.dish_id;
      const recipe = tuning.menu[dishId];
      const timer = stove.state === "cooking" && recipe ? {
        label: "Còn nấu", left: stove.cook_ticks_left,
        fill: 100 - percent(stove.cook_ticks_left, ticks(recipe.cook_s)),
      } : null;
      return stationCard("Bếp " + stove.id, stoveLabels[stove.state], dishId, timer);
    });
    const tables = state.tables.map((table) => {
      const c = state.customers.find((customer) => customer.id === table.customer_id);
      if (!c) return stationCard("Bàn " + table.id, "Bàn trống");
      const eating = c.state === "eating";
      const timer = eating ? {
        label: "Đang ăn", left: c.eat_ticks_left, fill: 100 - percent(c.eat_ticks_left, ticks(state.meta.eat_s)),
      } : {
        label: "Kiên nhẫn", left: c.patience_ticks_left, fill: percent(c.patience_ticks_left, ticks(state.meta.patience_s)),
        threshold: state.meta.tip_min_patience_ratio,
      };
      return stationCard("Bàn " + table.id, eating ? "Đã lên món" : "Đang đợi món", c.dish_id, timer);
    });
    strip.replaceChildren(...stoves, ...tables);
  });
}

const gatherReason = {
  docked: "Về bến rồi! Mẻ thu hoạch đã chốt.",
  time: "Hết giờ. Giỏ hiện tại được chốt sang kho.",
  fainted: "Út Sen bị ngất và đánh rơi cả giỏ. Kho chuyển sang buổi tối rỗng.",
};

function endScreen(state) {
  const morning = state.mode === "gather";
  write("result-phase", morning ? "Hết buổi sáng" : "Hết ca tối");
  write("result-title", morning ? "Về lại bến" : choice === "day" ? "Một ngày trọn vẹn" : "Quán đóng cửa");
  write("result-reason", morning ? gatherReason[state.reason] ?? "Buổi sáng đã kết thúc." : "Má Tư chốt sổ ca tối.");
  $("transfer").hidden = !morning;
  $("totals").hidden = morning;
  $("continue").hidden = !morning || choice !== "day";
  if (morning) {
    const end = state.events.findLast((event) => event.name === "gather_end");
    const items = end?.data.inventory?.items ?? {};
    write("inventory-title", Object.keys(items).length ? "Nguyên liệu bàn giao" : "Kho rỗng");
    itemList("transfer-items", items);
    const saved = state.inventory_saved;
    let status = "Chưa ghi được kho.";
    if (preview) status = "Đã chốt kho mẫu cho ca tối.";
    else if (saved) status = "Đã ghi " + state.inventory_file + ".";
    else if (choice === "day") status += " Chọn Mở quán để thử ghi lại.";
    write("file-status", status);
    $("file-status").classList.toggle("warning", !preview && !saved);
  } else {
    write("end-earned", money(state.earned));
    write("end-reputation", decimal.format(state.reputation));
    write("end-score", number.format(state.score));
    const multiplier = tuning.score.reputation_multiplier;
    write("score-formula", "Điểm = doanh thu + " + multiplier + " × phần nguyên của uy tín (⌊" + decimal.format(state.reputation) + "⌋ = " + Math.floor(state.reputation) + ").");
  }
  show("result");
}

function eventMessage(event) {
  const d = event.data;
  switch (event.name) {
    case "gather": return ["Hái được " + d.amount + " " + ingredient(d.kind).toLowerCase() + "!"];
    case "fish_caught": return ["Bắt được " + d.yield + " " + ingredient(d.kind).toLowerCase() + "!"];
    case "hold_full": return ["Giỏ đầy nhóc rồi! Cần " + d.required + " ô, còn " + d.free + ".", "danger"];
    case "oxygen_empty": return ["Ngoi lên thở cái Út ơi!", "danger"];
    case "choke": return ["Ngạt nước! Còn " + d.hp + " máu.", "danger"];
    case "cook_started": return ["Bắc bếp nấu " + dishName(d.dish_id).toLowerCase() + " rồi!"];
    case "dish_ready": return ["Bếp chín rồi, bưng lẹ kẻo nguội!"];
    case "served": return ["Đã dọn " + dishName(d.dish_id).toLowerCase() + " cho bàn " + d.table_id + "."];
    case "paid": return ["Tiền món +" + money(d.base_price) + " · Boa +" + money(d.tip), d.tip > 0 ? "tip" : ""];
    case "customer_left": return [d.reason === "closing" ? "Khách rời bàn vì quán đóng cửa." : "Khách đợi lâu quá, về mất rồi!", "danger"];
    case "no_dish": return ["Kho chưa đủ nguyên liệu để lên món.", "danger"];
    default: return null;
  }
}

function consumeEvents(state) {
  if (state.session_id !== sessionId || state.tick < lastTick) {
    sessionId = state.session_id;
    lastTick = -1;
    toasts = [];
    $("stage").classList.remove("damage");
  }
  const now = performance.now();
  toasts = toasts.filter(({ expires }) => expires > now);
  for (const event of state.events) {
    if (event.tick <= lastTick) continue;
    const message = eventMessage(event);
    if (message) toasts.push({ message, expires: now + 2900 });
    if (event.name === "choke") {
      clearTimeout(damageTimer);
      $("stage").classList.remove("damage");
      void $("stage").offsetWidth;
      $("stage").classList.add("damage");
      damageTimer = setTimeout(() => $("stage").classList.remove("damage"), 560);
    }
  }
  lastTick = state.tick;
  toasts = toasts.slice(-3);
  update("toasts", toasts, (list) => list.replaceChildren(...toasts.map(({ message }) => element("div", ...message))));
}

function display(state) {
  snapshot = state;
  if (state.error) {
    tell("Mô phỏng gặp lỗi. Nhấn R để thử lại.");
    return;
  }
  consumeEvents(state);
  if (state.finished) {
    endScreen(state);
    return;
  }
  const morning = state.mode === "gather";
  $("game").dataset.mode = state.mode;
  write("scene-title", morning ? "Sông Chín Khúc" : "Nhà bè Má Tư");
  write("phase-name", morning ? "Buổi sáng · Lặn và hái" : "Buổi tối · Mở quán");
  write("time", time(state.time_left_ticks));
  if (morning) drawGather(state);
  else drawQuan(state);
  const action = findAction(state);
  $("prompt").hidden = !action;
  if (action) {
    write("prompt-key", action.key);
    write("prompt-text", action.text);
  }
  renderer.state(state, action);
  show("game");
}

function send(frame) {
  input = input.then(() => adapter.input(frame)).catch(() => tell("Chưa gửi được phím đến máy chủ."));
}

function move() {
  const directions = new Set([...down].map((key) => movement[key]));
  const y = snapshot.mode === "quan" ? -1 : 1;
  return [Number(directions.has("east")) - Number(directions.has("west")),
    (Number(directions.has("south")) - Number(directions.has("north"))) * y];
}

function clearKeys() {
  if (!down.size) return;
  down.clear();
  send({ move: [0, 0], interact: false, catch: false });
}

async function transition(next, command) {
  if (busy || !tuning) return;
  busy = true;
  revision++;
  for (const control of controls) control.disabled = true;
  clearKeys();
  try {
    await input;
    await command();
    tell();
    if (next === "menu") show("menu");
    else {
      display(await adapter.state());
      $("world").focus({ preventScroll: true });
    }
  } catch (error) {
    tell(error.message);
  } finally {
    busy = false;
    for (const control of controls) control.disabled = false;
  }
}

const begin = (mode) => transition("game", async () => {
  await adapter.play(mode);
  choice = mode;
});
const menu = () => transition("menu", () => adapter.play("menu"));
const restart = () => transition("game", () => adapter.restart());

$("home-link").addEventListener("click", (event) => {
  event.preventDefault();
  if (screen !== "menu") menu();
});
for (const button of document.querySelectorAll("[data-play]")) {
  button.addEventListener("click", () => begin(button.dataset.play));
}
$("to-menu").addEventListener("click", menu);
$("result-menu").addEventListener("click", menu);
$("restart").addEventListener("click", restart);
$("play-again").addEventListener("click", () => begin(choice));
$("continue").addEventListener("click", () => transition("game", () => adapter.continueDay()));

addEventListener("keydown", (event) => {
  const { code } = event;
  if (busy || screen !== "game" || !(movement[code] || actionKeys[code] || code === "KeyR")) return;
  if (code === "Space" && event.target instanceof HTMLButtonElement) return;
  event.preventDefault();
  if (event.repeat || down.has(code)) return;
  if (code === "KeyR") {
    restart();
    return;
  }
  if (code === "Space" && snapshot.mode === "quan" && !preview) return;
  down.add(code);
  const action = actionKeys[code];
  send(action ? { [action]: true } : { move: move() });
});

addEventListener("keyup", (event) => {
  const { code } = event;
  if (!down.delete(code)) return;
  event.preventDefault();
  const action = actionKeys[code];
  send(action ? { [action]: false } : { move: move() });
});
addEventListener("blur", clearKeys);
document.addEventListener("visibilitychange", () => {
  if (document.hidden) clearKeys();
});
async function poll() {
  if (screen === "game" && !busy) {
    const check = revision;
    try {
      const state = await adapter.state();
      if (revision === check) {
        tell();
        display(state);
      }
    } catch {
      if (revision === check) tell("Mất kết nối đến máy chủ. Đang thử lại…");
    }
  }
  setTimeout(poll, 33);
}

$("preview-label").hidden = !preview;
$("preview-help").hidden = !preview;
try {
  tuning = await adapter.config();
  renderer.configure(tuning);
  for (const control of controls) control.disabled = false;
  poll();
} catch (error) {
  tell(error.message);
}
