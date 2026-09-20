from __future__ import annotations

CARD_WIDTH = 900
CARD_HEIGHT = 1600
ASPECT_RATIO = (9, 16)

PALETTE = {
    "ink": "#0B1942",
    "navy": "#123B67",
    "blue": "#1778D6",
    "blue_bright": "#2D95F4",
    "silver": "#C8D0D7",
    "silver_dark": "#7F8C98",
    "paper": "#F8F9FA",
    "paper_alt": "#EEF2F5",
    "track": "#D7DDE3",
    "white": "#FFFFFF",
}

# Reference images are 941 x 1672. These coordinates preserve the same
# visual hierarchy on a normalized 900 x 1600 canvas.
FRONT = {
    "header": (46, 54, 806, 198),
    "logo": (60, 74, 184, 144),
    "name": (276, 70, 390, 62),
    "team": (286, 126, 352, 42),
    "ovr_label": (690, 67, 142, 42),
    "ovr_value": (678, 103, 164, 106),
    "photo_outer": (45, 205, 807, 1139),
    "photo_inner": (53, 213, 791, 1122),
    "position_badge": (49, 270, 124, 113),
    "position_text": (55, 286, 112, 79),
    "number": (176, 265, 132, 103),
    "handedness": (713, 270, 140, 90),
    "stats": (43, 1348, 814, 196),
    "footer": (43, 1538, 814, 42),
}

BACK_COMMON = {
    "header": (45, 54, 810, 240),
    "logo": (61, 72, 185, 170),
    "name": (276, 69, 428, 58),
    "team": (276, 122, 430, 38),
    "profile": (276, 160, 438, 42),
    "franchise": (276, 199, 438, 34),
    "number": (738, 61, 100, 72),
    "tagline": (718, 143, 120, 82),
}

BACK_BATTER = {
    "ratings": (43, 304, 814, 542),
    "fielding": (43, 856, 814, 330),
    "scouting": (43, 1196, 814, 378),
}

BACK_PITCHER = {
    "ratings": (43, 304, 814, 502),
    "velocity": (43, 816, 814, 92),
    "pitch_arsenal": (43, 918, 814, 282),
    "scouting": (43, 1210, 814, 364),
}

RATING = {
    "title_left": 32,
    "title_top": 18,
    "label_width": 190,
    "bar_left": 205,
    "bar_right_margin": 80,
    "value_width": 54,
    "scale_top": 76,
    "rows_top": 112,
}


def scale_rect(rect: tuple[int, int, int, int], width: int, height: int):
    sx = width / CARD_WIDTH
    sy = height / CARD_HEIGHT
    x, y, w, h = rect
    return (round(x * sx), round(y * sy), round(w * sx), round(h * sy))
