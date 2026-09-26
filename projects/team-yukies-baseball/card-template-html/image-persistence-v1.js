(() => {
  const BUILD = "image-save-v1-20260927";
  const DB_NAME = "team-yukies-card-studio";
  const DB_VERSION = 1;
  const STORE_NAME = "player-images";

  const pendingFiles = new Map();
  const persistentUrls = new Map();
  let dbPromise = null;

  function setImageStatus(message) {
    if (typeof imageStatus === "function") {
      imageStatus(message);
      return;
    }
    const el = document.querySelector("#image-status");
    if (el) el.textContent = message || "";
  }

  function openDb() {
    if (!window.indexedDB) return Promise.reject(new Error("이 브라우저에서 IndexedDB를 사용할 수 없습니다"));
    if (dbPromise) return dbPromise;

    dbPromise = new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: "playerId" });
        }
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("이미지 저장소를 열 수 없습니다"));
      request.onblocked = () => reject(new Error("이미지 저장소가 다른 창에서 사용 중입니다"));
    });

    return dbPromise;
  }

  async function getRecord(playerId) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readonly");
      const request = tx.objectStore(STORE_NAME).get(playerId);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error || new Error("저장된 이미지를 읽을 수 없습니다"));
    });
  }

  async function putRecord(record) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      tx.objectStore(STORE_NAME).put(record);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error("선수 이미지를 저장할 수 없습니다"));
      tx.onabort = () => reject(tx.error || new Error("선수 이미지 저장이 취소되었습니다"));
    });
  }

  async function deleteRecord(playerId) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(STORE_NAME, "readwrite");
      tx.objectStore(STORE_NAME).delete(playerId);
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error || new Error("저장된 이미지를 삭제할 수 없습니다"));
    });
  }

  function revokeUrl(url) {
    if (typeof url === "string" && url.startsWith("blob:")) {
      try { URL.revokeObjectURL(url); } catch {}
    }
  }

  function installStoredBlob(playerId, blob) {
    const previousPersistent = persistentUrls.get(playerId);
    if (previousPersistent) revokeUrl(previousPersistent);

    const previousActive = typeof playerImageObjectUrls !== "undefined"
      ? playerImageObjectUrls.get(playerId)
      : null;

    const url = URL.createObjectURL(blob);
    persistentUrls.set(playerId, url);

    if (typeof playerImageObjectUrls !== "undefined") {
      playerImageObjectUrls.set(playerId, url);
    }

    if (previousActive && previousActive !== previousPersistent && previousActive !== url) {
      revokeUrl(previousActive);
    }

    return url;
  }

  function resolvedStoredLayout(playerId, record) {
    try {
      if (typeof layoutKey === "function" && localStorage.getItem(layoutKey(playerId))) {
        return typeof getImageLayout === "function" ? getImageLayout(playerId) : record?.layout;
      }
    } catch {}
    return record?.layout || (typeof getImageLayout === "function" ? getImageLayout(playerId) : null);
  }

  async function restoreSavedImage(playerId) {
    if (!playerId) return false;
    const record = await getRecord(playerId);
    if (!record?.blob) return false;
    if (typeof currentPlayerId === "function" && currentPlayerId() !== playerId) return false;

    const url = installStoredBlob(playerId, record.blob);
    const img = typeof playerImageEl === "function"
      ? playerImageEl()
      : document.querySelector("#front-player");
    if (!img) return false;

    const layout = resolvedStoredLayout(playerId, record);
    if (layout && typeof saveImageLayout === "function") {
      saveImageLayout(playerId, layout);
    }

    // Clear the legacy image onload assignment before swapping sources so an old
    // handler cannot reset the restored image back to the default placement.
    img.onload = null;
    img.hidden = false;
    img.src = url;

    if (layout && typeof applyImageLayout === "function") {
      applyImageLayout(layout, false);
    }

    img.addEventListener("load", () => {
      if (typeof currentPlayerId === "function" && currentPlayerId() !== playerId) return;
      setImageStatus(`저장 이미지 복원됨 · ${img.naturalWidth}×${img.naturalHeight}px`);
    }, { once: true });

    return true;
  }

  async function sourceBlobForCurrentPlayer(playerId, img) {
    const pending = pendingFiles.get(playerId);
    if (pending) return { blob: pending, fileName: pending.name || "player-image" };

    const existing = await getRecord(playerId);
    if (existing?.blob) {
      return { blob: existing.blob, fileName: existing.fileName || "player-image" };
    }

    const src = img?.currentSrc || img?.src || "";
    if (!src) throw new Error("저장할 선수 이미지가 없습니다");

    const response = await fetch(src);
    if (!response.ok) throw new Error(`선수 이미지 읽기 실패: HTTP ${response.status}`);
    const blob = await response.blob();
    return { blob, fileName: src.split("/").pop()?.split("?")[0] || "player-image" };
  }

  async function saveCurrentPlayerImage() {
    const player = typeof currentPlayer === "function" ? currentPlayer() : null;
    if (!player?.player_id) throw new Error("선택된 선수가 없습니다");

    const img = typeof playerImageEl === "function"
      ? playerImageEl()
      : document.querySelector("#front-player");
    if (!img || img.hidden || !(img.currentSrc || img.src)) {
      throw new Error("저장할 선수 이미지가 없습니다");
    }

    const layout = typeof readEditor === "function"
      ? readEditor()
      : { x:0, y:0, width:900, scale:1 };

    if (typeof saveImageLayout === "function") {
      saveImageLayout(player.player_id, layout);
    }

    const { blob, fileName } = await sourceBlobForCurrentPlayer(player.player_id, img);
    await putRecord({
      playerId: player.player_id,
      blob,
      fileName,
      mimeType: blob.type || "application/octet-stream",
      layout: { ...layout },
      updatedAt: Date.now()
    });

    pendingFiles.delete(player.player_id);
    const url = installStoredBlob(player.player_id, blob);

    // setImageFile() leaves a legacy onload callback on the image element. Clear
    // it before switching to the durable Blob URL or it would reset X/Y/W/Scale.
    img.onload = null;
    img.src = url;
    if (typeof applyImageLayout === "function") applyImageLayout(layout, false);

    setImageStatus(
      `저장됨 · X ${Math.round(layout.x)} / Y ${Math.round(layout.y)} / W ${Math.round(layout.width)} / S ${Number(layout.scale).toFixed(2)}`
    );
  }

  const originalSetImageFile = typeof setImageFile === "function" ? setImageFile : null;
  if (originalSetImageFile) {
    setImageFile = function setImageFilePersistent(file) {
      const player = typeof currentPlayer === "function" ? currentPlayer() : null;
      if (player?.player_id && file?.type?.startsWith("image/")) {
        pendingFiles.set(player.player_id, file);
      }

      originalSetImageFile(file);

      const id = player?.player_id;
      const img = typeof playerImageEl === "function" ? playerImageEl() : null;
      if (id && img) {
        img.addEventListener("load", () => {
          if (typeof currentPlayerId === "function" && currentPlayerId() === id) {
            setImageStatus(`${file.name} · ${img.naturalWidth}×${img.naturalHeight}px · Save 필요`);
          }
        }, { once: true });
      }
    };
  }

  const originalRenderEditedPlayerImage = typeof renderEditedPlayerImage === "function"
    ? renderEditedPlayerImage
    : null;

  if (originalRenderEditedPlayerImage) {
    renderEditedPlayerImage = function renderEditedPlayerImagePersistent() {
      const playerId = typeof currentPlayerId === "function" ? currentPlayerId() : "";
      const cached = playerId ? persistentUrls.get(playerId) : null;

      if (cached && typeof playerImageObjectUrls !== "undefined") {
        playerImageObjectUrls.set(playerId, cached);
      }

      originalRenderEditedPlayerImage();

      if (playerId && !cached) {
        restoreSavedImage(playerId).catch(error => {
          console.error(`[TEAM YUKIES ${BUILD}] restore failed`, error);
          setImageStatus(`복원 실패: ${error.message || String(error)}`);
        });
      }
    };
  }

  function bindPersistenceUi() {
    const saveButton = document.querySelector("#img-save");
    if (saveButton) {
      saveButton.addEventListener("click", async () => {
        saveButton.disabled = true;
        try {
          setImageStatus("선수 이미지/배치 저장 중…");
          await saveCurrentPlayerImage();
        } catch (error) {
          console.error(`[TEAM YUKIES ${BUILD}] save failed`, error);
          setImageStatus(`저장 실패: ${error.message || String(error)}`);
        } finally {
          saveButton.disabled = false;
        }
      });
    }

    const removeButton = document.querySelector("#img-clear");
    if (removeButton) {
      removeButton.onclick = async () => {
        const player = typeof currentPlayer === "function" ? currentPlayer() : null;
        if (!player?.player_id) return;

        const id = player.player_id;
        pendingFiles.delete(id);

        const persistent = persistentUrls.get(id);
        if (persistent) revokeUrl(persistent);
        persistentUrls.delete(id);

        if (typeof playerImageObjectUrls !== "undefined") {
          const active = playerImageObjectUrls.get(id);
          if (active && active !== persistent) revokeUrl(active);
          playerImageObjectUrls.delete(id);
        }

        try { await deleteRecord(id); } catch (error) {
          console.error(`[TEAM YUKIES ${BUILD}] delete failed`, error);
        }

        player.player_image = null;
        const img = typeof playerImageEl === "function" ? playerImageEl() : document.querySelector("#front-player");
        if (img) {
          img.onload = null;
          img.hidden = true;
          img.removeAttribute("src");
        }
        setImageStatus("저장된 선수 이미지 제거됨");
      };
    }

    const resetButton = document.querySelector("#img-reset");
    if (resetButton) {
      const originalReset = resetButton.onclick;
      resetButton.onclick = event => {
        if (typeof originalReset === "function") originalReset.call(resetButton, event);
        const layout = typeof readEditor === "function" ? readEditor() : null;
        if (layout) {
          setImageStatus(`배치 초기화 · X ${Math.round(layout.x)} / Y ${Math.round(layout.y)} / W ${Math.round(layout.width)} / S ${Number(layout.scale).toFixed(2)}`);
        }
      };
    }

    window.TEAM_YUKIES_IMAGE_PERSISTENCE_BUILD = BUILD;
    console.info(`[TEAM YUKIES] player image persistence ${BUILD} active`);
  }

  window.addEventListener("beforeunload", () => {
    persistentUrls.forEach(revokeUrl);
  }, { once: true });

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", bindPersistenceUi, { once: true });
  } else {
    bindPersistenceUi();
  }
})();
