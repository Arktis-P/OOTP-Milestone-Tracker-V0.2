from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer


CARD_WIDTH = 750
CARD_HEIGHT = 1050

INK = QColor("#14233A")
MUTED = QColor("#7A8795")
ACCENT = QColor("#2F7FF6")
NAVY = QColor("#153B61")
WHITE = QColor("#FFFFFF")
PLACEHOLDER = QColor("#EEF2F5")
LINE = QColor("#D7DEE6")
SOFT = QColor("#F4F7F9")


def _short_hand(value: str) -> str:
    return {"RIGHT": "R", "LEFT": "L", "SWITCH": "S"}.get(
        value.upper(), value[:1].upper() or "-"
    )


class SvgComponentLibrary:
    def __init__(self, root: Path) -> None:
        self.root = root
        self._cache: dict[str, QSvgRenderer] = {}

    def renderer(self, name: str) -> QSvgRenderer:
        if name not in self._cache:
            self._cache[name] = QSvgRenderer(str(self.root / f"{name}.svg"))
        return self._cache[name]

    def draw(self, painter: QPainter, name: str, rect: QRectF) -> None:
        renderer = self.renderer(name)
        if renderer.isValid():
            renderer.render(painter, rect)


class ModularCardRenderer:
    """Baseball-card renderer assembled from external SVG components."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.components = SvgComponentLibrary(
            self.project_dir / "templates" / "components"
        )

    def render(self, player: Any, side: str) -> QImage:
        image = QImage(
            CARD_WIDTH,
            CARD_HEIGHT,
            QImage.Format_ARGB32_Premultiplied,
        )
        image.fill(WHITE)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        self.components.draw(
            painter,
            "frame_card",
            QRectF(0, 0, CARD_WIDTH, CARD_HEIGHT),
        )

        if side == "back":
            self._draw_back(painter, player)
        else:
            self._draw_front(painter, player)

        painter.end()
        return image

    def _font(self, size: int, bold: bool = False) -> QFont:
        font = QFont("Malgun Gothic")
        font.setPointSize(size)
        font.setWeight(QFont.Bold if bold else QFont.Normal)
        return font

    def _text(
        self,
        painter: QPainter,
        rect: QRectF,
        text: str,
        size: int,
        color: QColor = INK,
        bold: bool = False,
        align: Qt.AlignmentFlag = Qt.AlignLeft | Qt.AlignVCenter,
    ) -> None:
        painter.setPen(color)
        painter.setFont(self._font(size, bold))
        painter.drawText(rect, align, text)

    def _draw_image(
        self,
        painter: QPainter,
        path: Path,
        rect: QRectF,
        *,
        contain: bool = False,
    ) -> bool:
        if not path.exists():
            return False

        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return False

        mode = Qt.KeepAspectRatio if contain else Qt.KeepAspectRatioByExpanding
        scaled = pixmap.scaled(
            int(rect.width()),
            int(rect.height()),
            mode,
            Qt.SmoothTransformation,
        )

        if contain:
            target = QRectF(0, 0, scaled.width(), scaled.height())
            target.moveCenter(rect.center())
            painter.drawPixmap(target, scaled, QRectF(scaled.rect()))
            return True

        sx = max(0, (scaled.width() - int(rect.width())) // 2)
        sy = max(0, (scaled.height() - int(rect.height())) // 2)
        painter.drawPixmap(
            rect,
            scaled,
            QRectF(sx, sy, rect.width(), rect.height()),
        )
        return True

    def _front_stats(self, player: Any) -> list[tuple[str, str]]:
        if player.is_pitcher:
            return [
                ("STF", str(player.number("stuff"))),
                ("MOV", str(player.number("movement"))),
                ("CTL", str(player.number("control"))),
                ("CMD", str(player.number("command"))),
                ("STA", str(player.number("stamina"))),
                ("VEL", str(player.number("velocity_kmh"))),
            ]

        fld_key = f"def_{player.position.lower()}"
        speed = round(
            (player.number("baserunning") + player.number("stealing")) / 2
        )
        return [
            ("CON", str(player.number("contact"))),
            ("POW", str(player.number("power"))),
            ("GAP", str(player.number("gap"))),
            ("EYE", str(player.number("eye"))),
            ("SPD", str(speed)),
            ("FLD", str(player.number(fld_key))),
        ]

    def _draw_front(self, painter: QPainter, player: Any) -> None:
        # Reference composition: the artwork is the dominant layer and extends behind
        # the top identity banner. Header/OVR/logo are then composited above it.
        photo_frame = QRectF(30, 150, 690, 710)
        photo_inner = QRectF(38, 158, 674, 694)

        clip = QPainterPath()
        clip.addRect(photo_inner)
        painter.save()
        painter.setClipPath(clip)

        if not self._draw_image(painter, player.player_image, photo_inner):
            painter.fillRect(photo_inner, PLACEHOLDER)
            self._text(
                painter,
                QRectF(80, 438, 590, 48),
                "PLAYER IMAGE",
                17,
                MUTED,
                True,
                Qt.AlignCenter,
            )
            self._text(
                painter,
                QRectF(80, 484, 590, 30),
                "우측 패널에서 이미지를 등록하세요",
                9,
                MUTED,
                False,
                Qt.AlignCenter,
            )

        painter.restore()
        self.components.draw(painter, "frame_image", photo_frame)

        # Identity header overlays the photograph, like the supplied baseball-card reference.
        header = QRectF(30, 30, 690, 168)
        self.components.draw(painter, "panel_header", header)

        logo_rect = QRectF(44, 44, 160, 146)
        if not self._draw_image(
            painter,
            player.team_logo,
            logo_rect,
            contain=True,
        ):
            self.components.draw(painter, "logo_slot", logo_rect)
            self._text(
                painter,
                logo_rect,
                "TEAM",
                8,
                MUTED,
                True,
                Qt.AlignCenter,
            )

        self._text(
            painter,
            QRectF(224, 48, 330, 52),
            player.name,
            23,
            INK,
            True,
        )
        self._text(
            painter,
            QRectF(224, 96, 330, 28),
            player.team_name.upper(),
            9,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(224, 124, 330, 24),
            player.get("series"),
            7,
            MUTED,
            False,
        )

        ovr_rect = QRectF(565, 41, 140, 145)
        self.components.draw(painter, "badge_ovr", ovr_rect)
        self._text(
            painter,
            QRectF(580, 54, 110, 28),
            "OVR",
            8,
            WHITE,
            True,
            Qt.AlignCenter,
        )
        self._text(
            painter,
            QRectF(575, 78, 120, 80),
            str(player.number("overall")),
            30,
            WHITE,
            True,
            Qt.AlignCenter,
        )

        # Position plate overlaps the upper-left of the artwork.
        pos_rect = QRectF(39, 214, 122, 114)
        self.components.draw(painter, "badge_position", pos_rect)
        self._text(
            painter,
            QRectF(49, 228, 102, 56),
            player.position,
            26,
            WHITE,
            True,
            Qt.AlignCenter,
        )
        self._text(
            painter,
            QRectF(171, 224, 100, 52),
            f"#{player.get('uniform_number', '-')}",
            20,
            NAVY,
            True,
        )

        bats = _short_hand(player.get("bats"))
        throws = _short_hand(player.get("throws"))
        profile = (
            player.get("arm_slot").replace("_", " ").title()
            if player.is_pitcher and player.get("arm_slot")
            else f"{bats}/{throws}"
        )
        self._text(
            painter,
            QRectF(171, 268, 215, 28),
            profile,
            9,
            MUTED,
            True,
        )

        # Bottom summary strip: compact, nearly full card width.
        stats = self._front_stats(player)
        start_x = 30
        gap = 6
        cell_w = (690 - gap * 5) / 6

        for index, (label, value) in enumerate(stats):
            x = start_x + index * (cell_w + gap)
            rect = QRectF(x, 870, cell_w, 106)
            self.components.draw(painter, "stat_cell", rect)
            self._text(
                painter,
                QRectF(x + 5, 878, cell_w - 10, 26),
                label,
                8,
                MUTED,
                True,
                Qt.AlignCenter,
            )

            suffix = " km/h" if label == "VEL" else ""
            self._text(
                painter,
                QRectF(x + 5, 906, cell_w - 10, 48),
                f"{value}{suffix}",
                10 if label == "VEL" else 18,
                NAVY,
                True,
                Qt.AlignCenter,
            )

        self.components.draw(
            painter,
            "divider",
            QRectF(72, 986, 606, 4),
        )
        self._text(
            painter,
            QRectF(72, 991, 606, 22),
            "TEAM YUKKIES",
            7,
            MUTED,
            True,
            Qt.AlignCenter,
        )

    def _draw_back(self, painter: QPainter, player: Any) -> None:
        # Reference card proportions:
        # header ~16%, batter ratings ~36%, fielding ~22%, report ~17%.
        # Pitcher uses a shorter rating block to make room for velocity + pitch mix.
        header = QRectF(30, 30, 690, 170)
        self.components.draw(painter, "panel_header", header)

        logo_rect = QRectF(46, 47, 142, 136)
        if not self._draw_image(
            painter,
            player.team_logo,
            logo_rect,
            contain=True,
        ):
            self._text(
                painter,
                logo_rect,
                "TEAM",
                8,
                MUTED,
                True,
                Qt.AlignCenter,
            )

        self._text(
            painter,
            QRectF(215, 49, 390, 46),
            player.name,
            22,
            INK,
            True,
        )
        self._text(
            painter,
            QRectF(215, 91, 390, 25),
            player.team_name.upper(),
            8,
            MUTED,
            True,
        )

        bats = _short_hand(player.get("bats"))
        throws = _short_hand(player.get("throws"))
        arm_slot = (
            f" / {player.get('arm_slot').replace('_', ' ').title()}"
            if player.is_pitcher and player.get("arm_slot")
            else ""
        )
        self._text(
            painter,
            QRectF(215, 119, 420, 31),
            f"{player.position} / {bats}-{throws}{arm_slot}",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(625, 48, 66, 50),
            f"#{player.get('uniform_number', '-')}",
            20,
            MUTED,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

        rows = (
            [
                ("STUFF", "stuff"),
                ("MOVEMENT", "movement"),
                ("CONTROL", "control"),
                ("COMMAND", "command"),
                ("STAMINA", "stamina"),
                ("FIELDING", "pitcher_fielding"),
            ]
            if player.is_pitcher
            else [
                ("CONTACT", "contact"),
                ("POWER", "power"),
                ("GAP", "gap"),
                ("EYE", "eye"),
                ("BASERUNNING", "baserunning"),
                ("STEALING", "stealing"),
                ("ARM", "arm"),
            ]
        )

        if player.is_pitcher:
            rating_panel = QRectF(30, 208, 690, 326)
            start_y = 255
            row_h = 43
        else:
            rating_panel = QRectF(30, 208, 690, 374)
            start_y = 258
            row_h = 41

        self.components.draw(painter, "panel_section", rating_panel)
        self._text(
            painter,
            QRectF(52, 222, 320, 32),
            "20–80 RATING BREAKDOWN",
            11,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(472, 224, 218, 28),
            "20   30   40   50   60   70   80",
            7,
            MUTED,
            False,
            Qt.AlignRight | Qt.AlignVCenter,
        )

        for index, (label, key) in enumerate(rows):
            self._draw_rating_row(
                painter,
                QRectF(52, start_y + index * row_h, 638, row_h - 5),
                label,
                player.number(key),
            )

        if player.is_pitcher:
            self._draw_pitcher_lower(painter, player)
        else:
            self._draw_batter_lower(painter, player)

    def _draw_rating_row(
        self,
        painter: QPainter,
        rect: QRectF,
        label: str,
        value: int,
    ) -> None:
        self._text(
            painter,
            QRectF(rect.x(), rect.y(), 136, rect.height()),
            label,
            8,
            INK,
            True,
        )

        track = QRectF(
            rect.x() + 142,
            rect.y() + rect.height() / 2 - 6,
            rect.width() - 194,
            12,
        )
        self.components.draw(painter, "bar_track", track)

        ratio = max(0.0, min(1.0, (value - 20) / 60))
        if ratio > 0:
            painter.save()
            painter.setClipRect(
                QRectF(
                    track.x(),
                    track.y(),
                    track.width() * ratio,
                    track.height(),
                )
            )
            self.components.draw(painter, "bar_fill", track)
            painter.restore()

        self._text(
            painter,
            QRectF(rect.right() - 38, rect.y(), 38, rect.height()),
            str(value),
            9,
            NAVY,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

    def _draw_batter_lower(self, painter: QPainter, player: Any) -> None:
        # Reference: fielding section is a wide horizontal band, roughly 22% of card height.
        field_panel = QRectF(30, 590, 690, 232)
        self.components.draw(painter, "panel_section", field_panel)

        self._text(
            painter,
            QRectF(52, 603, 290, 31),
            "FIELDING POSITIONS",
            10,
            NAVY,
            True,
        )

        active_positions: list[tuple[str, int]] = []
        for pos in ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"):
            value = player.number(f"def_{pos.lower()}")
            if value > 0:
                active_positions.append((pos, value))

        list_y = 642
        for index, (pos, value) in enumerate(active_positions[:4]):
            primary = pos == player.position
            chip_rect = QRectF(52, list_y + index * 40, 60, 31)
            self.components.draw(
                painter,
                "position_chip_primary" if primary else "position_chip",
                chip_rect,
            )
            self._text(
                painter,
                chip_rect,
                pos,
                8,
                WHITE if primary else NAVY,
                True,
                Qt.AlignCenter,
            )
            self._text(
                painter,
                QRectF(126, list_y + index * 40, 125, 31),
                "Primary" if primary else "Secondary",
                8,
                MUTED,
                True,
            )
            self._text(
                painter,
                QRectF(254, list_y + index * 40, 42, 31),
                str(value),
                9,
                NAVY,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
            )

        # Reference ratio: list ~40% width, field diagram ~50% width.
        self.components.draw(
            painter,
            "field_diamond",
            QRectF(353, 616, 330, 194),
        )

        positions = {
            "C": (518, 792),
            "1B": (627, 731),
            "2B": (590, 671),
            "3B": (409, 731),
            "SS": (446, 671),
            "LF": (383, 637),
            "CF": (518, 620),
            "RF": (653, 637),
        }

        for pos, (cx, cy) in positions.items():
            value = player.number(f"def_{pos.lower()}")
            if value <= 0:
                continue

            primary = pos == player.position
            chip_rect = QRectF(cx - 29, cy - 18, 58, 36)
            self.components.draw(
                painter,
                "position_chip_primary" if primary else "position_chip",
                chip_rect,
            )
            self._text(
                painter,
                chip_rect,
                f"{pos}\n{value}",
                7,
                WHITE if primary else NAVY,
                True,
                Qt.AlignCenter,
            )

        report_panel = QRectF(30, 830, 690, 174)
        self.components.draw(painter, "panel_section", report_panel)
        self._text(
            painter,
            QRectF(52, 843, 300, 31),
            "SCOUTING REPORT",
            10,
            NAVY,
            True,
        )
        self.components.draw(
            painter,
            "divider",
            QRectF(52, 878, 646, 4),
        )
        self._text(
            painter,
            QRectF(52, 889, 646, 91),
            player.get("scouting_report", "스카우팅 리포트가 없습니다."),
            9,
            INK,
            False,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
        )

    def _draw_pitcher_lower(self, painter: QPainter, player: Any) -> None:
        # Reference pitcher back: rating block -> thin velocity banner -> pitch mix -> report.
        velocity = QRectF(30, 542, 690, 68)
        self.components.draw(painter, "velocity_banner", velocity)
        self._text(
            painter,
            QRectF(52, 552, 280, 46),
            "FASTBALL VELOCITY",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(390, 548, 302, 50),
            f"{player.number('velocity_kmh')} km/h",
            20,
            WHITE,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

        pitch_panel = QRectF(30, 618, 690, 206)
        self.components.draw(painter, "panel_section", pitch_panel)
        self._text(
            painter,
            QRectF(52, 630, 270, 30),
            "PITCH MIX",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(548, 630, 144, 30),
            "20–80 GRADE",
            7,
            MUTED,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

        pitches = [
            ("4-SEAM", "pitch_four_seam"),
            ("SINKER", "pitch_sinker"),
            ("CUTTER", "pitch_cutter"),
            ("SLIDER", "pitch_slider"),
            ("SWEEPER", "pitch_sweeper"),
            ("SLURVE", "pitch_slurve"),
            ("CURVEBALL", "pitch_curveball"),
            ("KNUCKLE CURVE", "pitch_knuckle_curve"),
            ("SLOW CURVE", "pitch_slow_curve"),
            ("CHANGEUP", "pitch_changeup"),
            ("SPLITTER", "pitch_splitter"),
            ("FORKBALL", "pitch_forkball"),
            ("SCREWBALL", "pitch_screwball"),
            ("KNUCKLEBALL", "pitch_knuckleball"),
        ]

        active = [
            (label, player.number(key))
            for label, key in pitches
            if player.number(key) > 0
        ]

        for index, (label, value) in enumerate(active[:5]):
            y = 666 + index * 29
            self._text(
                painter,
                QRectF(52, y, 190, 26),
                label,
                8,
                INK,
                True,
            )

            track = QRectF(248, y + 7, 344, 12)
            self.components.draw(painter, "bar_track", track)
            ratio = max(0.0, min(1.0, (value - 20) / 60))
            if ratio > 0:
                painter.save()
                painter.setClipRect(
                    QRectF(
                        track.x(),
                        track.y(),
                        track.width() * ratio,
                        track.height(),
                    )
                )
                self.components.draw(painter, "bar_fill", track)
                painter.restore()

            self._text(
                painter,
                QRectF(610, y, 78, 26),
                str(value),
                9,
                NAVY,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
            )

        report_panel = QRectF(30, 832, 690, 172)
        self.components.draw(painter, "panel_section", report_panel)
        self._text(
            painter,
            QRectF(52, 844, 300, 29),
            "SCOUTING REPORT",
            10,
            NAVY,
            True,
        )
        self.components.draw(
            painter,
            "divider",
            QRectF(52, 877, 646, 4),
        )
        self._text(
            painter,
            QRectF(52, 888, 646, 91),
            player.get("scouting_report", "스카우팅 리포트가 없습니다."),
            8,
            INK,
            False,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
        )

