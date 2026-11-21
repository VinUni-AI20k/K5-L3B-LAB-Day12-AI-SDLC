// Hình minh họa Canvas gốc. Các số ở đây chỉ mô tả vị trí, màu và hình dáng nét vẽ.
const TAU = Math.PI * 2;
const sand = "#f3c782";
const ink = "#17352f";
const rust = "#be674e";

function sample(n) {
  const v = Math.sin(n * 127.1 + 23.4) * 43758.5453;
  return v - Math.floor(v);
}

function oval(ctx, x, y, rx, ry, color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.ellipse(x, y, rx, ry, 0, 0, TAU);
  ctx.fill();
}

function shape(ctx, color, ...points) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(...points[0]);
  for (const point of points.slice(1)) ctx.lineTo(...point);
  ctx.closePath();
  ctx.fill();
}

function stroke(ctx, color, width, ...points) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.beginPath();
  ctx.moveTo(...points[0]);
  for (const point of points.slice(1)) ctx.lineTo(...point);
  ctx.stroke();
}

function ramp(ctx, y0, y1, ...colors) {
  const gradient = ctx.createLinearGradient(0, y0, 0, Math.max(y0 + 1, y1));
  colors.forEach((color, i) => gradient.addColorStop(i / (colors.length - 1), color));
  return gradient;
}

function nipa(ctx, x, y, size, color, seed) {
  ctx.strokeStyle = color;
  ctx.lineWidth = Math.max(1, size * .034);
  for (let i = 0; i < 6; i++) {
    const dx = (i - 2.5) * size * .32;
    const up = size * (.58 + sample(seed + i) * .38);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.quadraticCurveTo(x + dx * .17, y - up * 1.15, x + dx, y - up);
    ctx.stroke();
    for (let j = 1; j < 6; j++) {
      const t = j / 6;
      const fx = x + dx * t * t;
      const fy = y - up * (2 * t - t * t);
      const feather = size * (.2 - t * .074);
      shape(ctx, color, [fx, fy], [fx + feather * .75, fy + feather], [fx + feather * .15, fy + feather * 1.37]);
      shape(ctx, color, [fx, fy], [fx - feather, fy + feather * .66], [fx - feather * .28, fy + feather]);
    }
  }
}

function house(ctx, x, y, size, color, roofColor, windowColor) {
  ctx.save();
  ctx.translate(x, y);
  ctx.scale(size, size);
  shape(ctx, color, [-1.2, -.76], [1.3, -.76], [1.3, -.23], [-1.2, -.23]);
  shape(ctx, roofColor, [-1.57, -.69], [-.8, -1.38], [.96, -1.38], [1.67, -.69]);
  stroke(ctx, color, .071, [-1.29, -.69], [-.77, -1.27], [.91, -1.27], [1.36, -.74]);
  ctx.fillStyle = windowColor;
  ctx.fillRect(-.84, -.62, .31, .25);
  ctx.fillRect(.06, -.62, .34, .25);
  ctx.fillStyle = color;
  for (const i of [-.98, -.16, .83]) ctx.fillRect(i, -.24, .095, .29);
  stroke(ctx, color, .07, [.94, -.22], [1.46, .02]);
  stroke(ctx, color, .07, [1.23, -.22], [1.73, .02]);
  stroke(ctx, color, .05, [1.32, -.12], [1.51, -.12]);
  ctx.restore();
}

export function shore(ctx, w, h, horizon, drift = 0) {
  ctx.fillStyle = ramp(ctx, 0, horizon, "#b76e82", "#e7a18f", "#ffd7a0");
  ctx.fillRect(0, 0, w, h);
  if (horizon <= 0) return;

  const size = Math.min(w * .06, horizon * .26);
  const sunX = w * .69 - drift * .034;
  const sunY = horizon * .41;
  oval(ctx, sunX, sunY, size * 1.22, size * 1.22, "#fdda9e37");
  oval(ctx, sunX, sunY, size, size, "#ffe0a5");
  for (let i = 0; i < 12; i++) {
    const x = w * sample(i + 4);
    const y = horizon * (.19 + sample(i + 24) * .57);
    const length = 16 + sample(i + 46) * w * .14;
    stroke(ctx, "#ffdec25c", 1 + sample(i + 19), [x, y], [x + length, y]);
  }

  for (let layer = 0; layer < 3; layer++) {
    const color = ["#857c73", "#687c71", "#476b60"][layer];
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.moveTo(0, horizon);
    for (let x = 0; x <= w + 15; x += 15) {
      const phase = (x + drift * (.06 + layer * .04)) * .016;
      const y = horizon - (Math.sin(phase) + Math.cos(phase * .46) + 2.7) * (2 + layer) * (horizon / 142);
      ctx.lineTo(x, y);
    }
    ctx.lineTo(w, horizon);
    ctx.fill();
  }
  const unit = Math.min(28, horizon * .19);
  for (let i = -1; i < 8; i++) {
    const x = i * (w / 7 + 16) - (drift * .19) % (w / 7 + 16);
    if (i % 3 === 1) house(ctx, x + 10, horizon - 3, unit, "#466659", "#696c65", "#c4a683");
    else nipa(ctx, x, horizon - 3, unit * (1.13 + sample(i) * .6), "#3a685b", i);
  }
}

