(() => {
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
    const serial = cleanPart(player.serial, "NO_SERIAL");
    const last = cleanPart(player.display_last_name, "NO_LAST");
    const first = cleanPart(player.display_first_name, "NO_FIRST");
    return `${serial}_${last}_${first}`;
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

    return String(error || "알 수 없는 PNG 렌더링 오류");
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
      try {
        canvas.toBlob(blob => {
          if (blob) resolve(blob);
          else reject(new Error("PNG 인코딩 결과가 비어 있습니다"));
        }, "image/png");
      } catch (error) {
        reject(new Error(describeError(error)));
      }
    });
  }

  async function renderCard(card) {
    if (!window.html2canvas) throw new Error("html2canvas가 로드되지 않았습니다");
    if (!card) throw new Error("카드 요소를 찾지 못했습니다");

    await waitForAssets(card);

    const stage = document.querySelector("#card-stage");
    const previousStageTransform = stage?.style.transform || "";
    const previousCardTransform = card.style.transform;
    const previousCardMargin = card.style.margin;

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

      if (canvas.width !== WIDTH || canvas.height !== HEIGHT) {
        const normalized = document.createElement("canvas");
        normalized.width = WIDTH;
        normalized.height = HEIGHT;
        const ctx = normalized.getContext("2d");
        if (!ctx) throw new Error("PNG 정규화용 Canvas를 만들 수 없습니다");
        ctx.drawImage(canvas, 0, 0, WIDTH, HEIGHT);
        return canvasToBlob(normalized);
      }

      return canvasToBlob(canvas);
    } finally {
      if (stage) stage.style.transform = previousStageTransform;
      card.style.transform = previousCardTransform;
      card.style.margin = previousCardMargin;
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
    setTimeout(() => URL.revokeObjectURL(url), 5000);
  }

  window.exportCurrentCards = async function exportCurrentCardsFixed() {
    const player = typeof currentPlayer === "function" ? currentPlayer() : null;
    if (!player) throw new Error("선택된 선수가 없습니다");
    if (!player.serial) throw new Error("선택된 선수의 시리얼 넘버가 없습니다");

    const button = document.querySelector("#save-cards");
    if (button) button.disabled = true;

    const base = filenameBase(player);
    const frontName = `${base}_front.png`;
    const backName = `${base}_back.png`;

    try {
      status("앞면 PNG 생성 중…");
      const frontBlob = await renderCard(document.querySelector("#front-card"));

      status("뒷면 PNG 생성 중…");
      const backBlob = await renderCard(document.querySelector("#back-card"));

      status("다운로드 시작…");
      downloadBlob(frontBlob, frontName);
      setTimeout(() => downloadBlob(backBlob, backName), 120);
      status(`저장 요청 완료 · ${frontName} / ${backName}`);
    } catch (error) {
      const message = describeError(error);
      console.error("TEAM YUKIES PNG export failed", error);
      throw new Error(message);
    } finally {
      if (button) button.disabled = false;
    }
  };
})();
