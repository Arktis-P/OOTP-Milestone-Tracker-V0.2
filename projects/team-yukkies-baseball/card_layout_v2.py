from __future__ import annotations

CARD_WIDTH = 900
CARD_HEIGHT = 1600
ASPECT_RATIO = (9, 16)

PALETTE = {
    "ink": "#10224A",
    "navy": "#123A67",
    "blue": "#2376D8",
    "blue_bright": "#3688EA",
    "silver": "#C9D0D7",
    "silver_dark": "#8E9AA5",
    "paper": "#F7F8FA",
    "paper_alt": "#EEF2F6",
    "track": "#D7DDE4",
    "white": "#FFFFFF",
}

FRONT = {
    "header": (28, 28, 844, 260),
    "logo": (54, 56, 180, 168),
    "name": (270, 64, 390, 62),
    "team": (270, 124, 390, 42),
    "ovr_label": (700, 54, 142, 44),
    "ovr_value": (694, 94, 154, 112),
    "photo_outer": (34, 220, 832, 1122),
    "photo_inner": (42, 228, 816, 1106),
    "position_badge": (40, 278, 128, 112),
    "position_text": (48, 294, 112, 78),
    "number": (170, 284, 110, 90),
    "handedness": (742, 284, 114, 74),
    "stats": (28, 1346, 844, 180),
    "footer": (28, 1528, 844, 44),
}

BACK_COMMON = {
    "header": (28, 28, 844, 268),
    "logo": (54, 52, 176, 166),
    "name": (270, 58, 430, 58),
    "team": (270, 116, 430, 38),
    "profile": (270, 158, 470, 44),
    "franchise": (270, 202, 470, 34),
    "number": (742, 56, 100, 72),
}

BACK_BATTER = {
    "ratings": (28, 302, 844, 550),
    "fielding": (28, 858, 844, 330),
    "scouting": (28, 1194, 844, 378),
}

BACK_PITCHER = {
    "ratings": (28, 302, 844, 510),
    "velocity": (28, 818, 844, 92),
    "pitch_arsenal": (28, 916, 844, 280),
    "scouting": (28, 1202, 844, 370),
}

RATING = {
    "title_left": 32,
    "title_top": 20,
    "label_width": 190,
    "bar_left": 205,
    "bar_right_margin": 80,
    "value_width": 54,
    "scale_top": 74,
    "rows_top": 106,
}


def scale_rect(rect: tuple[int, int, int, int], width: int, height: int):
    sx = width / CARD_WIDTH
    sy = height / CARD_HEIGHT
    x, y, w, h = rect
    return (round(x * sx), round(y * sy), round(w * sx), round(h * sy))
