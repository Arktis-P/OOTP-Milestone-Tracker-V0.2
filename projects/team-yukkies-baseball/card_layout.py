from __future__ import annotations

CARD_WIDTH = 700
CARD_HEIGHT = 1050

FRONT = {
    "photo_outer": (20, 140, 660, 715),
    "photo_inner": (27, 147, 646, 701),
    "header": (20, 20, 660, 176),
    "logo": (35, 36, 155, 142),
    "name": (205, 46, 300, 46),
    "team": (205, 91, 300, 27),
    "ovr_label": (532, 42, 130, 28),
    "ovr_value": (522, 70, 150, 80),
    "position_badge": (29, 215, 124, 100),
    "position_text": (37, 232, 108, 56),
    "number_batter": (162, 225, 90, 48),
    "number_pitcher": (205, 120, 120, 34),
    "stats": (20, 865, 660, 110),
    "footer": (20, 978, 660, 42),
}

BACK_COMMON = {
    "header": (20, 20, 660, 185),
    "logo": (35, 38, 155, 145),
    "name": (205, 46, 355, 46),
    "team": (205, 91, 355, 26),
    "profile": (205, 119, 410, 32),
    "number": (600, 42, 64, 54),
}

BACK_BATTER = {
    "ratings": (20, 210, 660, 380),
    "fielding": (20, 595, 660, 230),
    "scouting": (20, 830, 660, 185),
}

BACK_PITCHER = {
    "ratings": (20, 210, 660, 325),
    "velocity": (20, 540, 660, 70),
    "pitch_mix": (20, 615, 660, 210),
    "scouting": (20, 830, 660, 185),
}

RATING = {
    "title_x": 22,
    "title_y": 12,
    "title_w": 300,
    "title_h": 32,
    "label_x": 22,
    "bar_x": 160,
    "bar_w": 410,
    "value_x": 585,
    "value_w": 50,
}
