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
  style.dataset.teamYukiesPitchSchema = "v3";
  style.textContent = `
    /* 7 rows per column must stay inside the original 214px arsenal area. */
    .pitch-list {
      height: 214px;
    }

    .pitch-slot {
      height: 28px;
    }

    .pitch-slot[data-row="0"] { top: 0; }
    .pitch-slot[data-row="1"] { top: 31px; }
    .pitch-slot[data-row="2"] { top: 62px; }
    .pitch-slot[data-row="3"] { top: 93px; }
    .pitch-slot[data-row="4"] { top: 124px; }
    .pitch-slot[data-row="5"] { top: 155px; }
    .pitch-slot[data-row="6"] { top: 186px; }

    .pitch-label,
    .pitch-value {
      height: 28px;
      font-size: 24px;
      line-height: 28px;
    }

    .pitch-label {
      padding-left: 8px;
      letter-spacing: -0.02em;
    }
  `;
  document.head.appendChild(style);
})();
