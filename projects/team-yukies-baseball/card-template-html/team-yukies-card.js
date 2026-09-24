let PLAYERS = {};
const DEFAULT_CSV_PATH = "../PLAYER_RATINGS.csv";
const PLAYER_IMAGE_DATA = { ...(window.TEAM_YUKIES_PLAYER_IMAGES || {}) };

const FIELDING_LIST = [
  ["C",0,0,"def_c"], ["1B",0,1,"def_1b"], ["2B",0,2,"def_2b"], ["3B",0,3,"def_3b"], ["SS",0,4,"def_ss"],
  ["LF",1,0,"def_lf"], ["CF",1,1,"def_cf"], ["RF",1,2,"def_rf"], ["P",1,3,null]
];

const FIELDING_NODE = {
  LF:["fn-lf","def_lf"], CF:["fn-cf","def_cf"], RF:["fn-rf","def_rf"],
  SS:["fn-ss","def_ss"], "2B":["fn-2b","def_2b"], "3B":["fn-3b","def_3b"],
  "1B":["fn-1b","def_1b"], C:["fn-c","def_c"]
};

const PITCHES = [
  ["4SEAM",0,0,"pitch_four_seam"], ["SINKER",0,1,"pitch_sinker"], ["CUTTER",0,2,"pitch_cutter"],
  ["SLIDER",0,3,"pitch_slider"], ["CHANGEUP",0,4,"pitch_changeup"],
  ["CURVE",1,0,"pitch_curveball"], ["SPLITTER",1,1,"pitch_splitter"], ["SWEEPER",1,2,"pitch_sweeper"],
  ["SLURVE",1,3,"pitch_slurve"], ["KNUCKLE",1,4,"pitch_knuckleball"]
];

function val(v) {
  return v === undefined || v === null || v === "" ? null : Number(v);
}
function rated(v) { return val(v) !== null; }
function pct(v) {
  const n = val(v);
  if (n === null) return 0;
  return ((Math.max(20, Math.min(80, n)) - 20) / 60) * 100;
}
function fillText(root, selector, value) {
  const el = root.querySelector(selector);
  if (el) el.textContent = value ?? "";
}

function handLabel(value) {
  const v = String(value ?? "").trim().toUpperCase();
  if (v === "RIGHT" || v === "R") return "Right";
  if (v === "LEFT" || v === "L") return "Left";
  if (v === "SWITCH" || v === "S") return "Switch";
  return value || "-";
}

function profileLines(p) {
  const height = p.height_cm ?? "-";
  const weight = p.weight_kg ?? "-";
  const birthday = p.birthday || "-";
  const birthplace = p.birth_place || "-";
  const traits = [p.trait_1, p.trait_2, p.trait_3].filter(Boolean);

  return [
    `${height}cm | ${weight}kg | Bats: ${handLabel(p.bats)} | Throws: ${handLabel(p.throws)}`,
    `${birthday} | ${birthplace}`,
    traits.length ? traits.join(" | ") : "-"
  ];
}

function renderProfile(root, p) {
  const host = root.querySelector("#back-profile");
  const lines = profileLines(p);
  const elements = host.querySelectorAll(".back__profile-line");

  elements.forEach((el, i) => {
    el.textContent = lines[i] ?? "";
  });
}

function primaryDefense(p) {
  const key = {
    C:"def_c", "1B":"def_1b", "2B":"def_2b", "3B":"def_3b", SS:"def_ss",
    LF:"def_lf", CF:"def_cf", RF:"def_rf"
  }[p.primary_position];
  return key ? val(p[key]) : null;
}

function renderRatingBlock(root, values) {
  const valuesHost = root.querySelector(".rating-values");
  const barsHost = root.querySelector(".rating-bars");

  valuesHost.replaceChildren();
  barsHost.replaceChildren();

  values.forEach(v => {
    const ve = document.createElement("div");
    ve.className = "rating-value";
    ve.textContent = rated(v) ? v : "-";
    valuesHost.appendChild(ve);

    const bar = document.createElement("div");
    bar.className = "rating-bar";

    const fill = document.createElement("div");
    fill.className = "rating-fill";
    fill.style.setProperty("--pct", `${pct(v)}%`);

    bar.appendChild(fill);
    barsHost.appendChild(bar);
  });
}