export function river(ctx, w, h, horizon, floor, drift = 0, t = 0, tiers, floodSeason = false) {
  if (tiers) {
    const [middle, deep] = tiers;
    for (const [top, bottom, light, dark] of [
      [horizon, middle, "#b2a673", "#667d57"], [middle, deep, "#4e7558", "#2b5350"], [deep, floor, "#25474a", "#112e37"],
    ]) {
      ctx.fillStyle = ramp(ctx, top, bottom, light, dark);
      ctx.fillRect(0, top, w, bottom - top + 1);
    }
  } else {
    ctx.fillStyle = ramp(ctx, horizon, floor, "#87a385", "#497963", "#24534c", "#163731");
    ctx.fillRect(0, horizon, w, h - horizon);
  }
  ctx.save();
  ctx.beginPath();
  ctx.rect(0, horizon, w, Math.max(0, h - horizon));
  ctx.clip();

  for (let i = -1; i < 8; i++) {
    const x = i * w / 7 - (drift * .1) % (w / 7);
    shape(ctx, "#d6e6a008", [x, horizon], [x + w * .06, horizon],
      [x + w * .26, (h + horizon) * .5], [x + w * .23, (h + horizon) * .56]);
  }
  for (let i = 0; i < 48; i++) {
    const depth = sample(i + 15);
    const x = (sample(i + 41) * (w + 84) - drift * (.15 - depth * .07) + t * (depth > .12 ? 3 : 10)) % (w + 84);
    const y = horizon + (floor - horizon) * depth;
    const length = 5 + sample(i + 80) * (depth > .15 ? 33 : 74);
    stroke(ctx, depth < .2 ? "#f8e9b652" : "#b2d6ba24", depth < .1 ? 1.5 : 1, [x, y], [x + length, y]);
  }
  if (floodSeason) {
    const band = (tiers?.[0] ?? (horizon + (floor - horizon) / 3)) - horizon;
    for (let i = 0; i < 16; i++) {
      const x = (sample(i + 12) * w + t * (5 + sample(i) * 9)) % (w + 20);
      const y = horizon + sample(i + 61) * band;
      const leaf = i % 5 === 0;
      oval(ctx, x, y + Math.sin(t * .9 + i) * 2, leaf ? 5 : 1.6, leaf ? 1.6 : 1.2, leaf ? "#d7b46d80" : "#f6df9f6e");
    }
  }
  for (let i = -1; i < 14; i++) {
    const gap = w / 10 + 17;
    const x = i * gap - (drift * .9) % gap;
    const y = Math.min(h + 6, floor);
    nipa(ctx, x, y, 12 + sample(i + 11) * 26, "#153a33b9", i + 9);
    oval(ctx, x + 9, y - 2, 8 + sample(i) * 13, 3.5, "#244f42");
  }
  ctx.restore();
}

export function dockArt(ctx, x, y, scale) {
  const s = Math.max(9, scale);
  house(ctx, x, y - .16 * s, s * .87, "#7e563c", "#a75240", "#f3b477");
  shape(ctx, "#986644", [x - s * 1.65, y - 4], [x + s * 1.65, y - 4], [x + s * 1.92, y + 1], [x - s * 1.72, y + 1]);
  for (const i of [-1.43, .28, 1.69]) stroke(ctx, "#644b36", 2, [x + i * s, y - 1], [x + i * s, y + 8]);
}

