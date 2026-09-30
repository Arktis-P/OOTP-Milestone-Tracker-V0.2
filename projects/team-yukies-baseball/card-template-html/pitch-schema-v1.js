(() => {
  if (!Array.isArray(PITCHES)) return;

  const normalizeCSVRowBase = normalizeCSVRow;
  normalizeCSVRow = function(row) {
    const player = normalizeCSVRowBase(row);
    [
      "pitch_circle_change",
      "pitch_knuckle_curve",
      "pitch_forkball",
      "pitch_screwball"
    ].forEach(key => {
      player[key] = numberOrNull(player[key]);
    });
    return player;
  };

  const extraPitches = [
    ["CIRCLE CHG", 0, 5, "pitch_circle_change"],
    ["FORKBALL", 1, 5, "pitch_forkball"],
    ["KNUCKLE CV", 0, 6, "pitch_knuckle_curve"],
    ["SCREWBALL", 1, 6, "pitch_screwball"]
  ];

  extraPitches.forEach(pitch => {
    const key = pitch[3];
    if (!PITCHES.some(([, , , existingKey]) => existingKey === key)) {
      PITCHES.push(pitch);
    }
  });

  const style = document.createElement("style");
  style.dataset.teamYukiesPitchSchema = "v2";
  style.textContent = `
    .pitch-list { height: 302px; }
    .pitch-slot[data-row="5"] { top: 220px; }
    .pitch-slot[data-row="6"] { top: 264px; }
  `;
  document.head.appendChild(style);
})();