function renderFront(root, p) {
  const isPitcher = p.player_type === "PITCHER";

  root.querySelector("#front-batter-overlay").hidden = isPitcher;
  root.querySelector("#front-pitcher-overlay").hidden = !isPitcher;

  const playerImg = root.querySelector("#front-player");
  if (p.player_image) {
    playerImg.hidden = false;
    playerImg.src = p.player_image;
  } else {
    playerImg.hidden = true;
    playerImg.removeAttribute("src");
  }

  fillText(root, ".front__ovr", p.overall);
  fillText(root, ".front__position", p.primary_position);
  fillText(root, ".front__number", p.uniform_number);
  fillText(root, ".front__first", p.display_first_name);
  fillText(root, ".front__last", p.display_last_name);
  fillText(root, ".front__serial", p.serial);

  const statHost = root.querySelector(".front__stats");
  statHost.replaceChildren();

  const stats = isPitcher
    ? [p.stuff, p.movement, p.control, p.command, p.stamina, p.fielding]
    : [p.contact, p.power, p.gap_power, p.discipline, p.speed, p.fielding];

  stats.forEach(v => {
    const e = document.createElement("div");
    e.className = "front__stat";
    e.textContent = rated(v) ? v : "-";
    statHost.appendChild(e);
  });
}

function renderFielding(root, p) {
  const list = root.querySelector(".fielding-list");
  const diamond = root.querySelector(".fielding-diamond");

  list.replaceChildren();
  diamond.replaceChildren();

  FIELDING_LIST.forEach(([pos,col,row,key]) => {
    const v = key ? val(p[key]) : null;
    const primary = pos === p.primary_position;

    const slot = document.createElement("div");
    slot.className = `fielding-slot ${primary ? "is-primary" : rated(v) ? "is-rated" : "is-unrated"}`;
    slot.dataset.col = col;
    slot.dataset.row = row;
    slot.innerHTML =
      `<div class="fielding-label">${pos}</div>` +
      `<div class="fielding-value">${rated(v) ? v : "-"}</div>`;

    list.appendChild(slot);
  });

  Object.entries(FIELDING_NODE).forEach(([pos,[cls,key]]) => {
    const v = val(p[key]);
    if (!rated(v)) return;

    const node = document.createElement("div");
    node.className = `fielding-node ${cls}${pos === p.primary_position ? " is-primary" : ""}`;
    node.innerHTML = `<div>${pos}</div><div>${v}</div>`;
    diamond.appendChild(node);
  });
}

function renderPitches(root, p) {
  const host = root.querySelector(".pitch-list");
  host.replaceChildren();

  PITCHES.forEach(([name,col,row,key]) => {
    const v = val(p[key]);
    const slot = document.createElement("div");
    slot.className = `pitch-slot ${rated(v) ? "is-rated" : "is-unrated"}`;
    slot.dataset.col = col;
    slot.dataset.row = row;
    slot.innerHTML =
      `<div class="pitch-label">${name}</div>` +
      `<div class="pitch-value">${rated(v) ? v : "-"}</div>`;

    host.appendChild(slot);
  });

  fillText(root, ".velocity", p.velocity_kmh);
}

function resetBackState(root) {
  root.querySelector(".fielding-list").replaceChildren();
  root.querySelector(".fielding-diamond").replaceChildren();
  root.querySelector(".pitch-list").replaceChildren();

  fillText(root, ".velocity", "");

  root.querySelector(".fielding-list").hidden = true;
  root.querySelector(".fielding-diamond").hidden = true;
  root.querySelector(".pitch-list").hidden = true;
  root.querySelector(".velocity").hidden = true;
}