export function plant(ctx, x, y, kind, ready, scale) {
  const s = Math.max(8, scale * .7);
  const lotus = kind === "bong_sung";
  for (const [dx, dy] of [[-7, -1], [5, 1]]) oval(ctx, x + dx, y + dy, s * .71, s * .25, ready ? "#3c7953" : "#457160");
  if (!ready) return;
  for (let i = 0; i < 3; i++) {
    const dx = (i - 1) * s * .57;
    const up = s * (.6 + (i % 2) * .31);
    stroke(ctx, "#427551", 1.6, [x + dx * .4, y + 2], [x + dx, y - up]);
    const [flower, tip] = kind === "keo_neo" ? ["#88b46b", "#d4e491"] : lotus ? ["#e2849b", "#f5b2ba"] : ["#eda857", "#f8cf79"];
    oval(ctx, x + dx, y - up, s * .35, s * .23, flower);
    oval(ctx, x + dx - 1, y - up - s * .15, s * .17, s * .18, tip);
  }
}

function fishBody(ctx, x, y, size, moss) {
  const dark = moss ? "#567549" : "#609a8b";
  const pale = moss ? "#b7c883" : "#cce6ce";
  shape(ctx, dark, [x - size * .42, y], [x - size * .86, y - size * .28], [x - size * .75, y + size * .25]);
  oval(ctx, x, y, size * .58, size * .24, pale);
  shape(ctx, dark, [x - size * .35, y - size * .12], [x - size * .05, y - size * .33], [x + size * .19, y - size * .15]);
  stroke(ctx, dark, 1, [x - size * .31, y + 1], [x + size * .18, y + 1]);
  oval(ctx, x + size * .39, y - size * .06, 1.25, 1.25, "#1e332c");
}

export function school(ctx, x, y, fish, scale, t) {
  const size = Math.max(11, scale * 1.15);
  const moss = fish.kind === "ca_loc";
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate((fish.heading_deg ?? 0) * Math.PI / 180);
  const wave = Math.sin(t * 2 + fish.pos[0]);
  if (fish.kind === "ca_keo") {
    shape(ctx, "#716d83", [-size * .46, 0], [-size, -size * .24], [-size * .88, size * .19]);
    oval(ctx, 0, wave * 1.4, size * .68, size * .16, "#a5a7c1");
    oval(ctx, size * .42, -.8, 1.65, 1.65, "#313342");
  } else fishBody(ctx, 0, wave * 1.4, size, moss);
  if (fish.kind === "ca_linh") {
    fishBody(ctx, -size * .65, size * .48, size * .67, false);
    fishBody(ctx, size * .58, -size * .31, size * .61, false);
  }
  ctx.restore();
}

export function crocodile(ctx, x, y, scale, monster, time) {
  const sway = Math.sin(time * (monster.state === "chase" ? 10 : 4)) * 4;
  const chase = monster.state === "chase";
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate((monster.heading_deg ?? 0) * Math.PI / 180);
  const size = Math.min(1.7, Math.max(.85, scale / 12));
  ctx.scale(size, size);
  ctx.globalAlpha = monster.state === "recoil" ? .58 : 1;
  if (chase) {
    oval(ctx, 0, 0, 42, 14, "#e9645d44");
    stroke(ctx, "#ff9d8075", 1.6, [-65, -8], [-35, -4], [-55, 0]);
  }
  shape(ctx, "#627e53", [-10, -5], [-27, -2], [-46, sway], [-22, 6], [-8, 7]);
  oval(ctx, -4, 0, 18, 8, "#74945f");
  shape(ctx, "#8dae6e", [8,-6], [27,-4], [36,-1], [35,5], [9,6]);
  for (let i = -13; i < 7; i += 5) shape(ctx, "#3a654c", [i,-2], [i+2,-6], [i+4,-2]);
  stroke(ctx, "#264e3a", 1.3, [15, 3], [35, 2]);
  oval(ctx, 13, -3, 3.2, 3.2, chase ? "#ff584d" : "#e9bb6e");
  oval(ctx, 14, -3, 1.1, 1.65, "#243932");
  ctx.restore();
}

