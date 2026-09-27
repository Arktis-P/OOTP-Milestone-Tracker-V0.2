(() => {
  const BUILD = "image-adjust-v3-20260927";
  const STYLE_PREFIX = "team-yukies-image-style:";
  const DEFAULT_STYLE = Object.freeze({
    brightness: 100,
    contrast: 100,
    saturation: 100,
    outlineColor: "#202A43",
    outlineWidth: 0
  });

  const LIMITS = Object.freeze({
    brightness: [50, 150],
    contrast: [50, 150],
    saturation: [0, 200],
    outlineWidth: [0, 50]
  });

  const originalSources = new Map();
  const processedUrls = new Map();
  const processedUrlSet = new Set();
  const processedGeometry = new Map();
  let renderToken = 0;
  let renderTimer = null;
  let baseApplyImageLayout = null;

  function clamp(value, min, max, fallback) {
    const n = Number(value);
    return Number.isFinite(n) ? Math.max(min, Math.min(max, n)) : fallback;
  }

  function normalizeColor(value) {
    let text = String(value || "").trim();
    if (/^[0-9a-f]{6}$/i.test(text)) text = `#${text}`;
    return /^#[0-9a-f]{6}$/i.test(text) ? text.toUpperCase() : DEFAULT_STYLE.outlineColor;
  }

  function isValidColor(value) {
    return /^#?[0-9a-f]{6}$/i.test(String(value || "").trim());
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
      brightness: clamp(value.brightness, ...LIMITS.brightness, DEFAULT_STYLE.brightness),
      contrast: clamp(value.contrast, ...LIMITS.contrast, DEFAULT_STYLE.contrast),
      saturation: clamp(value.saturation, ...LIMITS.saturation, DEFAULT_STYLE.saturation),
      outlineColor: normalizeColor(value.outlineColor),
      outlineWidth: clamp(value.outlineWidth, ...LIMITS.outlineWidth, DEFAULT_STYLE.outlineWidth)
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

  function setControlValue(id, value) {
    const el = control(id);
    if (el && document.activeElement !== el) el.value = String(value);
  }

  function syncControls(style = loadStyle(currentId())) {
    setControlValue("img-brightness", style.brightness);
    setControlValue("img-brightness-number", style.brightness);
    setControlValue("img-contrast", style.contrast);
    setControlValue("img-contrast-number", style.contrast);
    setControlValue("img-saturation", style.saturation);
    setControlValue("img-saturation-number", style.saturation);
    setControlValue("img-outline-width", style.outlineWidth);
    setControlValue("img-outline-width-number", style.outlineWidth);
    setControlValue("img-outline-color", style.outlineColor);
    setControlValue("img-outline-hex", style.outlineColor);
  }

  function setAdjustStatus(message) {
    const el = control("adjust-status");
    if (el) el.textContent = message || "";
  }

  function updateStyleField(field, value, { immediate = false } = {}) {
    const playerId = currentId();
    if (!playerId) return;
    const style = loadStyle(playerId);

    if (field === "outlineColor") {
      if (!isValidColor(value)) return;
      style.outlineColor = normalizeColor(value);
    } else {
      const [min, max] = LIMITS[field] || [Number.NEGATIVE_INFINITY, Number.POSITIVE_INFINITY];
      const n = Number(value);
      if (!Number.isFinite(n)) return;
      style[field] = clamp(n, min, max, DEFAULT_STYLE[field]);
    }

    const normalized = normalizeStyle(style);
    saveStyle(playerId, normalized);
    syncControls(normalized);
    scheduleApply(immediate ? 0 : 80);
  }

  function finalizeNumberField(field, inputId) {
    const input = control(inputId);
    if (!input) return;
    input.value = String(loadStyle(currentId())[field]);
  }

  function revokeProcessed(playerId) {
    const old = processedUrls.get(playerId);
    if (old) {
      processedUrls.delete(playerId);
      processedUrlSet.delete(old);
      try { URL.revokeObjectURL(old); } catch {}
    }
    processedGeometry.delete(playerId);
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

  function drawOutline(maskContext, sourceCanvas, radius, originX, originY) {
    if (radius <= 0) return;

    // More rings/angles than v2 so wide outlines remain continuous around
    // thin hair strands, fingers and other narrow alpha silhouettes.
    const rings = Math.max(3, Math.min(16, Math.ceil(radius / 4)));
    const steps = Math.max(24, Math.min(72, Math.ceil((Math.PI * 2 * radius) / 3)));

    for (let ring = 1; ring <= rings; ring++) {
      const r = radius * (ring / rings);
      for (let i = 0; i < steps; i++) {
        const angle = (Math.PI * 2 * i) / steps;
        const dx = Math.round(Math.cos(angle) * r);
        const dy = Math.round(Math.sin(angle) * r);
        maskContext.drawImage(sourceCanvas, originX + dx, originY + dy);
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

    if (style.outlineWidth <= 0) {
      return {
        blob: await canvasToBlob(adjusted),
        geometry: null
      };
    }

    const displayedWidth = Math.max(1, Number(layout?.width) || 900);
    const displayedScale = Math.max(.1, Number(layout?.scale) || 1);
    const radius = Math.max(
      1,
      Math.min(256, Math.round(style.outlineWidth * width / (displayedWidth * displayedScale)))
    );

    // v2 rendered into a canvas exactly as large as the source image, so any
    // outline extending past the source PNG bounds was clipped. Add transparent
    // padding on every side and keep that padding in the resulting PNG.
    const padding = radius + 4;
    const outputWidth = width + padding * 2;
    const outputHeight = height + padding * 2;

    const mask = document.createElement("canvas");
    mask.width = outputWidth;
    mask.height = outputHeight;
    const maskContext = mask.getContext("2d");
    if (!maskContext) throw new Error("아웃라인 마스크를 만들 수 없습니다");

    drawOutline(maskContext, adjusted, radius, padding, padding);
    maskContext.globalCompositeOperation = "source-in";
    maskContext.fillStyle = style.outlineColor;
    maskContext.fillRect(0, 0, outputWidth, outputHeight);
    maskContext.globalCompositeOperation = "destination-out";
    maskContext.drawImage(adjusted, padding, padding);
    maskContext.globalCompositeOperation = "source-over";

    const output = document.createElement("canvas");
    output.width = outputWidth;
    output.height = outputHeight;
    const outputContext = output.getContext("2d");
    if (!outputContext) throw new Error("보정 결과 Canvas를 만들 수 없습니다");

    outputContext.drawImage(mask, 0, 0);
    outputContext.drawImage(adjusted, padding, padding);

    return {
      blob: await canvasToBlob(output),
      geometry: {
        sourceWidth: width,
        sourceHeight: height,
        outputWidth,
        outputHeight,
        padding
      }
    };
  }

  function applyPaddedLayout(img, layout, geometry) {
    if (!img || !layout || !geometry?.padding) return;

    const sourceWidth = Math.max(1, Number(geometry.sourceWidth) || 1);
    const outputWidth = Math.max(sourceWidth, Number(geometry.outputWidth) || sourceWidth);
    const scale = Math.max(.1, Number(layout.scale) || 1);
    const baseWidth = Math.max(1, Number(layout.width) || 900);

    // Keep the original character pixels in exactly the same card coordinates.
    // Only the transparent padded area grows beyond the former image rectangle.
    const paddingCss = baseWidth * geometry.padding / sourceWidth;
    const expandedWidth = baseWidth * outputWidth / sourceWidth;
    const x = Number(layout.x || 0) - paddingCss * scale;
    const y = Number(layout.y || 0) - paddingCss * scale;

    img.style.setProperty("--player-x", `${x}px`);
    img.style.setProperty("--player-y", `${y}px`);
    img.style.setProperty("--player-width", `${expandedWidth}px`);
    img.style.transform = `scale(${scale})`;
  }

  function reapplyCurrentGeometry(layout = null) {
    const playerId = currentId();
    if (!playerId) return;
    const geometry = processedGeometry.get(playerId);
    if (!geometry?.padding) return;

    const img = typeof playerImageEl === "function"
      ? playerImageEl()
      : document.querySelector("#front-player");
    if (!img || img.hidden) return;

    const activeUrl = processedUrls.get(playerId);
    if (!activeUrl) return;

    const resolvedLayout = layout || (typeof getImageLayout === "function"
      ? getImageLayout(playerId)
      : { x: 0, y: 0, width: 900, scale: 1 });

    applyPaddedLayout(img, resolvedLayout, geometry);
  }

  function installLayoutHook() {
    if (typeof applyImageLayout !== "function") return;
    if (applyImageLayout.__teamYukiesOutlineOverflowV3) return;

    baseApplyImageLayout = applyImageLayout;
    const wrapped = function applyImageLayoutWithOutlinePadding(layout, persist = true) {
      baseApplyImageLayout(layout, persist);
      reapplyCurrentGeometry(layout);
    };
    wrapped.__teamYukiesOutlineOverflowV3 = true;
    applyImageLayout = wrapped;
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
      : { x: 0, y: 0, width: 900, scale: 1 };

    const token = ++renderToken;

    if (isDefaultStyle(style)) {
      revokeProcessed(playerId);
      if (playerId === currentId() && img.src !== source) {
        img.onload = null;
        img.src = source;
      }
      if (typeof applyImageLayout === "function") applyImageLayout(layout, false);
      setAdjustStatus("Tone 100 / Outline Off");
      return;
    }

    if (immediate) setAdjustStatus("Rendering…");

    const result = await buildProcessedBlob(source, style, layout);
    if (token !== renderToken || playerId !== currentId()) return;

    const url = URL.createObjectURL(result.blob);
    const old = processedUrls.get(playerId);
    processedUrls.set(playerId, url);
    processedUrlSet.add(url);

    if (result.geometry) processedGeometry.set(playerId, result.geometry);
    else processedGeometry.delete(playerId);

    img.onload = null;
    img.src = url;
    if (typeof applyImageLayout === "function") applyImageLayout(layout, false);
    if (result.geometry) applyPaddedLayout(img, layout, result.geometry);

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

  function scheduleApply(delay = 80) {
    clearTimeout(renderTimer);
    renderTimer = setTimeout(() => {
      applyStyle(currentId()).catch(error => {
        console.error(`[TEAM YUKIES ${BUILD}] render failed`, error);
        setAdjustStatus(`보정 실패: ${error.message || String(error)}`);
      });
    }, delay);
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

  function bindPair(rangeId, numberId, field) {
    const range = control(rangeId);
    const number = control(numberId);

    range?.addEventListener("input", () => {
      if (number) number.value = range.value;
      updateStyleField(field, range.value);
    });

    number?.addEventListener("input", () => {
      if (!Number.isFinite(Number(number.value))) return;
      updateStyleField(field, number.value);
      if (range) range.value = String(loadStyle(currentId())[field]);
    });

    number?.addEventListener("change", () => finalizeNumberField(field, numberId));
  }

  function bindColorControls() {
    const picker = control("img-outline-color");
    const hex = control("img-outline-hex");

    picker?.addEventListener("input", () => {
      if (hex) hex.value = picker.value.toUpperCase();
      updateStyleField("outlineColor", picker.value);
    });

    hex?.addEventListener("input", () => {
      if (!isValidColor(hex.value)) return;
      const color = normalizeColor(hex.value);
      if (picker) picker.value = color;
      updateStyleField("outlineColor", color);
    });

    hex?.addEventListener("change", () => {
      const style = loadStyle(currentId());
      hex.value = style.outlineColor;
      if (picker) picker.value = style.outlineColor;
    });
  }

  function bindUi() {
    installLayoutHook();

    bindPair("img-brightness", "img-brightness-number", "brightness");
    bindPair("img-contrast", "img-contrast-number", "contrast");
    bindPair("img-saturation", "img-saturation-number", "saturation");
    bindPair("img-outline-width", "img-outline-width-number", "outlineWidth");
    bindColorControls();

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
      if (playerId) saveStyle(playerId, loadStyle(playerId));
    });

    // Width/scale alter the source-pixel radius needed for a fixed visual
    // outline thickness, so rebuild. X/Y are handled immediately by the
    // applyImageLayout hook without re-rasterizing the image.
    ["img-width", "img-scale"].forEach(id => {
      control(id)?.addEventListener("input", () => scheduleApply(100));
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
      reapplyCurrentGeometry();
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