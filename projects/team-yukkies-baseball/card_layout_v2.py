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
    # Front identity: photo first, metadata second.
    "front_name": 52,
    "front_name_min": 44,
    "front_team": 24,
    "ovr_label": 34,
    "ovr_value": 110,
    "position": 58,
    "number": 58,
    "handedness": 44,
    "stat_label": 26,
    "stat_value": 52,
    "stat_value_velocity": 48,
    "stat_unit": 18,
    "footer": 18,

    # Back identity.
    "back_name": 50,
    "back_name_min": 42,
    "back_team": 24,
    "back_profile": 28,
    "back_profile_min": 24,
    "back_franchise": 24,
    "back_number": 56,
    "back_tagline": 20,

    # Back data hierarchy: restrained, print-card-like.
    "section_title": 34,
    "scale_note": 18,
    "scale_tick": 20,
    "rating_label": 28,
    "rating_value": 30,
    "position_chip": 26,
    "position_chip_value": 20,
    "field_role": 22,
    "field_value": 28,
    "scouting_body": 22,
    "scouting_body_min": 17,

    # Pitcher-only data.
    "velocity_value": 72,
    "velocity_unit": 34,
    "pitch_label": 24,
    "pitch_label_min": 20,
    "pitch_value": 30,
    "small_note": 18,
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
    "ratings": (35, 310, 832, 500),
    "fielding": (35, 820, 832, 290),
    "scouting": (35, 1120, 832, 421),
}

BACK_PITCHER = {
    "ratings": (35, 310, 832, 440),
    "velocity": (35, 760, 832, 92),
    "pitch_arsenal": (35, 862, 832, 248),
    "scouting": (35, 1120, 832, 421),
}

RATING = {
    "title_left": 32,
    "title_top": 18,
    "label_width": 194,
    "bar_left": 206,
    "bar_right_margin": 82,
    "value_width": 57,
    "scale_top": 68,
    "rows_top": 98,
}


def scale_rect(rect: tuple[int, int, int, int], width: int, height: int):
    sx = width / CARD_WIDTH
    sy = height / CARD_HEIGHT
    x, y, w, h = rect
    return (round(x * sx), round(y * sy), round(w * sx), round(h * sy))
