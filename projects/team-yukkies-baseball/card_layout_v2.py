from __future__ import annotations

CARD_WIDTH = 900
CARD_HEIGHT = 1600
ASPECT_RATIO = (9, 16)
REFERENCE_WIDTH = 941
REFERENCE_HEIGHT = 1672

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

# Pixel sizes are deliberately tied to the 900 x 1600 render canvas.
# The reference cards are 941 x 1672, so these values preserve their
# visual hierarchy instead of depending on monitor DPI / point sizes.
TYPOGRAPHY = {
    "front_name": 70,
    "front_name_min": 54,
    "front_team": 38,
    "ovr_label": 46,
    "ovr_value": 126,
    "position": 78,
    "number": 74,
    "handedness": 62,
    "stat_label": 39,
    "stat_value": 72,
    "stat_value_velocity": 62,
    "stat_unit": 24,
    "footer": 25,
    "back_name": 66,
    "back_name_min": 50,
    "back_team": 36,
    "back_profile": 36,
    "back_profile_min": 29,
    "back_franchise": 30,
    "back_number": 70,
    "back_tagline": 27,
    "section_title": 54,
    "scale_note": 28,
    "scale_tick": 27,
    "rating_label": 40,
    "rating_value": 43,
    "position_chip": 34,
    "position_chip_value": 26,
    "field_role": 31,
    "field_value": 38,
    "scouting_body": 35,
    "velocity_value": 84,
    "velocity_unit": 45,
    "pitch_label": 35,
    "pitch_label_min": 27,
    "pitch_value": 40,
    "small_note": 22,
}

# Coordinates below are the reference composition mapped from 941 x 1672
# to the canonical 900 x 1600 canvas. Do not independently resize sections:
# keep their relative proportions and adjust only through a new reference pass.
FRONT = {
    "header": (35, 40, 832, 226),
    "logo": (53, 61, 206, 201),
    "name": (270, 79, 373, 71),
    "team": (293, 145, 340, 53),
    "ovr_label": (693, 62, 130, 53),
    "ovr_value": (676, 102, 160, 119),
    "photo_outer": (35, 209, 832, 1081),
    "photo_inner": (43, 216, 816, 1066),
    "position_badge": (44, 278, 133, 114),
    "position_text": (49, 288, 122, 87),
    "number": (177, 270, 139, 112),
    "handedness": (711, 271, 139, 77),
    "stats": (35, 1299, 832, 172),
    "footer": (35, 1471, 832, 66),
}

BACK_COMMON = {
    "header": (35, 40, 832, 258),
    "logo": (53, 61, 206, 201),
    "name": (270, 79, 414, 68),
    "team": (278, 145, 406, 47),
    "profile": (278, 188, 470, 43),
    "franchise": (278, 230, 470, 34),
    "number": (733, 61, 102, 74),
    "tagline": (714, 142, 122, 92),
}

BACK_BATTER = {
    "ratings": (35, 305, 832, 528),
    "fielding": (35, 838, 832, 316),
    "scouting": (35, 1164, 832, 377),
}

BACK_PITCHER = {
    "ratings": (35, 305, 832, 475),
    "velocity": (35, 786, 832, 94),
    "pitch_arsenal": (35, 888, 832, 284),
    "scouting": (35, 1180, 832, 361),
}

RATING = {
    "title_left": 32,
    "title_top": 18,
    "label_width": 194,
    "bar_left": 206,
    "bar_right_margin": 82,
    "value_width": 57,
    "scale_top": 80,
    "rows_top": 122,
}


def scale_rect(rect: tuple[int, int, int, int], width: int, height: int):
    sx = width / CARD_WIDTH
    sy = height / CARD_HEIGHT
    x, y, w, h = rect
    return (round(x * sx), round(y * sy), round(w * sx), round(h * sy))
