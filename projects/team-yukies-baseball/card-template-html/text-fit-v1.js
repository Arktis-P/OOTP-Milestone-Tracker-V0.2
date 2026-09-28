(() => {
  const BUILD = "text-fit-v1-20260929";
  const STORAGE_PREFIX = "team-yukies-text-fit:";
  const DEFAULT_SETTING = Object.freeze({ tracking: 0, width: 100 });
  const LIMITS = Object.freeze({ tracking: [-12, 6], width: [50, 120] });

  const TARGETS = Object.freeze({
    front_first:  { label: "Front · First name", selector: ".front__first" },
    front_last:   { label: "Front · Last name", selector: ".front__last" },
    front_pos:    { label: "Front · Position", selector: ".front__position" },
    back_first:   { label: "Back · First name", selector: ".back__first" },
    back_last:    { label: "Back · Last name", selector: ".back__last" },
    back_pos:     { label: "Back · Position", selector: ".back__position" },
    profile_1:    { label: "Back · Profile line 1", selector: ".back__profile-line:nth-child(1)", compensateWidth: true },
    profile_2:    { label: "Back · Profile line 2", selector: ".back__profile-line:nth-child(2)", compensateWidth: true },
    profile_3:    { label: "Back · Profile line 3", selector: ".back__profile-line:nth-child(3)", compensateWidth: true },
    back_report:  { label: "Back · Scouting report", selector: ".back__report", compensateWidth: true }
  });

  const baseStyles = new WeakMap();

  function control(id) {
    return document.getElementById(id);
  }

  function clamp(value, min, max, fallback) {
    const n = Number(value);
    return Number.isFinite(n) ? Math.max(min, Math.min(max, n)) : fallback;
  }

  function playerId() {
    return typeof currentPlayerId === "function"
      ? currentPlayerId()
      : (document.querySelector("#player-select")?.value || "");
  }

  function storageKey(id) {
    return `${STORAGE_PREFIX}${id}`;
  }

  function normalizeSetting(value = {}) {
    return {
      tracking: clamp(value.tracking, ...LIMITS.tracking, DEFAULT_SETTING.tracking),
      width: clamp(value.width, ...LIMITS.width, DEFAULT_SETTING.width)
    };
  }

  function loadAll(id) {
    if (!id) return {};
    try {
      const raw = localStorage.getItem(storageKey(id));
      const parsed = raw ? JSON.parse(raw) : {};
      const result = {};
      Object.keys(TARGETS).forEach(key => {
        if (parsed?.[key]) result[key] = normalizeSetting(parsed[key]);
      });
      return result;
    } catch {
      return {};
    }
  }

  function saveAll(id, value) {
    if (!id) return;
    const compact = {};
    Object.entries(value || {}).forEach(([key, setting]) => {
      if (!TARGETS[key]) return;
      const normalized = normalizeSetting(setting);
      if (normalized.tracking !== 0 || normalized.width !== 100) {
        compact[key] = normalized;
      }
    });

    if (Object.keys(compact).length) {
      localStorage.setItem(storageKey(id), JSON.stringify(compact));
    } else {
      localStorage.removeItem(storageKey(id));
    }
  }

  function selectedTarget() {
    const key = control("text-fit-target")?.value || "front_last";
    return TARGETS[key] ? key : "front_last";
  }

  function getBase(el) {
    let base = baseStyles.get(el);
    if (base) return base;

    const computed = getComputedStyle(el);
    const letterSpacing = computed.letterSpacing === "normal"
      ? 0
      : (parseFloat(computed.letterSpacing) || 0);
    const computedWidth = parseFloat(computed.width) || el.offsetWidth || 1;

    base = {
      letterSpacing,
      computedWidth,
      inlineLetterSpacing: el.style.letterSpacing,
      inlineTransform: el.style.transform,
      inlineTransformOrigin: el.style.transformOrigin,
      inlineWidth: el.style.width
    };
    baseStyles.set(el, base);
    return base;
  }

  function restoreElement(el) {
    if (!el) return;
    const base = getBase(el);
    el.style.letterSpacing = base.inlineLetterSpacing;
    el.style.transform = base.inlineTransform;
    el.style.transformOrigin = base.inlineTransformOrigin;
    el.style.width = base.inlineWidth;
    el.removeAttribute("data-text-fit-active");
  }

  function applySetting(key, setting) {
    const config = TARGETS[key];
    if (!config) return;
    const el = document.querySelector(config.selector);
    if (!el) return;

    const normalized = normalizeSetting(setting);
    const base = getBase(el);
    const scale = normalized.width / 100;

    el.style.letterSpacing = `${base.letterSpacing + normalized.tracking}px`;
    el.style.transformOrigin = "left center";
    el.style.transform = scale === 1
      ? base.inlineTransform
      : `${base.inlineTransform ? `${base.inlineTransform} ` : ""}scaleX(${scale})`;

    if (config.compensateWidth && scale !== 1) {
      // Expand the layout box before scaleX so clipped/wrapped text receives
      // more logical width while its final visual footprint stays unchanged.
      el.style.width = `${base.computedWidth / scale}px`;
    } else {
      el.style.width = base.inlineWidth;
    }

    if (normalized.tracking !== 0 || normalized.width !== 100) {
      el.setAttribute("data-text-fit-active", key);
    } else {
      el.removeAttribute("data-text-fit-active");
    }
  }

  function resetAllElements() {
    Object.values(TARGETS).forEach(config => {
      restoreElement(document.querySelector(config.selector));
    });
  }

  function applyCurrentPlayer() {
    resetAllElements();
    const settings = loadAll(playerId());
    Object.entries(settings).forEach(([key, setting]) => applySetting(key, setting));
    syncControls();
  }

  function currentSetting() {
    const settings = loadAll(playerId());
    return normalizeSetting(settings[selectedTarget()] || DEFAULT_SETTING);
  }

  function setControlValue(id, value) {
    const el = control(id);
    if (el && document.activeElement !== el) el.value = String(value);
  }

  function syncControls() {
    const setting = currentSetting();
    setControlValue("text-fit-tracking", setting.tracking);
    setControlValue("text-fit-tracking-number", setting.tracking);
    setControlValue("text-fit-width", setting.width);
    setControlValue("text-fit-width-number", setting.width);

    const status = control("text-fit-status");
    if (status) {
      const target = TARGETS[selectedTarget()];
      status.textContent = `${target.label} · Tracking ${setting.tracking}px · Width ${setting.width}%`;
    }
  }

  function updateSelected(field, value) {
    const id = playerId();
    if (!id) return;
    const key = selectedTarget();
    const settings = loadAll(id);
    const next = normalizeSetting(settings[key] || DEFAULT_SETTING);

    if (field === "tracking") {
      next.tracking = clamp(value, ...LIMITS.tracking, DEFAULT_SETTING.tracking);
    } else if (field === "width") {
      next.width = clamp(value, ...LIMITS.width, DEFAULT_SETTING.width);
    }

    if (next.tracking === 0 && next.width === 100) delete settings[key];
    else settings[key] = next;

    saveAll(id, settings);
    applySetting(key, next);
    syncControls();
  }

  function bindPair(rangeId, numberId, field) {
    const range = control(rangeId);
    const number = control(numberId);

    range?.addEventListener("input", () => {
      if (number) number.value = range.value;
      updateSelected(field, range.value);
    });

    number?.addEventListener("input", () => {
      if (!Number.isFinite(Number(number.value))) return;
      updateSelected(field, number.value);
      if (range) range.value = String(currentSetting()[field]);
    });

    number?.addEventListener("change", () => {
      const setting = currentSetting();
      number.value = String(setting[field]);
      if (range) range.value = String(setting[field]);
    });
  }

  function resetField() {
    const id = playerId();
    if (!id) return;
    const key = selectedTarget();
    const settings = loadAll(id);
    delete settings[key];
    saveAll(id, settings);
    restoreElement(document.querySelector(TARGETS[key].selector));
    syncControls();
  }

  function resetPlayer() {
    const id = playerId();
    if (!id) return;
    localStorage.removeItem(storageKey(id));
    resetAllElements();
    syncControls();
  }

  function populateTargets() {
    const select = control("text-fit-target");
    if (!select) return;
    select.replaceChildren();
    Object.entries(TARGETS).forEach(([key, config]) => {
      const option = document.createElement("option");
      option.value = key;
      option.textContent = config.label;
      select.appendChild(option);
    });
    select.value = "front_last";
  }

  function bindUi() {
    populateTargets();

    control("text-fit-target")?.addEventListener("change", syncControls);
    bindPair("text-fit-tracking", "text-fit-tracking-number", "tracking");
    bindPair("text-fit-width", "text-fit-width-number", "width");
    control("text-fit-reset-field")?.addEventListener("click", resetField);
    control("text-fit-reset-player")?.addEventListener("click", resetPlayer);

    document.querySelector("#player-select")?.addEventListener("change", () => {
      requestAnimationFrame(applyCurrentPlayer);
    });

    // Startup CSV rendering occurs asynchronously after DOMContentLoaded.
    // Re-apply once text data has arrived, and also whenever card text changes.
    const cardData = document.querySelector("#front-card .card__data")?.parentElement?.parentElement || document.querySelector("#card-stage");
    if (cardData) {
      const observer = new MutationObserver(() => {
        requestAnimationFrame(() => {
          const settings = loadAll(playerId());
          Object.entries(settings).forEach(([key, setting]) => applySetting(key, setting));
        });
      });
      observer.observe(cardData, { subtree: true, childList: true, characterData: true });
    }

    setTimeout(applyCurrentPlayer, 0);
    setTimeout(applyCurrentPlayer, 500);

    window.TEAM_YUKIES_TEXT_FIT_BUILD = BUILD;
    window.TEAM_YUKIES_applyTextFit = applyCurrentPlayer;
    console.info(`[TEAM YUKIES] text fit ${BUILD} active`);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindUi, { once: true });
  } else {
    bindUi();
  }
})();