export function utSen(ctx, x, y, scale, angle, velocity = [0, 0], t = 0, side = true, diving = true) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(angle);
  const size = Math.min(1.8, Math.max(.83, scale / 12));
  ctx.scale(size, size);
  ctx.lineCap = "round";
  const gait = Math.min(1, Math.hypot(...velocity)) * Math.sin(t * 10) * 3;
  stroke(ctx, "#253b36", 4, [-6, -2], [-11, -4 + gait], [-16, -3 + gait]);
  stroke(ctx, "#263e37", 4, [-6, 2], [-10, 4 - gait], [-16, 3 - gait]);
  oval(ctx, -1, 0, side ? 9 : 7, side ? 4.8 : 7.5, rust);
  stroke(ctx, "#f2b27c", 1, [-7, 1], [3, 1]);
  stroke(ctx, "#b9634c", 3.5, [2, -2], [8, -5 - gait], [13, -4 - gait]);
  stroke(ctx, "#dfa477", 2.3, [12, -4 - gait], [15, -4 - gait]);
  if (!side) stroke(ctx, "#b9634c", 3.5, [2, 2], [6, 6 + gait], [10, 5 + gait]);
  oval(ctx, 4.2, 0, 2.5, 5.1, "#e6c7a6");
  for (let i = -4; i <= 4; i += 2) stroke(ctx, "#65594c", .8, [3.2, i - .7], [5.9, i + .25]);
  oval(ctx, 8.3, -.15, 4.6, 4.7, "#272f2a");
  oval(ctx, 9.6, .45, 3.75, 3.2, "#f1bb89");
  if (diving) {
    oval(ctx, 11, -.45, 2.4, 2.5, "#38534c");
    oval(ctx, 11.7, -.55, 1.2, 1.5, "#b6ded1");
  }
  oval(ctx, -4, 5.1, 5.35, 3.75, "#a59756");
  for (let i = -7; i <= -1; i += 2) {
    stroke(ctx, "#605d3b", .6, [i, 3], [i + 2, 7.6]);
    stroke(ctx, "#d6bb78", .6, [i, 7], [i + 2, 3.7]);
  }
  ctx.restore();
}

function lamp(ctx, x, y, time) {
  const sway = Math.sin(time * 1.5 + x * .025) * 3;
  stroke(ctx, "#c18c55", 1, [x, y], [x + sway, y + 6]);
  oval(ctx, x + sway, y + 8, 12, 11, "#eaa55028");
  oval(ctx, x + sway, y + 8, 6.3, 6.3, "#ffba6638");
  oval(ctx, x + sway, y + 8, 2.7, 3.2, "#ffd998");
}

export function deck(ctx, w, h, x, y, width, height, t) {
  ctx.fillStyle = ramp(ctx, 0, h, "#142632", "#244345", "#183338");
  ctx.fillRect(0, 0, w, h);
  for (let i = 0; i < 42; i++) {
    const rx = (sample(i) * (w + 30) + t * 1.5) % (w + 30) - 15;
    const ry = sample(i + 18) * h;
    stroke(ctx, i % 6 === 0 ? "#e1a86638" : "#8cbbae30", 1.1, [rx, ry], [rx + 12 + sample(i + 77) * 40, ry]);
  }
  ctx.fillStyle = "#3a2c25";
  ctx.fillRect(x - 5, y - 4, width + 10, height + 13);
  ctx.fillStyle = ramp(ctx, y, y + height, "#b17950", "#a46d49", "#825237");
  ctx.fillRect(x, y, width, height);
  const boards = 14;
  for (let i = 1; i < boards; i++) {
    const py = y + height * i / boards;
    stroke(ctx, "#593d2b8f", 1.2, [x, py], [x + width, py]);
    stroke(ctx, "#ecc19445", 1, [x, py + 1], [x + width, py + 1]);
    for (let j = 0; j < 3; j++) {
      const px = x + sample(i * 3 + j + 50) * width * .88;
      const gy = py + sample(i + j + 9) * (height / boards - 4);
      stroke(ctx, "#653f2a5e", 1, [px, gy], [px + width * .12, gy + .5]);
    }
  }
  ctx.strokeStyle = "#d19d67";
  ctx.lineWidth = 2;
  ctx.strokeRect(x, y, width, height);
  for (const postX of [x, x + width]) {
    for (const postY of [y, y + height]) {
      oval(ctx, postX, postY, 5.3, 5.3, "#683f2a");
      oval(ctx, postX, postY - 1, 3.2, 3.2, "#b48155");
    }
  }
  const line = (i) => y - 9 + 12 * Math.sin(i * Math.PI / 9);
  ctx.strokeStyle = "#f9ca846a";
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(x, line(0));
  for (let i = 1; i <= 9; i++) ctx.lineTo(x + i * width / 9, line(i));
  ctx.stroke();
  for (let i = 0; i <= 9; i++) lamp(ctx, x + i * width / 9, line(i), t);
}

export function mealArt(ctx, x, y, size) {
  oval(ctx, x, y, size, size * .73, "#6c4736");
  oval(ctx, x, y - 1, size * .91, size * .61, "#f1ddaf");
  oval(ctx, x - .8, y - 1, size * .51, size * .39, "#8aa25d");
  oval(ctx, x + size * .19, y - size * .14, size * .27, size * .18, rust);
}

