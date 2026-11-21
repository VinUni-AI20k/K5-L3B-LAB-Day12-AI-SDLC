import { shore, river, deck, dockArt, plant, school, utSen, stoveArt, tableArt, mealArt, coverArt } from "./art.js";

const tau = Math.PI * 2;
const clamp = (value, min, max) => Math.max(min, Math.min(max, value));
const distance = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);

function nearest(pos, items, radius) {
  let best;
  let limit = radius;
  for (const item of items) {
    const gap = distance(pos, item.pos);
    if (gap <= limit && (!best || gap < limit)) {
      best = item;
      limit = gap;
    }
  }
  return best;
}

// Gợi ý hiển thị dựa trên snapshot. Sim chọn mục tiêu và xử lý hành động.
export function findAction(state) {
  const { player, meta } = state;
  const here = player.pos;
  if (state.mode === "gather") {
    if (distance(here, meta.dock_pos) <= meta.dock_radius) {
      return { key: "E", text: "Cập bến", pos: meta.dock_pos, radius: meta.dock_radius };
    }
    if (player.at_surface) {
      const node = nearest(here, state.nodes.filter((item) => item.ready), meta.interact_radius);
      if (node) return { key: "E", text: "Hái rau", pos: node.pos, radius: .9 };
    } else {
      const fish = nearest(here, state.fish, meta.catch_radius);
      if (fish) return { key: "Space", text: player.catch_cd_ticks ? "Đang hồi chiêu" : "Bắt đàn cá", pos: fish.pos, radius: 1.35 };
    }
    return null;
  }

  const options = [
    ...state.stoves.map((stove) => ({
      pos: stove.pos, label: stove.state === "idle" ? "Tương tác với bếp" : stove.state === "ready" ? "Bưng món" : "Xem bếp",
    })),
    ...state.tables.map((table) => ({
      pos: table.pos, label: state.hand?.order_id === table.customer_id ? "Phục vụ bàn " + table.id : "Tương tác với bàn",
    })),
  ];
  const item = nearest(here, options, meta.interact_radius);
  return item ? { key: "E", text: item.label, pos: item.pos, radius: .85 } : null;
}

function fit(canvas) {
  const w = canvas.clientWidth;
  const h = canvas.clientHeight;
  if (!w || !h) return null;
  const ratio = Math.min(devicePixelRatio || 1, 2);
  const width = Math.round(w * ratio);
  const height = Math.round(h * ratio);
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width;
    canvas.height = height;
  }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  return { ctx, w, h };
}

function label(ctx, name, x, y, options = {}) {
  ctx.font = "700 11px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  const width = ctx.measureText(name).width + 12;
  ctx.fillStyle = options.background ?? "#192c24e8";
  ctx.beginPath();
  ctx.roundRect(x - width / 2, y - 9, width, 18, 5);
  ctx.fill();
  ctx.fillStyle = options.color ?? "#fff0d4";
  ctx.fillText(name, x, y);
}

function ring(ctx, x, y, radius, color, dashed = false) {
  ctx.strokeStyle = color;
  ctx.lineWidth = 1.7;
  ctx.setLineDash(dashed ? [5, 4] : []);
  ctx.beginPath();
  ctx.arc(x, y, radius, 0, tau);
  ctx.stroke();
  ctx.setLineDash([]);
}

function progressRing(ctx, x, y, size, fraction) {
  ring(ctx, x, y, size, "#213b36");
  ctx.strokeStyle = "#ffd390";
  ctx.beginPath();
  ctx.arc(x, y, size, -Math.PI / 2, -Math.PI / 2 + clamp(fraction, 0, 1) * tau);
  ctx.stroke();
}

function highlight(ctx, action, x, y, scale, w, h) {
  if (!action) return;
  const ax = x(action.pos[0]);
  const ay = y(action.pos[1]);
  ring(ctx, ax, ay, Math.max(13, action.radius * scale), "#ffdc8d", true);
  label(ctx, action.key, clamp(ax, 24, w - 24), clamp(ay - Math.max(25, action.radius * scale + 12), 13, h - 15),
    { color: "#302419", background: "#f4bd70" });
}

