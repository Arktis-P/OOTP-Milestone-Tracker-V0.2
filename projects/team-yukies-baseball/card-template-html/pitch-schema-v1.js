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
  style.dataset.teamYukiesPitchSchema = "v5";
  style.textContent = `
    /*
     * The overlay is presentation-only. The pitch labels are always rendered
     * by the DOM, so give the dynamic arsenal its own clean canvas. This also
     * masks any legacy labels that may still be baked into an older/cached
     * pitcher overlay without covering the velocity badge or helper text.
     */
    .pitch-list {
      height: 190px;
      overflow: hidden;
      background: #F9F9F9;
      z-index: 2;
    }

    .pitch-slot {
      height: 24px;
      z-index: 3;
    }

    .pitch-slot[data-row="0"] { top: 0; }
    .pitch-slot[data-row="1"] { top: 27px; }
    .pitch-slot[data-row="2"] { top: 54px; }
    .pitch-slot[data-row="3"] { top: 81px; }
    .pitch-slot[data-row="4"] { top: 108px; }
    .pitch-slot[data-row="5"] { top: 135px; }
    .pitch-slot[data-row="6"] { top: 162px; }

    .pitch-label,
    .pitch-value {
      height: 24px;
      line-height: 24px;
    }

    .pitch-label {
      padding-left: 8px;
      font-size: 20px;
      letter-spacing: -0.03em;
      white-space: nowrap;
      overflow: hidden;
    }

    .pitch-value {
      font-size: 22px;
    }
  `;
  document.head.appendChild(style);
})();
