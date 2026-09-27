(() => {
  const BUILD = "image-adjust-v1-20260927";
  const STYLE_PREFIX = "team-yukies-image-style:";
  const DEFAULT_STYLE = Object.freeze({
    brightness: 100,
    contrast: 100,
    saturation: 100,
    outlineColor: "#202A43",
    outlineWidth: 0
  });

  const originalSources = new Map();
  const processedUrls = new Map();
  const processedUrlSet = new Set();
  let renderToken = 0;
  let renderTimer = null;

  function clamp(value, min, max, fallback) {
    const n = Number(value);
    return Number.isFinite(n) ? Math.max(min, Math.min(max, n)) : fallback;
  }

  function normalizeColor(value) {
    const text = String(value || "").trim();
    return /^#[0-9a-f]{6}$/i.test(text) ? text.toUpperCase() : DEFAULT_STYLE.outlineColor;
  }

  function styleKey(playerId) {
    return `${STYLE_PREFIX}${playerId}`;
  }

  function currentId() {
    return typeof currentPlayerId === "function"
      ? currentPlayerId()
      : (document.querySelector("#player-select")?.value || "");
  }

  function normalizeStyle(value = {}) {
    return {
      brightness: clamp(value.brightness, 50, 150, DEFAULT_STYLE.brightness),
      contrast: clamp(value.contrast, 50, 150, DEFAULT_STYLE.contrast),
      saturation: clamp(value.saturation, 0, 200, DEFAULT_STYLE.saturation),
      outlineColor: normalizeColor(value.outlineColor),
      outlineWidth: clamp(value.outlineWidth, 0, 12, DEFAULT_STYLE.outlineWidth)
    };
  }

  function loadStyle(playerId) {
    if (!playerId) return { ...DEFAULT_STYLE };
    try {
      const raw = localStorage.getItem(styleKey(playerId));
      return raw ? normalizeStyle(JSON.parse(raw)) : { ...DEFAULT_STYLE };
    } catch {
      return { ...DEFAULT_STYLE };
    }
  }

  function saveStyle(playerId, style) {
    if (!playerId) return;
    localStorage.setItem(styleKey(playerId), JSON.stringify(normalizeStyle(style)));
  }

  function isDefaultStyle(style) {
    return style.brightness === DEFAULT_STYLE.brightness &&
      style.contrast === DEFAULT_STYLE.contrast &&
      style.saturation === DEFAULT_STYLE.saturation &&
      style.outlineWidth === 0;
  }

  function control(id) {
    return document.getElementById(id);
  }

  function syncControls(style = loadStyle(currentId())) {
    const values = {
      "img-brightness": style.brightness,
      "img-contrast": style.contrast,
      "img-saturation": style.saturation,
      "img-outline-width": style.outlineWidth,
      "img-outline-color": style.outlineColor
    };

    Object.entries(values).forEach(([id, value]) => {
      const el = control(id);
      if (el) el.value = String(value);
    });

    const outputs = {
      "img-brightness-value": `${Math.round(style.brightness)}%`,
      "img-contrast-value": `${Math.round(style.contrast)}%`,
      "img-saturation-value": `${Math.round(style.saturation)}%`,
      "img-outline-width-value": `${Number(style.outlineWidth).toFixed(style.outlineWidth % 1 ? 1 : 0)}px`
    };

    Object.entries(outputs).forEach(([id, value]) => {
      const el = control(id);
      if (el) el.textContent = value;
    });
  }

  function readControls() {
    return normalizeStyle({
      brightness: control("img-brightness")?.value,
      contrast: control("img-contrast")?.value,
      saturation: control("img-saturation")?.value,
      outlineColor: control("img-outline-color")?.value,
      outlineWidth: control("img-outline-width")?.value
    });
  }

  function setAdjustStatus(message) {
    const el = control("adjust-status");
    if (el) el.textContent = message || "";
  }

  function revokeProcessed(playerId) {
    const old = processedUrls.get(playerId);
    if (!old) return;
    processedUrls.delete(playerId);
    processedUrlSet.delete(old);
    try { URL.revokeObjectURL(old); } catch {}
  }

  function activeOriginalSource(playerId) {
    let source = null;

    if (typeof playerImageObjectUrls !== "undefined") {
      const candidate = playerImageObjectUrls.get(playerId);
      if (candidate && !processedUrlSet.has(candidate)) source = candidate;
    }

    if (!source) source = originalSources.get(playerId) || null;

    if (!source && typeof PLAYERS !== "undefined") {
      const player = PLAYERS[playerId];
      if (player?.player_image) source = player.player_image;
    }

    if (!source && typeof PLAYER_IMAGE_DATA !== "undefined") {
      const meta = PLAYER_IMAGE_DATA[playerId];
      if (meta?.image_src) source = meta.image_src;
    }

    if (source && !processedUrlSet.has(source)) {
      originalSources.set(playerId, source);
      return source;
    }

    return null;
  }

  function loadImage(source) {
    return new Promise((resolve, reject) => {
      const image = new Image();
      image.decoding = "async";
      image.onload = () => resolve(image);
      image.onerror = () => reject(new Error(`보정용 이미지 로드 실패: ${source}`));
      image.src = source;
    });
  }

  function canvasToBlob(canvas) {
    return new Promise((resolve, reject) => {
      canvas.toBlob(blob => {
        if (blob) resolve(blob);
        else reject(new Error("보정 이미지 PNG 생성에 실패했습니다"));
      }, "image/png");
    });
  }

  function drawOutline(maskContext, sourceCanvas, radius) {
    if (radius <= 0) return;

    const rings = Math.max(2, Math.min(5, Math.ceil(radius / 3)));
    const steps = 24;

    for (let ring = 1; ring <= rings; ring++) {
      const r = radius * (ring / rings);
      for (let i = 0; i < steps; i++) {
        const angle = (Math.PI * 2 * i) / steps;
        const dx = Math.round(Math.cos(angle) * r);
        const dy = Math.round(Math.sin(angle) * r);
        maskContext.drawImage(sourceCanvas, dx, dy);
      }
    }
  }

  async function buildProcessedBlob(source, style, layout) {
    const image = await loadImage(source);
    const sourceWidth = Math.max(1, image.naturalWidth || image.width);
    const sourceHeight = Math.max(1, image.naturalHeight || image.height);
    const maxDimension = 4096;
    const scaleDown = Math.min(1, maxDimension / Math.max(sourceWidth, sourceHeight));
    const width = Math.max(1, Math.round(sourceWidth * scaleDown));
    const height = Math.max(1, Math.round(sourceHeight * scaleDown));

    const adjusted = document.createElement("canvas");
    adjusted.width = width;
    adjusted.height = height;
    const adjustedContext = adjusted.getContext("2d");
    if (!adjustedContext) throw new Error("보정 Canvas를 만들 수 없습니다");

    adjustedContext.filter = [
      `brightness(${style.brightness}%)`,
      `contrast(${style.contrast}%)`,
      `saturate(${style.saturation}%)`
    ].join(" ");
    adjustedContext.drawImage(image, 0, 0, width, height);
    adjustedContext.filter = "none";

    if (style.outlineWidth <= 0) return canvasToBlob(adjusted);

    const displayedWidth = Math.max(1, Number(layout?.width) || 900);
    const displayedScale = Math.max(.1, Number(layout?.scale) || 1);
    const radius = Math.max(
      1,
      Math.min(64, Math.round(style.outlineWidth * width / (displayedWidth * displayedScale)))
    );

    const mask = document.createElement("canvas");
    mask.width = width;
    mask.height = height;
    const maskContext = mask.getContext("2d");
    if (!maskContext) throw new Error("아웃라인 마스크를 만들 수 없습니다");

    drawOutline(maskContext, adjusted, radius);
    maskContext.globalCompositeOperation = "source-in";
    maskContext.fillStyle = style.outlineColor;
    maskContext.fillRect(0, 0, width, height);
    maskContext.globalCompositeOperation = "destination-out";
    maskContext.drawImage(adjusted, 0, 0);
    maskContext.globalCompositeOperation = "source-over";

    const output = document.createElement("canvas");
    output.width = width;
    output.height = height;
    const outputContext = output.getContext("2d");
    if (!outputContext) throw new Error("보정 결과 Canvas를 만들 수 없습니다");

    outputContext.drawImage(mask, 0, 0);
    outputContext.drawImage(adjusted, 0, 0);
    return canvasToBlob(output);
  }

  async function applyStyle(playerId = currentId(), { immediate = false } = {}) {
    if (!playerId || playerId !== currentId()) return;

    const img = typeof playerImageEl === "function"
      ? playerImageEl()
      : document.querySelector("#front-player");
    if (!img || img.hidden) return;

    const source = activeOriginalSource(playerId);
    if (!source) return;

    const style = loadStyle(playerId);
    const layout = typeof getImageLayout === "function"
      ? getImageLayout(playerId)
      : { width: 900, scale: 1 };

    const token = ++renderToken;

    if (isDefaultStyle(style)) {
      revokeProcessed(playerId);
      if (playerId === currentId() && img.src !== source) {
        img.onload = null;
        img.src = source;
        if (typeof applyImageLayout === "function") applyImageLayout(layout, false);
      }
      setAdjustStatus("Tone 100 / Outline Off");
      return;
    }

    if (immediate) setAdjustStatus("Rendering…");

    const blob = await buildProcessedBlob(source, style, layout);
    if (token !== renderToken || playerId !== currentId()) return;

    const url = URL.createObjectURL(blob);
    const old = processedUrls.get(playerId);
    processedUrls.set(playerId, url);
    processedUrlSet.add(url);

    img.onload = null;
    img.src = url;
    if (typeof applyImageLayout === "function") applyImageLayout(layout, false);

    if (old) {
      processedUrlSet.delete(old);
      setTimeout(() => {
        try { URL.revokeObjectURL(old); } catch {}
      }, 1000);
    }

    setAdjustStatus(
      `B ${Math.round(style.brightness)} · C ${Math.round(style.contrast)} · S ${Math.round(style.saturation)} · O ${style.outlineWidth}px`
    );
  }

  function scheduleApply(delay = 70) {
    clearTimeout(renderTimer);
    renderTimer = setTimeout(() => {
      applyStyle(currentId()).catch(error => {
        console.error(`[TEAM YUKIES ${BUILD}] render failed`, error);
        setAdjustStatus(`보정 실패: ${error.message || String(error)}`);
      });
    }, delay);
  }

  function onStyleInput() {
    const playerId = currentId();
    if (!playerId) return;
    const style = readControls();
    saveStyle(playerId, style);
    syncControls(style);
    scheduleApply();
  }

  function resetTone() {
    const playerId = currentId();
    if (!playerId) return;
    const style = loadStyle(playerId);
    style.brightness = DEFAULT_STYLE.brightness;
    style.contrast = DEFAULT_STYLE.contrast;
    style.saturation = DEFAULT_STYLE.saturation;
    saveStyle(playerId, style);
    syncControls(style);
    scheduleApply(0);
  }

  function resetOutline() {
    const playerId = currentId();
    if (!playerId) return;
    const style = loadStyle(playerId);
    style.outlineColor = DEFAULT_STYLE.outlineColor;
    style.outlineWidth = DEFAULT_STYLE.outlineWidth;
    saveStyle(playerId, style);
    syncControls(style);
    scheduleApply(0);
  }

  function rememberVisibleSource() {
    const playerId = currentId();
    const img = typeof playerImageEl === "function" ? playerImageEl() : document.querySelector("#front-player");
    if (!playerId || !img) return;

    const source = img.currentSrc || img.src || "";
    if (source && !processedUrlSet.has(source)) {
      originalSources.set(playerId, source);
      scheduleApply(0);
    }
  }

  function observePlayerImage() {
    const img = typeof playerImageEl === "function" ? playerImageEl() : document.querySelector("#front-player");
    if (!img) return;

    const observer = new MutationObserver(() => rememberVisibleSource());
    observer.observe(img, { attributes: true, attributeFilter: ["src", "hidden"] });

    img.addEventListener("load", () => {
      const source = img.currentSrc || img.src || "";
      if (source && !processedUrlSet.has(source)) {
        originalSources.set(currentId(), source);
        setTimeout(() => scheduleApply(0), 0);
      }
    });
  }

  function bindUi() {
    ["img-brightness", "img-contrast", "img-saturation", "img-outline-width", "img-outline-color"]
      .forEach(id => control(id)?.addEventListener("input", onStyleInput));

    control("img-tone-reset")?.addEventListener("click", resetTone);
    control("img-outline-reset")?.addEventListener("click", resetOutline);

    document.querySelector("#player-select")?.addEventListener("change", () => {
      renderToken++;
      syncControls(loadStyle(currentId()));
      setTimeout(() => {
        rememberVisibleSource();
        scheduleApply(0);
      }, 0);
    });

    control("img-save")?.addEventListener("click", () => {
      const playerId = currentId();
      if (playerId) saveStyle(playerId, readControls());
    });

    ["img-width", "img-scale"].forEach(id => {
      control(id)?.addEventListener("input", () => scheduleApply(90));
    });

    syncControls(loadStyle(currentId()));
    observePlayerImage();
    setTimeout(rememberVisibleSource, 0);

    window.TEAM_YUKIES_prepareStyledPlayerImage = async () => {
      clearTimeout(renderTimer);
      await applyStyle(currentId(), { immediate: true });
      const img = typeof playerImageEl === "function" ? playerImageEl() : document.querySelector("#front-player");
      if (img && !img.hidden && typeof img.decode === "function") {
        try { await img.decode(); } catch {}
      }
    };
    window.TEAM_YUKIES_IMAGE_ADJUST_BUILD = BUILD;
    console.info(`[TEAM YUKIES] image adjust ${BUILD} active`);
  }

  window.addEventListener("beforeunload", () => {
    processedUrls.forEach(url => {
      try { URL.revokeObjectURL(url); } catch {}
    });
  }, { once: true });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindUi, { once: true });
  } else {
    bindUi();
  }
})();
