(() => {
  if (!Array.isArray(PITCHES) || PITCHES.some(([, , , key]) => key === "pitch_forkball")) return;

  const normalizeCSVRowBase = normalizeCSVRow;
  normalizeCSVRow = function(row) {
    const player = normalizeCSVRowBase(row);
    player.pitch_forkball = numberOrNull(player.pitch_forkball);
    return player;
  };

  PITCHES.push(["FORKBALL", 1, 5, "pitch_forkball"]);

  const style = document.createElement("style");
  style.dataset.teamYukiesPitchSchema = "v1";
  style.textContent = `
    .pitch-list { height: 258px; }
    .pitch-slot[data-row="5"] { top: 220px; }
  `;
  document.head.appendChild(style);
})();
