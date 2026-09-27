(() => {
  const BUILD = "pitcher-front-v2-20260927";
  const PITCHER_LABELS = ["STF", "MOV", "CTL", "CMD", "PIT", "STA"];

  function injectStyles() {
    if (document.getElementById("pitcher-front-v2-style")) return;

    const style = document.createElement("style");
    style.id = "pitcher-front-v2-style";
    style.textContent = `
      .front__pitcher-labels {
        position: absolute;
        left: 18px;
        top: 1079px;
        width: 864px;
        height: 39px;
        display: grid;
        grid-template-columns: repeat(6, 144px);
        background: var(--navy);
        color: var(--white);
        pointer-events: none;
      }
      .front__pitcher-labels[hidden] {
        display: none !important;
      }
      .front__pitcher-label {
        display: grid;
        place-items: center;
        height: 39px;
        color: var(--white);
        font-family: "Esamanru", sans-serif;
        font-size: 30px;
        font-weight: 700;
        line-height: 39px;
        border-right: 2px solid var(--white);
      }
      .front__pitcher-label:last-child {
        border-right: 0;
      }
    `;
    document.head.appendChild(style);
  }

  function ensurePitcherLabels(root) {
    const data = root.querySelector(".card__data");
    if (!data) return null;

    let host = data.querySelector(".front__pitcher-labels");
    if (!host) {
      host = document.createElement("div");
      host.className = "front__pitcher-labels";
      host.hidden = true;

      PITCHER_LABELS.forEach(label => {
        const cell = document.createElement("div");
        cell.className = "front__pitcher-label";
        cell.textContent = label;
        host.appendChild(cell);
      });

      data.appendChild(host);
    }

    return host;
  }

  function renderPitcherValues(root, player) {
    const host = root.querySelector(".front__stats");
    if (!host) return;

    host.replaceChildren();
    [
      player.stuff,
      player.movement,
      player.control,
      player.command,
      player.pitchability,
      player.stamina
    ].forEach(value => {
      const cell = document.createElement("div");
      cell.className = "front__stat";
      cell.textContent = typeof rated === "function" && rated(value) ? value : "-";
      host.appendChild(cell);
    });
  }

  if (typeof renderFront !== "function") {
    console.error(`[TEAM YUKIES ${BUILD}] renderFront was not available`);
    return;
  }

  injectStyles();
  const originalRenderFront = renderFront;

  renderFront = function renderFrontWithPitchability(root, player) {
    originalRenderFront(root, player);

    const labels = ensurePitcherLabels(root);
    const isPitcher = player?.player_type === "PITCHER";
    if (labels) labels.hidden = !isPitcher;

    if (isPitcher) renderPitcherValues(root, player);
  };

  window.TEAM_YUKIES_PITCHER_FRONT_BUILD = BUILD;
  console.info(`[TEAM YUKIES] pitcher front ${BUILD} active`);
})();
