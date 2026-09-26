(() => {
  const BUILD = "v3-20260927";
  const WIDTH = 900;
  const HEIGHT = 1260;

  function status(message) {
    const el = document.querySelector("#export-status");
    if (el) el.textContent = message || "";
  }

  function cleanPart(value, fallback = "") {
    const text = String(value ?? "").trim() || fallback;
    return text
      .replace(/[<>:"/\\|?*\x00-\x1F]/g, "_")
      .replace(/\s+/g, "_")
      .replace(/[. ]+$/g, "")
      .replace(/_+/g, "_");
  }

  function filenameBase(player) {
    return [
      cleanPart(player.serial, "NO_SERIAL"),
      cleanPart(player.display_last_name, "NO_LAST"),
      cleanPart(player.display_first_name, "NO_FIRST")
    ].join("_");
  }

  function describeError(error) {
    if (error instanceof Error && error.message) return error.message;
    if (typeof error === "string" && error.trim()) return error.trim();
    const source = error?.target?.currentSrc || error?.target?.src || "";
    if (source) return `이미지 로드 실패: ${source}`;
    try {
      const json = JSON.stringify(error);
      if (json && json !== "{}") return json;
    } catch {}
    const text = String(error || "").trim();
    return text && text !== "[object Event]" && text !== "[object Object]"
      ? text
      : "알 수 없는 PNG 렌더링 오류";
  }

  async function waitForAssets(card) {
    if (document.fonts?.ready) {
      await Promise.race([
        document.fonts.ready,
        new Promise((_, reject) => setTimeout(() => reject(new Error("폰트 로딩 시간 초과")), 15000))
      ]);
    }

    const images = [...card.querySelectorAll("img")]
      .filter(img => !img.hidden && img.getAttribute("src"));

    await Promise.all(images.map(img => {
      if (img.complete && img.naturalWidth > 0) return Promise.resolve();
      return new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          cleanup();
          reject(new Error(`이미지 로딩 시간 초과: ${img.currentSrc || img.src}`));
        }, 15000);
        const cleanup = () => {
          clearTimeout(timer);
          img.removeEventListener("load", onLoad);
          img.removeEventListener("error", onError);
        };
        const onLoad = () => { cleanup(); resolve(); };
        const onError = () => {
          cleanup();
          reject(new Error(`이미지 로드 실패: ${img.currentSrc || img.src}`));
        };
        img.addEventListener("load", onLoad, { once: true });
        img.addEventListener("error", onError, { once: true });
      });
    }));
  }

  function canvasToBlob(canvas) {
    return new Promise((resolve, reject) => {
      canvas.toBlob(blob => {
        if (blob) resolve(blob);
        else reject(new Error("PNG 인코딩 결과가 비어 있습니다"));
      }, "image/png");
    });
  }

  async function renderCard(card) {
    if (!window.html2canvas) throw new Error("html2canvas가 로드되지 않았습니다");
    if (!card) throw new Error("카드 요소를 찾지 못했습니다");

    await waitForAssets(card);

    const stage = document.querySelector("#card-stage");
    const stageTransform = stage?.style.transform || "";
    const cardTransform = card.style.transform;
    const cardMargin = card.style.margin;

    try {
      if (stage) stage.style.transform = "none";
      card.style.transform = "none";
      card.style.margin = "0";
      await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));

      const canvas = await window.html2canvas(card, {
        backgroundColor: null,
        scale: 1,
        width: WIDTH,
        height: HEIGHT,
        useCORS: true,
        allowTaint: false,
        logging: true,
        removeContainer: true,
        imageTimeout: 30000,
        scrollX: 0,
        scrollY: 0,
        onclone: clonedDocument => {
          const clonedStage = clonedDocument.querySelector("#card-stage");
          if (clonedStage) clonedStage.style.transform = "none";
          const clonedCard = card.id ? clonedDocument.getElementById(card.id) : null;
          if (clonedCard) {
            clonedCard.style.width = `${WIDTH}px`;
            clonedCard.style.height = `${HEIGHT}px`;
            clonedCard.style.margin = "0";
            clonedCard.style.transform = "none";
          }
        }
      });

      if (!canvas || canvas.width < 1 || canvas.height < 1) {
        throw new Error("렌더러가 빈 Canvas를 반환했습니다");
      }

      if (canvas.width === WIDTH && canvas.height === HEIGHT) return canvasToBlob(canvas);

      const normalized = document.createElement("canvas");
      normalized.width = WIDTH;
      normalized.height = HEIGHT;
      const ctx = normalized.getContext("2d");
      if (!ctx) throw new Error("PNG 정규화용 Canvas를 만들 수 없습니다");
      ctx.drawImage(canvas, 0, 0, WIDTH, HEIGHT);
      return canvasToBlob(normalized);
    } finally {
      if (stage) stage.style.transform = stageTransform;
      card.style.transform = cardTransform;
      card.style.margin = cardMargin;
    }
  }

  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 10000);
  }

  async function exportCurrentCardsV3() {
    const player = typeof currentPlayer === "function" ? currentPlayer() : null;
    if (!player) throw new Error("선택된 선수가 없습니다");
    if (!player.serial) throw new Error("선택된 선수의 시리얼 넘버가 없습니다");

    const base = filenameBase(player);
    status(`${BUILD} · 앞면 렌더링 중…`);
    const frontBlob = await renderCard(document.querySelector("#front-card"));

    status(`${BUILD} · 뒷면 렌더링 중…`);
    const backBlob = await renderCard(document.querySelector("#back-card"));

    const frontName = `${base}_front.png`;
    const backName = `${base}_back.png`;
    downloadBlob(frontBlob, frontName);
    setTimeout(() => downloadBlob(backBlob, backName), 150);
    status(`${BUILD} · 저장 요청 완료`);
  }

  function bindExportButton() {
    const oldButton = document.querySelector("#save-cards");
    if (!oldButton) {
      status(`${BUILD} · 저장 버튼 없음`);
      return;
    }

    // Replace the node itself so every listener registered by legacy export code
    // is physically discarded. Only this v3 handler remains on the new button.
    const button = oldButton.cloneNode(true);
    oldButton.replaceWith(button);
    button.dataset.exportBuild = BUILD;
    button.title = `PNG export ${BUILD}`;

    button.addEventListener("click", async event => {
      event.preventDefault();
      event.stopImmediatePropagation();
      button.disabled = true;
      try {
        await exportCurrentCardsV3();
      } catch (error) {
        const message = describeError(error);
        console.error(`[TEAM YUKIES ${BUILD}] PNG export failed`, error);
        status(`${BUILD} · 저장 실패: ${message}`);
      } finally {
        button.disabled = false;
      }
    }, { capture: true });

    window.exportCurrentCards = exportCurrentCardsV3;
    window.TEAM_YUKIES_EXPORT_BUILD = BUILD;
    console.info(`[TEAM YUKIES] PNG export ${BUILD} active`);
    status(`EXPORT ${BUILD} READY`);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindExportButton, { once: true });
  } else {
    bindExportButton();
  }
})();