export function stoveArt(ctx, x, y, scale, state, t) {
  const s = Math.max(9, .55 * scale);
  ctx.fillStyle = "#5a3c30";
  ctx.fillRect(x - s * 1.22, y - s * .78, s * 2.44, s * 1.75);
  ctx.fillStyle = "#97816b";
  ctx.fillRect(x - s * 1.12, y - s * .92, s * 2.24, s * 1.61);
  oval(ctx, x, y, s * .85, s * .71, "#383a32");
  if (state === "ready") {
    oval(ctx, x, y, s * 1.11, s * .94, "#f6d08168");
    mealArt(ctx, x, y, s * .76);
  } else {
    oval(ctx, x, y, s * .69, s * .53, state === "cooking" ? "#c87345" : "#6b6150");
    oval(ctx, x, y - 1, s * .48, s * .36, state === "cooking" ? "#ebc176" : "#837a64");
    oval(ctx, x, y - 1, s * .18, s * .17, "#65543f");
  }
  if (state === "cooking") {
    for (let i = 0; i < 5; i++) {
      const phase = (t * .65 + i / 5) % 1;
      const color = "rgba(255,226,180," + ((1 - phase) * .38) + ")";
      oval(ctx, x + Math.sin(phase * 5 + i) * s * .31, y - phase * 38 - 4, 2 + phase * 6, 2 + phase * 4, color);
    }
  }
}

export function tableArt(ctx, x, y, scale, customer) {
  const s = Math.max(10, .67 * scale);
  oval(ctx, x, y + 3, s, s, "#604130");
  oval(ctx, x, y, s, s, "#cb9a6d");
  oval(ctx, x, y, s * .87, s * .87, "#956144");
  stroke(ctx, "#b48054", 1, [x - s * .7, y - 2], [x + s * .7, y - 2]);
  oval(ctx, x + s * .3, y - s * .29, s * .15, s * .15, "#edd3aa");
  if (customer) {
    oval(ctx, x, y - s * .89, s * .49, s * .41, "#77946a");
    oval(ctx, x, y - s * .98, s * .29, s * .29, "#efb183");
    if (customer.state === "eating") mealArt(ctx, x, y + s * .15, s * .5);
    else oval(ctx, x, y, s * .24, s * .24, "#f4d9ad");
  }
}

export function coverArt(ctx, w, h) {
  const horizon = h * .56;
  shore(ctx, w, h, horizon);
  river(ctx, w, h, horizon, h);
  const s = Math.min(w / 24, h / 20);
  house(ctx, w * .18, horizon + s * .61, s * 1.16, "#4e5e4a", "#92644d", "#ffd496");
  for (let i = 0; i < 5; i++) {
    nipa(ctx, i * s * .83 - s, horizon + s * .43, s * (1.2 + sample(i + 6) * 1.5), "#35594b", i);
  }
  const boat = [w * .56, horizon + s * .72];
  const [bx, by] = boat;
  shape(ctx, "#4b3b32", [bx - s * 2.9, by - s * .25], [bx + s * 2.8, by - s * .15],
    [bx + s * 2.28, by + s * .32], [bx - s * 2.09, by + s * .35]);
  stroke(ctx, "#eaac79", 1.7, [bx - s * 2.37, by + 1], [bx + s * 2.34, by + 1]);
  oval(ctx, bx + s * .76, by - s * .35, s * .25, s * .32, rust);
  shape(ctx, sand, [bx + s * .32, by - s * .53], [bx + s * .72, by - s * .98], [bx + s * 1.1, by - s * .53]);
  stroke(ctx, "#79543c", Math.max(1.2, s * .061), [bx + s * 1.0, by - s * .61], [bx + s * 1.52, by + s * .8]);
  plant(ctx, w * .88, horizon + s * 1.05, "bong_sung", true, s * 1.2);
  plant(ctx, w * .82, horizon + s * 1.2, "bong_dien_dien", true, s * .8);
  const p = [w * .41, h * .8];
  utSen(ctx, ...p, s * 1.2, .22);
  for (let i = 0; i < 4; i++) {
    ctx.strokeStyle = "#d9e9c8a4";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(p[0] + s * (.7 + i * .2), p[1] - s * (.5 + i * .35), s * (.08 + i * .027), 0, TAU);
    ctx.stroke();
  }
  school(ctx, w * .72, h * .84, { kind: "ca_linh", pos: [0, 0], heading_deg: 172 }, s, 0);
}
