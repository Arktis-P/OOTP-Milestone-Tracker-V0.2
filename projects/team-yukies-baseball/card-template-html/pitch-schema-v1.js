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
  style.dataset.teamYukiesPitchSchema = "v6";
  style.textContent = `
    /* 7 rows per column, expanded to use the arsenal body without touching
       the helper line printed near the bottom of the overlay. */
    .pitch-list {
      height: 210px;
      overflow: hidden;
      background: #F9F9F9;
      z-index: 2;
    }

    .pitch-slot {
      height: 26px;
      z-index: 3;
    }

    .pitch-slot[data-row="0"] { top: 0; }
    .pitch-slot[data-row="1"] { top: 30px; }
    .pitch-slot[data-row="2"] { top: 60px; }
    .pitch-slot[data-row="3"] { top: 90px; }
    .pitch-slot[data-row="4"] { top: 120px; }
    .pitch-slot[data-row="5"] { top: 150px; }
    .pitch-slot[data-row="6"] { top: 180px; }

    .pitch-label,
    .pitch-value {
      height: 26px;
      line-height: 26px;
    }

    .pitch-label {
      padding-left: 8px;
      font-size: 22px;
      letter-spacing: -0.03em;
      white-space: nowrap;
      overflow: hidden;
    }

    .pitch-value {
      font-size: 24px;
    }
  `;
  document.head.appendChild(style);
})();