function renderBack(root, p) {
  resetBackState(root);

  const isPitcher = p.player_type === "PITCHER";

  root.querySelector("#back-batter-overlay").hidden = isPitcher;
  root.querySelector("#back-pitcher-overlay").hidden = !isPitcher;

  fillText(root, ".back__first", p.display_first_name);
  fillText(root, ".back__last", p.display_last_name);
  fillText(root, ".back__position", p.primary_position);
  fillText(root, ".back__number", p.uniform_number);

  renderProfile(root, p);

  fillText(root, ".back__report", p.scouting_report);
  fillText(root, ".back__serial", p.serial);

  if (isPitcher) {
    renderRatingBlock(root, [
      p.stuff, p.movement, p.control, p.command,
      p.stamina, p.holding, p.pitchability, p.fielding
    ]);

    root.querySelector(".pitch-list").hidden = false;
    root.querySelector(".velocity").hidden = false;
    renderPitches(root, p);
  } else {
    renderRatingBlock(root, [
      p.contact, p.power, p.gap_power, p.discipline,
      p.baserunning, p.stealing, p.arm, p.fielding
    ]);

    root.querySelector(".fielding-list").hidden = false;
    root.querySelector(".fielding-diamond").hidden = false;
    renderFielding(root, p);
  }
}

function renderPlayer(playerId) {
  const p = PLAYERS[playerId];
  if (!p) return;

  renderFront(document.querySelector("#front-card"), p);
  renderBack(document.querySelector("#back-card"), p);
}

/* ---------------------------------------------------------
   v8 preview UI / export
   --------------------------------------------------------- */

function playerDisplayName(p) {
  return [p.display_first_name, p.display_last_name].filter(Boolean).join(" ")
    || p.character_name
    || p.player_id;
}

function renderPlayerList() {
  const host = document.querySelector("#player-list");
  const count = document.querySelector("#player-count");
  if (!host) return;

  const activeId = document.querySelector("#player-select")?.value || "";
  host.replaceChildren();

  const players = Object.values(PLAYERS);
  if (count) count.textContent = String(players.length);

  players.forEach(p => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "player-list__item" + (p.player_id === activeId ? " is-active" : "");
    button.dataset.playerId = p.player_id;
    button.setAttribute("role", "option");
    button.setAttribute("aria-selected", p.player_id === activeId ? "true" : "false");

    const name = document.createElement("span");
    name.className = "player-list__name";
    name.textContent = playerDisplayName(p);

    const meta = document.createElement("span");
    meta.className = "player-list__meta";
    meta.textContent = [p.primary_position, p.uniform_number != null ? `#${p.uniform_number}` : null, p.serial]
      .filter(Boolean).join(" · ");

    button.append(name, meta);
    button.addEventListener("click", () => selectPlayer(p.player_id));
    host.appendChild(button);
  });
}

function selectPlayer(playerId) {
  if (!PLAYERS[playerId]) return;
  const select = document.querySelector("#player-select");
  select.value = playerId;
  renderPlayer(playerId);
  renderPlayerList();
}

function setPreviewScale(percent) {
  const value = Math.max(35, Math.min(100, Number(percent) || 55));
  document.documentElement.style.setProperty("--preview-scale", String(value / 100));
  const output = document.querySelector("#preview-scale-value");
  if (output) output.value = `${value}%`;
  try { localStorage.setItem("team-yukies-preview-scale", String(value)); } catch {}
}

function initPreviewScale() {
  const input = document.querySelector("#preview-scale");
  if (!input) return;

  let value = Number(input.value || 55);
  try {
    const saved = Number(localStorage.getItem("team-yukies-preview-scale"));
    if (Number.isFinite(saved) && saved >= 35 && saved <= 100) value = saved;
  } catch {}

  input.value = String(value);
  setPreviewScale(value);
  input.addEventListener("input", () => setPreviewScale(input.value));
}

function setExportStatus(message) {
  const el = document.querySelector("#export-status");
  if (el) el.textContent = message || "";
}

async function waitForCardAssets(card) {
  if (document.fonts?.ready) await document.fonts.ready;

  const images = [...card.querySelectorAll("img")].filter(img => !img.hidden && img.src);
  await Promise.all(images.map(img => {
    if (img.complete && img.naturalWidth > 0) return Promise.resolve();
    return new Promise(resolve => {
      img.addEventListener("load", resolve, { once:true });
      img.addEventListener("error", resolve, { once:true });
    });
  }));
}

