TEAMS = [
    (1, "Seoul Meteors", "SEO", 1),
    (2, "Busan Waves", "BUS", 0),
    (3, "Incheon Harbor", "INC", 0),
]

PLAYERS = [
    (101, 1, "Ji-ho Park", "박지호", "1B", 34, 1),
    (102, 1, "Min-jun Kim", "김민준", "CF", 31, 1),
    (103, 1, "Hyun-woo Lee", "이현우", "SP", 32, 1),
    (104, 1, "Jun-seo Choi", "최준서", "SS", 27, 1),
    (105, 1, "Woo-jin Han", "한우진", "C", 29, 1),
    (201, 2, "Do-yun Kang", "강도윤", "RF", 30, 1),
    (202, 2, "Si-woo Jeong", "정시우", "SP", 35, 1),
    (301, 3, "Ye-jun Song", "송예준", "3B", 25, 1),
]

BATTING = [
    (101, 2024, 148, 634, 565, 170, 31, 102, 58, 92, 4, .301, .369, .497, 5.1),
    (101, 2025, 151, 647, 571, 174, 35, 108, 64, 95, 3, .305, .377, .516, 5.7),
    (101, 2026, 103, 441, 392, 123, 31, 96, 41, 63, 2, .314, .387, .523, 5.1),
    (102, 2024, 154, 682, 611, 191, 24, 81, 58, 104, 28, .313, .371, .462, 6.0),
    (102, 2025, 149, 658, 589, 183, 27, 88, 55, 101, 24, .311, .369, .471, 5.8),
    (102, 2026, 101, 452, 404, 126, 20, 67, 39, 69, 19, .312, .374, .478, 4.4),
    (104, 2024, 143, 595, 538, 151, 16, 64, 45, 110, 21, .281, .341, .421, 4.2),
    (104, 2025, 150, 632, 566, 166, 19, 72, 52, 116, 25, .293, .356, .446, 5.0),
    (104, 2026, 99, 419, 372, 110, 15, 54, 38, 72, 17, .296, .359, .452, 3.5),
    (105, 2024, 119, 442, 395, 101, 14, 58, 37, 88, 2, .256, .319, .398, 2.7),
    (105, 2025, 128, 477, 421, 113, 18, 66, 45, 91, 1, .268, .337, .427, 3.2),
    (105, 2026, 87, 329, 291, 80, 12, 47, 31, 61, 1, .275, .348, .436, 2.4),
    (201, 2026, 104, 466, 414, 132, 26, 79, 42, 77, 11, .319, .379, .512, 4.6),
    (301, 2026, 97, 402, 361, 104, 17, 61, 33, 81, 8, .288, .348, .455, 3.0),
]

PITCHING = [
    (103, 2024, 31, 31, 15, 8, 0, 186.2, 192, 3.42, 1.18, 4.8),
    (103, 2025, 32, 32, 17, 7, 0, 194.1, 207, 3.18, 1.12, 5.5),
    (103, 2026, 22, 22, 12, 5, 0, 137.0, 151, 2.96, 1.09, 4.1),
    (202, 2026, 21, 21, 9, 8, 0, 128.2, 118, 3.88, 1.27, 2.4),
]

AWARDS = [
    (101, 2022, "All-Star"), (101, 2023, "Gold Glove"), (101, 2025, "All-Star"),
    (102, 2024, "All-Star"), (102, 2025, "Gold Glove"),
    (103, 2025, "Pitcher of the Year"), (104, 2025, "Gold Glove"),
]

MILESTONES = [
    ("player", 101, "career", "H", "2,500 Hits", 2431, 2500, 0, None, 10),
    ("player", 101, "career", "HR", "400 Home Runs", 382, 400, 0, None, 20),
    ("player", 101, "career", "RBI", "1,500 RBI", 1438, 1500, 0, None, 30),
    ("player", 102, "career", "H", "2,000 Hits", 1884, 2000, 0, None, 10),
    ("player", 102, "career", "HR", "300 Home Runs", 284, 300, 0, None, 20),
    ("player", 103, "career", "W", "150 Wins", 148, 150, 0, None, 10),
    ("player", 103, "career", "SO", "2,000 Strikeouts", 1876, 2000, 0, None, 20),
    ("player", 104, "career", "H", "1,500 Hits", 1391, 1500, 0, None, 10),
    ("player", 105, "career", "G", "1,000 Games", 964, 1000, 0, None, 10),
    ("player", 101, "season", "HR", "40 Home Runs", 31, 40, 0, 2026, 10),
    ("player", 102, "season", "H", "200 Hits", 126, 200, 0, 2026, 10),
    ("player", 103, "season", "W", "20 Wins", 12, 20, 0, 2026, 10),
    ("player", 101, "award", "ALLSTAR", "10 All-Star selections", 8, 10, 0, None, 10),
    ("team", 1, "career", "W", "5,000 Team Wins", 4976, 5000, 0, None, 10),
    ("player", 201, "career", "HR", "300 Home Runs", 271, 300, 0, None, 10),
]

SETTINGS = [
    ("save_folder", ""),
    ("theme", "dark"),
    ("accent", "blue"),
    ("density", "compact"),
]


def seed_sample_data(conn) -> None:
    conn.executemany("INSERT INTO teams VALUES (?, ?, ?, ?)", TEAMS)
    conn.executemany("INSERT INTO players VALUES (?, ?, ?, ?, ?, ?, ?)", PLAYERS)
    conn.executemany(
        """INSERT INTO batting_seasons (player_id, season, g, pa, ab, h, hr, rbi, r, bb, sb, avg, obp, slg, war)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        BATTING,
    )
    conn.executemany(
        """INSERT INTO pitching_seasons (player_id, season, g, gs, w, l, sv, ip, so, era, whip, war)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        PITCHING,
    )
    conn.executemany("INSERT INTO awards(player_id, season, award_name) VALUES (?, ?, ?)", AWARDS)

    conn.executemany(
        """INSERT INTO milestones(entity_type, entity_id, scope, stat_key, label,
        current_value, target_value, achieved, achieved_season, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        MILESTONES,
    )
    conn.executemany("INSERT INTO app_settings(key, value) VALUES (?, ?)", SETTINGS)