function worldGather(ctx, w, h, state, action, t, hz) {
  const { meta, player } = state;
  const [[left, right], [surface, bottom]] = [meta.bounds.x, meta.bounds.d];
  const depth = bottom - surface;
  const preferredHorizon = h * .29;
  // Vùng nhìn ngang hẹp hơn lòng sông và bám player.x khi rời rìa.
  const scale = Math.max(w / Math.min(65, right - left), (h - preferredHorizon - 24) / depth);
  const span = w / scale;
  const viewX = clamp(player.pos[0] - span / 2, left - 3, right + 3 - span);
  const minHorizon = h - 23 - depth * scale;
  const horizon = Math.min(preferredHorizon, Math.max(minHorizon, h - 30 - (player.pos[1] - surface) * scale));
  const x = (pos) => (pos - viewX) * scale;
  const y = (pos) => horizon + (pos - surface) * scale;

  shore(ctx, w, h, horizon, viewX * scale, t);
  river(ctx, w, h, horizon, y(bottom), viewX * scale, t);
  ctx.fillStyle = "#b8e3a063";
  ctx.fillRect(0, horizon, w, meta.surface_depth * scale);
  ctx.fillStyle = "#d7dcb2";
  ctx.fillRect(0, horizon - 1, w, 1.5);
  if (y(bottom) < h) {
    ctx.fillStyle = "#12312e";
    ctx.fillRect(0, y(bottom), w, h - y(bottom));
  }

  const [dockX, dockD] = meta.dock_pos;
  ring(ctx, x(dockX), y(dockD), scale * meta.dock_radius, "#ffdfa7b5", true);
  dockArt(ctx, x(dockX), y(dockD), scale);
  if (x(dockX) >= 0 && x(dockX) < w) label(ctx, "Bến", Math.max(25, x(dockX)), y(dockD) + 28);

  for (const node of state.nodes) {
    const nx = x(node.pos[0]);
    if (nx < -35 || nx > w + 35) continue;
    const ny = y(node.pos[1]);
    plant(ctx, nx, ny, node.kind, node.ready, scale);
    label(ctx, node.id, nx, ny + 15);
    if (!node.ready) {
      const seconds = Math.ceil(node.regrow_ticks / hz);
      progressRing(ctx, nx, ny - 20, 10, 1 - node.regrow_ticks / (meta.regrow_s * hz));
      ctx.font = "700 9px system-ui";
      ctx.fillStyle = "#fff2d7";
      ctx.fillText(String(seconds), nx, ny - 20);
    }
  }
  for (const fish of state.fish) {
    const fx = x(fish.pos[0]);
    const fy = y(fish.pos[1]);
    if (fx < -45 || fx > w + 45) continue;
    school(ctx, fx, fy, fish, scale, t);
    label(ctx, fish.id, fx, fy + 16);
  }
  highlight(ctx, action, x, y, scale, w, h);
  const [px, pd] = player.pos;
  const p = [x(px), y(pd)];
  if (!player.at_surface) {
    if (player.catch_cd_ticks === 0) ring(ctx, ...p, scale * meta.catch_radius, "#e4eeba49");
    const motion = Math.hypot(...(player.vel ?? [0, 0]));
    if (motion > .1) {
      for (let i = 0; i < 4; i++) {
        const life = (t + i / 4) % 1;
        ring(ctx, p[0] + Math.sin(i + t * 5) * 7, p[1] - 7 - life * 31, 2 + life * 3, "#dcf3de8a");
      }
    }
  }
  utSen(ctx, ...p, scale, player.heading_deg * Math.PI / 180, player.vel, t, true, !player.at_surface);
}

function worldQuan(ctx, w, h, state, action, t) {
  const [[left, right], [south, north]] = [state.meta.bounds.x, state.meta.bounds.z];
  const pad = Math.min(w, h) * .15;
  const scale = Math.min((w - 2 * pad) / (right - left), (h - 1.5 * pad) / (north - south));
  const width = (right - left) * scale;
  const height = (north - south) * scale;
  const ox = (w - width) / 2;
  const oy = (h - height) / 2;
  const x = (pos) => ox + (pos - left) * scale;
  const y = (pos) => oy + (north - pos) * scale;
  deck(ctx, w, h, ox, oy, width, height, t);
  for (const stove of state.stoves) {
    const sx = x(stove.pos[0]);
    const sy = y(stove.pos[1]);
    stoveArt(ctx, sx, sy, scale, stove.state, t);
    label(ctx, "Bếp " + stove.id, sx, sy + .63 * scale + 11);
  }
  for (const table of state.tables) {
    const customer = state.customers.find((item) => item.id === table.customer_id);
    const tx = x(table.pos[0]);
    const ty = y(table.pos[1]);
    tableArt(ctx, tx, ty, scale, customer);
    label(ctx, "Bàn " + table.id, tx, ty + .65 * scale + 12);
  }

  highlight(ctx, action, x, y, scale, w, h);
  const p = state.player;
  const px = x(p.pos[0]);
  const py = y(p.pos[1]);
  const [vx, vz] = p.vel ?? [0, 0];
  const heading = vx || vz ? Math.atan2(-vz, vx) : -Math.PI / 2;
  utSen(ctx, px, py, scale * .48, heading, p.vel, t, false, false);
  if (state.hand) mealArt(ctx, px, py - 22, 8);
}

export function createRenderer(cover, canvas) {
  let current;
  let action;
  let tuning;
  const reducedMotion = matchMedia("(prefers-reduced-motion: reduce)");

  function drawCover() {
    const frame = fit(cover);
    if (frame) coverArt(frame.ctx, frame.w, frame.h);
  }

  function draw(ms) {
    if (current && tuning) {
      const frame = fit(canvas);
      if (frame) {
        const { ctx, w, h } = frame;
        const t = reducedMotion.matches ? 0 : ms / 1000;
        if (current.mode === "gather") worldGather(ctx, w, h, current, action, t, tuning.tick_hz);
        else worldQuan(ctx, w, h, current, action, t);
      }
    }
    requestAnimationFrame(draw);
  }

  new ResizeObserver(drawCover).observe(cover);
  requestAnimationFrame(draw);
  return {
    configure(config) { tuning = config; },
    state(snapshot, target) {
      action = target;
      const previous = current;
      current = snapshot;
      // Starter quán chưa có vel. Khoảng dịch chuyển giữa hai snapshot chỉ dùng để vẽ bước chân.
      if (!snapshot.player.vel && previous && previous.session_id === snapshot.session_id) {
        const elapsed = (snapshot.tick - previous.tick) / tuning.tick_hz;
        const velocity = elapsed > 0
          ? snapshot.player.pos.map((pos, axis) => (pos - previous.player.pos[axis]) / elapsed)
          : previous.player.vel;
        current = { ...snapshot, player: { ...snapshot.player, vel: velocity } };
      }
    },
  };
}