function triggerDownload(dataUrl, filename) {
  const link = document.createElement("a");
  link.download = filename;
  link.href = dataUrl;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

async function exportCard(card, filename) {
  if (!window.htmlToImage?.toPng) {
    throw new Error("PNG export library failed to load");
  }

  await waitForCardAssets(card);

  const dataUrl = await window.htmlToImage.toPng(card, {
    cacheBust: true,
    pixelRatio: 1,
    width: 900,
    height: 1260,
    canvasWidth: 900,
    canvasHeight: 1260,
    backgroundColor: null,
    style: {
      margin: "0",
      transform: "none"
    }
  });

  triggerDownload(dataUrl, filename);
}

async function exportCurrentCards() {
  const player = currentPlayer();
  if (!player) throw new Error("No player selected");
  if (!player.serial) throw new Error("Selected player has no serial number");

  const button = document.querySelector("#save-cards");
  if (button) button.disabled = true;
  setExportStatus("PNG 생성 중…");

  try {
    await exportCard(document.querySelector("#front-card"), `${player.serial}_front.png`);
    await new Promise(resolve => setTimeout(resolve, 150));
    await exportCard(document.querySelector("#back-card"), `${player.serial}_back.png`);
    setExportStatus("앞/뒤 저장 완료");
  } finally {
    if (button) button.disabled = false;
  }
}

function initExportControls() {
  const button = document.querySelector("#save-cards");
  if (!button) return;

  button.addEventListener("click", async () => {
    try {
      await exportCurrentCards();
    } catch (error) {
      console.error(error);
      setExportStatus(`저장 실패: ${error.message}`);
    }
  });
}

/* ---------------------------------------------------------
   CSV
   --------------------------------------------------------- */

function parseCSVLine(line) {
  const out = [];
  let cur = "";
  let quoted = false;

  for (let i = 0; i < line.length; i++) {
    const c = line[i];

    if (c === '"') {
      if (quoted && line[i + 1] === '"') {
        cur += '"';
        i++;
      } else {
        quoted = !quoted;
      }
    } else if (c === "," && !quoted) {
      out.push(cur);
      cur = "";
    } else {
      cur += c;
    }
  }

  out.push(cur);
  return out;
}

function parseCSV(text) {
  const lines = text
    .replace(/^\uFEFF/, "")
    .split(/\r?\n/)
    .filter(line => line.trim() !== "");

  if (!lines.length) return [];

  const headers = parseCSVLine(lines[0]).map(h => h.trim());

  return lines.slice(1).map(line => {
    const values = parseCSVLine(line);
    const row = {};
    headers.forEach((h, i) => row[h] = values[i] ?? "");
    return row;
  });
}

function first(row, aliases) {
  for (const key of aliases) {
    if (Object.prototype.hasOwnProperty.call(row, key) && row[key] !== "") {
      return row[key];
    }
  }
  return "";
}

function numberOrNull(v) {
  if (v === "" || v === null || v === undefined) return null;
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
}

const POSITION_CODE = Object.freeze({
  DH: "0", SP: "1", RP: "1", CL: "1", P: "1",
  C: "2", "1B": "3", "2B": "4", "3B": "5", SS: "6",
  LF: "7", CF: "8", RF: "9"
});

const FIELDING_WEIGHTS = Object.freeze({
  C:  [0.60, 0.40],
  "1B":[0.90, 0.10],
  "2B":[0.80, 0.20],
  "3B":[0.65, 0.35],
  SS:  [0.70, 0.30],
  LF:  [0.85, 0.15],
  CF:  [0.85, 0.15],
  RF:  [0.65, 0.35]
});

const BATTER_OVR_WEIGHTS = Object.freeze({
  C:  {contact:.16,power:.16,gap_power:.08,discipline:.15,baserunning:.04,stealing:.02,arm:.14,fielding:.25},
  "1B":{contact:.18,power:.26,gap_power:.12,discipline:.19,baserunning:.06,stealing:.02,arm:.04,fielding:.13},
  "2B":{contact:.20,power:.14,gap_power:.10,discipline:.18,baserunning:.09,stealing:.05,arm:.07,fielding:.17},
  "3B":{contact:.20,power:.25,gap_power:.12,discipline:.18,baserunning:.03,stealing:.02,arm:.08,fielding:.12},
  SS:  {contact:.18,power:.12,gap_power:.08,discipline:.16,baserunning:.08,stealing:.05,arm:.10,fielding:.23},
  LF:  {contact:.18,power:.25,gap_power:.12,discipline:.19,baserunning:.07,stealing:.03,arm:.05,fielding:.11},
  CF:  {contact:.18,power:.14,gap_power:.10,discipline:.16,baserunning:.10,stealing:.06,arm:.07,fielding:.19},
  RF:  {contact:.18,power:.24,gap_power:.12,discipline:.18,baserunning:.05,stealing:.02,arm:.10,fielding:.11},
  DH:  {contact:.22,power:.28,gap_power:.14,discipline:.22,baserunning:.08,stealing:.06,arm:0,fielding:0}
});

const PITCHER_OVR_WEIGHTS = Object.freeze({
  SP: {stuff:.20,movement:.15,control:.14,command:.16,stamina:.15,holding:.05,pitchability:.10,fielding:.05},
  RP: {stuff:.27,movement:.17,control:.14,command:.17,stamina:.05,holding:.05,pitchability:.10,fielding:.05},
  CL: {stuff:.27,movement:.17,control:.14,command:.17,stamina:.05,holding:.05,pitchability:.10,fielding:.05}
});

function clampRating(v) {
  return Math.max(20, Math.min(80, Math.round(v)));
}

function weightedRating(p, weights) {
  let total = 0;
  for (const [key, weight] of Object.entries(weights)) {
    if (weight === 0) continue;
    const value = val(p[key]);
    if (value === null) return null;
    total += value * weight;
  }
  return clampRating(total);
}

function recalcBatterDerived(p) {
  const br = val(p.baserunning);
  const st = val(p.stealing);
  const arm = val(p.arm);
  const primary = primaryDefense(p);

  p.speed = br !== null && st !== null
    ? clampRating(br * 0.60 + st * 0.40)
    : null;

  if (p.primary_position === "DH") {
    p.fielding = null;
  } else {
    const fieldWeights = FIELDING_WEIGHTS[p.primary_position];
    p.fielding = fieldWeights && arm !== null && primary !== null
      ? clampRating(primary * fieldWeights[0] + arm * fieldWeights[1])
      : null;
  }

  const weights = BATTER_OVR_WEIGHTS[p.primary_position];
  p.overall = weights ? weightedRating(p, weights) : null;
}

function recalcPitcherOverall(p) {
  const role = PITCHER_OVR_WEIGHTS[p.primary_position] ? p.primary_position : "SP";
  p.overall = weightedRating(p, PITCHER_OVR_WEIGHTS[role]);
}

function serialInteger(value, min, max, width) {
  const n = Number(value);
  if (!Number.isInteger(n) || n < min || n > max) return null;
  return String(n).padStart(width, "0");
}

function recalcSerial(p) {
  p.serial = "";

  const code = String(p.team_code || "").trim().toUpperCase();
  const year = serialInteger(p.card_year, 0, 99, 2);
  const grade = serialInteger(p.card_grade, 0, 9, 1);
  const theme = serialInteger(p.card_theme, 0, 9, 1);
  const themeIndex = serialInteger(p.theme_index, 1, 99, 2);
  const number = serialInteger(p.uniform_number, 0, 99, 2);
  const position = POSITION_CODE[p.primary_position];

  if (/^[A-Z0-9]{2}$/.test(code) && year && grade && theme &&
      themeIndex && number && position !== undefined) {
    p.serial = `${code}${year}${grade}${theme}${themeIndex}${number}${position}`;
  }
}

function recalcDerivedFields(p) {
  if (p.player_type === "BATTER") recalcBatterDerived(p);
  else if (p.player_type === "PITCHER") recalcPitcherOverall(p);
  else p.overall = null;

  recalcSerial(p);
}

function normalizeCSVRow(row) {
  const p = { ...row };

  p.player_id = first(row, ["player_id", "선수 ID", "선수ID"]) || `csv_${crypto.randomUUID()}`;

  p.display_first_name = first(row, ["display_first_name", "first_name", "이름"]);
  p.display_last_name = first(row, ["display_last_name", "last_name", "성"]);

  p.height_cm = numberOrNull(first(row, ["height_cm", "height", "키"]));
  p.weight_kg = numberOrNull(first(row, ["weight_kg", "weight", "몸무게"]));

  p.bats = first(row, ["bats", "bat_hand", "타격 손", "타격손"]);
  p.throws = first(row, ["throws", "throw_hand", "투구 손", "투구손"]);

  p.birthday = first(row, ["birthday", "birth_date", "생일"]);
  p.birth_place = first(row, ["birth_place", "birthplace", "태어난 곳", "태어난곳"]);

  p.trait_1 = first(row, ["trait_1", "player_trait_1", "선수 특징 1", "선수특징1"]);
  p.trait_2 = first(row, ["trait_2", "player_trait_2", "선수 특징 2", "선수특징2"]);
  p.trait_3 = first(row, ["trait_3", "player_trait_3", "선수 특징 3", "선수특징3"]);

  [
    "overall","uniform_number","card_year","card_grade","card_theme","theme_index",
    "contact","power","gap_power","discipline","speed","fielding","baserunning","stealing","arm",
    "def_c","def_1b","def_2b","def_3b","def_ss","def_lf","def_cf","def_rf",
    "stuff","movement","control","command","stamina","holding","pitchability",
    "velocity_kmh","pitch_four_seam","pitch_sinker","pitch_cutter","pitch_slider",
    "pitch_changeup","pitch_curveball","pitch_splitter","pitch_sweeper","pitch_slurve",
    "pitch_knuckleball"
  ].forEach(key => {
    if (Object.prototype.hasOwnProperty.call(p, key)) {
      p[key] = numberOrNull(p[key]);
    }
  });

  recalcDerivedFields(p);
  return p;
}

function rebuildPlayerSelect(preferredId = null) {
  const select = document.querySelector("#player-select");
  const previous = preferredId || select.value;

  select.replaceChildren();

  Object.values(PLAYERS).forEach(p => {
    const opt = document.createElement("option");
    opt.value = p.player_id;
    opt.textContent =
      [p.display_first_name, p.display_last_name].filter(Boolean).join(" ")
      || p.character_name
      || p.player_id;
    select.appendChild(opt);
  });

  if (previous && PLAYERS[previous]) select.value = previous;
  else if (select.options.length) select.selectedIndex = 0;

  renderPlayerList();
}

function installPlayers(rows, sourceLabel, preferredId = null) {
  const normalized = rows.map(normalizeCSVRow);
  PLAYERS = {};

  normalized.forEach(p => {
    if (!p.player_id) return;
    PLAYERS[p.player_id] = p;
  });

  rebuildPlayerSelect(preferredId || normalized[0]?.player_id || null);

  const selected = document.querySelector("#player-select").value;
  if (selected) renderPlayer(selected);

  document.querySelector("#csv-status").textContent =
    `${sourceLabel}: ${normalized.length} player(s) loaded`;

  return normalized;
}

async function loadCSVFile(file) {
  const text = await file.text();
  return installPlayers(parseCSV(text), file.name);
}

async function loadDefaultCSV() {
  const response = await fetch(DEFAULT_CSV_PATH, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status} ${response.statusText}`);
  }

  const text = await response.text();
  return installPlayers(parseCSV(text), DEFAULT_CSV_PATH, "himekawa_yuki");
}

document.addEventListener("DOMContentLoaded", async () => {
  const select = document.querySelector("#player-select");
  select.addEventListener("change", () => {
    renderPlayer(select.value);
    renderPlayerList();
  });

  initPreviewScale();
  initExportControls();

  document.querySelector("#csv-input").addEventListener("change", async event => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      await loadCSVFile(file);
    } catch (error) {
      console.error(error);
      document.querySelector("#csv-status").textContent =
        `CSV load failed: ${error.message}`;
    }
  });

  try {
    await loadDefaultCSV();
  } catch (error) {
    console.error(error);
    document.querySelector("#csv-status").textContent =
      `../PLAYER_RATINGS.csv auto-load failed: ${error.message}. Open through a local HTTP server or choose the CSV manually.`;
  }
});

/* v7 player image editor */
const PLAYER_IMAGE_DEFAULT = Object.freeze({ x:0, y:0, width:900, scale:1 });
const playerImageObjectUrls = new Map();

function layoutKey(playerId){ return `team-yukies-image-layout:${playerId}`; }
function legacyLayoutKey(playerId){ return `team-yukkies-image-layout:${playerId}`; }
function currentPlayerId(){ return document.querySelector("#player-select")?.value || ""; }
function currentPlayer(){ return PLAYERS[currentPlayerId()] || null; }
function playerImageEl(){ return document.querySelector("#front-player"); }

function repositoryImageLayout(playerId){
  const s = PLAYER_IMAGE_DATA[playerId] || PLAYER_IMAGE_DEFAULT;
  return {
    x:Number(s.x ?? 0),
    y:Number(s.y ?? 0),
    width:Math.max(1, Number(s.width ?? 900)),
    scale:Math.max(.1, Number(s.scale ?? 1))
  };
}

function getImageLayout(playerId){
  const p = PLAYERS[playerId] || {};
  let saved = null;
  try {
    let raw = localStorage.getItem(layoutKey(playerId));
    if (!raw) {
      const legacy = localStorage.getItem(legacyLayoutKey(playerId));
      if (legacy) {
        raw = legacy;
        localStorage.setItem(layoutKey(playerId), legacy);
        localStorage.removeItem(legacyLayoutKey(playerId));
      }
    }
    saved = raw ? JSON.parse(raw) : null;
  } catch {}
  const s = saved || p.player_image_layout || repositoryImageLayout(playerId);
  return {
    x:Number(s.x ?? 0),
    y:Number(s.y ?? 0),
    width:Math.max(1, Number(s.width ?? 900)),
    scale:Math.max(.1, Number(s.scale ?? 1))
  };
}

function saveImageLayout(playerId, layout){
  localStorage.setItem(layoutKey(playerId), JSON.stringify(layout));
  if (PLAYERS[playerId]) PLAYERS[playerId].player_image_layout = {...layout};
}

function syncEditor(l){
  document.querySelector("#img-x").value = Math.round(l.x);
  document.querySelector("#img-y").value = Math.round(l.y);
  document.querySelector("#img-width").value = Math.round(l.width);
  document.querySelector("#img-scale").value = Number(l.scale).toFixed(2);
}

function readEditor(){
  return {
    x:Number(document.querySelector("#img-x").value || 0),
    y:Number(document.querySelector("#img-y").value || 0),
    width:Math.max(1, Number(document.querySelector("#img-width").value || 900)),
    scale:Math.max(.1, Number(document.querySelector("#img-scale").value || 1))
  };
}

function applyImageLayout(l, persist=true){
  const img = playerImageEl();
  const id = currentPlayerId();
  if (!img || !id) return;
  img.style.setProperty("--player-x", `${l.x}px`);
  img.style.setProperty("--player-y", `${l.y}px`);
  img.style.setProperty("--player-width", `${l.width}px`);
  img.style.transform = `scale(${l.scale})`;
  syncEditor(l);
  if (persist) saveImageLayout(id, l);
}

function imageStatus(text){
  const el = document.querySelector("#image-status");
  if (el) el.textContent = text || "";
}

function renderEditedPlayerImage(){
  const p = currentPlayer();
  const img = playerImageEl();
  if (!p || !img) return;

  const imageMeta = PLAYER_IMAGE_DATA[p.player_id] || {};
  const src = playerImageObjectUrls.get(p.player_id) || p.player_image || imageMeta.image_src || null;
  const layout = getImageLayout(p.player_id);
  syncEditor(layout);

  if (!src){
    img.hidden = true;
    img.removeAttribute("src");
    imageStatus("선수 이미지 없음");
    return;
  }

  img.hidden = false;
  img.src = src;
  applyImageLayout(layout, false);
  img.onload = () => imageStatus(`${img.naturalWidth}×${img.naturalHeight}px`);
}

function setImageFile(file){
  if (!file || !file.type.startsWith("image/")) return;
  const p = currentPlayer();
  if (!p) return;

  const old = playerImageObjectUrls.get(p.player_id);
  if (old) URL.revokeObjectURL(old);

  const url = URL.createObjectURL(file);
  playerImageObjectUrls.set(p.player_id, url);

  const img = playerImageEl();
  img.hidden = false;
  img.src = url;
  img.onload = () => {
    const layout = {...PLAYER_IMAGE_DEFAULT};
    applyImageLayout(layout, true);
    imageStatus(`${file.name} · ${img.naturalWidth}×${img.naturalHeight}px`);
  };
}

function nudge(dx,dy){
  const l = readEditor();
  l.x += dx; l.y += dy;
  applyImageLayout(l, true);
}

function initImageEditor(){
  const img = playerImageEl();
  const card = document.querySelector("#front-card");

  document.querySelector("#player-image-input").addEventListener("change", e => {
    const file = e.target.files?.[0];
    if (file) setImageFile(file);
  });

  ["#img-x","#img-y","#img-width","#img-scale"].forEach(sel => {
    document.querySelector(sel).addEventListener("input", () => {
      applyImageLayout(readEditor(), true);
    });
  });

  document.querySelector("#nudge-left").onclick = () => nudge(-1,0);
  document.querySelector("#nudge-right").onclick = () => nudge(1,0);
  document.querySelector("#nudge-up").onclick = () => nudge(0,-1);
  document.querySelector("#nudge-down").onclick = () => nudge(0,1);

  document.querySelector("#img-reset").onclick = () => {
    const id = currentPlayerId();
    localStorage.removeItem(layoutKey(id));
    const repoLayout = repositoryImageLayout(id);
    if (PLAYERS[id]) PLAYERS[id].player_image_layout = {...repoLayout};
    applyImageLayout(repoLayout, false);
  };

  document.querySelector("#img-clear").onclick = () => {
    const p = currentPlayer();
    if (!p) return;
    const url = playerImageObjectUrls.get(p.player_id);
    if (url) URL.revokeObjectURL(url);
    playerImageObjectUrls.delete(p.player_id);
    p.player_image = null;
    img.hidden = true;
    img.removeAttribute("src");
    imageStatus("선수 이미지 제거됨");
  };

  document.querySelector("#img-copy-layout").onclick = async () => {
    const p = currentPlayer();
    if (!p) return;
    const current = PLAYER_IMAGE_DATA[p.player_id] || {};
    const layout = readEditor();
    const text = JSON.stringify({
      player_id:p.player_id,
      image_src:current.image_src || p.player_image || null,
      x:layout.x,
      y:layout.y,
      width:layout.width,
      scale:layout.scale
    }, null, 2);
    try {
      await navigator.clipboard.writeText(text);
      imageStatus("배치 JSON 복사 완료");
    } catch {
      imageStatus(text);
    }
  };

  let dragging=false, sx=0, sy=0, ox=0, oy=0;

  img.addEventListener("pointerdown", e => {
    if (img.hidden) return;
    dragging=true;
    img.classList.add("is-dragging");
    const l=readEditor();
    sx=e.clientX; sy=e.clientY; ox=l.x; oy=l.y;
    img.setPointerCapture(e.pointerId);
    e.preventDefault();
  });

  img.addEventListener("pointermove", e => {
    if (!dragging) return;
    const rect=card.getBoundingClientRect();
    const l=readEditor();
    l.x=Math.round(ox + (e.clientX-sx)*(900/rect.width));
    l.y=Math.round(oy + (e.clientY-sy)*(1260/rect.height));
    applyImageLayout(l, false);
  });

  function finish(e){
    if (!dragging) return;
    dragging=false;
    img.classList.remove("is-dragging");
    applyImageLayout(readEditor(), true);
    try { img.releasePointerCapture(e.pointerId); } catch {}
  }
  img.addEventListener("pointerup", finish);
  img.addEventListener("pointercancel", finish);

  card.addEventListener("dragover", e => {
    e.preventDefault();
    card.classList.add("is-dragover");
  });
  card.addEventListener("dragleave", e => {
    if (!card.contains(e.relatedTarget)) card.classList.remove("is-dragover");
  });
  card.addEventListener("drop", e => {
    e.preventDefault();
    card.classList.remove("is-dragover");
    const file=[...(e.dataTransfer.files||[])].find(f=>f.type.startsWith("image/"));
    if (file) setImageFile(file);
  });
}

const renderPlayerV6 = renderPlayer;
renderPlayer = function(playerId){
  renderPlayerV6(playerId);
  requestAnimationFrame(renderEditedPlayerImage);
};

document.addEventListener("DOMContentLoaded", () => {
  initImageEditor();
  document.querySelector("#player-select").addEventListener("change", () => {
    requestAnimationFrame(renderEditedPlayerImage);
  });
  renderEditedPlayerImage();
});
