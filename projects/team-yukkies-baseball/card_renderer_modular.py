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
        # Header: logo -> name/team -> OVR, matching a conventional baseball card.
        header = QRectF(42, 38, 664, 126)
        self.components.draw(painter, "panel_header", header)

        logo_rect = QRectF(58, 52, 92, 92)
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
            QRectF(171, 48, 386, 48),
            player.name,
            23,
            INK,
            True,
        )
        self._text(
            painter,
            QRectF(171, 91, 386, 25),
            player.team_name.upper(),
            9,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(171, 117, 386, 24),
            player.get("series"),
            7,
            MUTED,
            False,
        )

        ovr_rect = QRectF(579, 43, 112, 112)
        self.components.draw(painter, "badge_ovr", ovr_rect)
        self._text(
            painter,
            QRectF(590, 53, 90, 26),
            "OVR",
            8,
            WHITE,
            True,
            Qt.AlignCenter,
        )
        self._text(
            painter,
            QRectF(587, 76, 96, 65),
            str(player.number("overall")),
            29,
            WHITE,
            True,
            Qt.AlignCenter,
        )

        # Player image is now the dominant visual area.
        photo_frame = QRectF(42, 168, 664, 652)
        photo_inner = QRectF(50, 176, 648, 636)

        clip = QPainterPath()
        clip.addRect(photo_inner)
        painter.save()
        painter.setClipPath(clip)

        if not self._draw_image(painter, player.player_image, photo_inner):
            painter.fillRect(photo_inner, PLACEHOLDER)
            self._text(
                painter,
                QRectF(80, 428, 588, 48),
                "PLAYER IMAGE",
                17,
                MUTED,
                True,
                Qt.AlignCenter,
            )
            self._text(
                painter,
                QRectF(80, 474, 588, 30),
                "우측 패널에서 이미지를 등록하세요",
                9,
                MUTED,
                False,
                Qt.AlignCenter,
            )

        painter.restore()
        self.components.draw(painter, "frame_image", photo_frame)

        # Position badge and uniform number sit over the photograph, like the reference.
        pos_rect = QRectF(49, 185, 116, 116)
        self.components.draw(painter, "badge_position", pos_rect)
        self._text(
            painter,
            QRectF(58, 204, 98, 58),
            player.position,
            26,
            WHITE,
            True,
            Qt.AlignCenter,
        )

        self._text(
            painter,
            QRectF(169, 204, 100, 56),
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
            QRectF(169, 250, 215, 29),
            profile,
            9,
            MUTED,
            True,
        )

        # Footer stat strip.
        stats = self._front_stats(player)
        start_x = 42
        gap = 6
        cell_w = (664 - gap * 5) / 6

        for index, (label, value) in enumerate(stats):
            x = start_x + index * (cell_w + gap)
            rect = QRectF(x, 838, cell_w, 112)
            self.components.draw(painter, "stat_cell", rect)
            self._text(
                painter,
                QRectF(x + 5, 848, cell_w - 10, 28),
                label,
                8,
                MUTED,
                True,
                Qt.AlignCenter,
            )

            suffix = " km/h" if label == "VEL" else ""
            self._text(
                painter,
                QRectF(x + 5, 878, cell_w - 10, 52),
                f"{value}{suffix}",
                10 if label == "VEL" else 18,
                NAVY,
                True,
                Qt.AlignCenter,
            )

        self.components.draw(
            painter,
            "divider",
            QRectF(74, 974, 602, 4),
        )
        self._text(
            painter,
            QRectF(74, 980, 602, 26),
            "TEAM YUKKIES",
            7,
            MUTED,
            True,
            Qt.AlignCenter,
        )

    def _draw_back(self, painter: QPainter, player: Any) -> None:
        # Conventional baseball-card header.
        header = QRectF(42, 38, 664, 138)
        self.components.draw(painter, "panel_header", header)

        logo_rect = QRectF(58, 54, 92, 92)
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
            QRectF(171, 51, 406, 44),
            player.name,
            22,
            INK,
            True,
        )
        self._text(
            painter,
            QRectF(171, 91, 406, 24),
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
            QRectF(171, 116, 430, 28),
            f"{player.position} / {bats}-{throws}{arm_slot}",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(606, 53, 72, 44),
            f"#{player.get('uniform_number', '-')}",
            19,
            MUTED,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

        # Ratings block: wide, dense, and chart-like.
        rating_panel = QRectF(42, 190, 664, 356)
        self.components.draw(painter, "panel_section", rating_panel)

        self._text(
            painter,
            QRectF(62, 205, 310, 30),
            "20–80 RATING BREAKDOWN",
            11,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(482, 205, 198, 30),
            "20   30   40   50   60   70   80",
            7,
            MUTED,
            False,
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

        start_y = 251
        row_h = 37 if len(rows) == 7 else 42
        for index, (label, key) in enumerate(rows):
            self._draw_rating_row(
                painter,
                QRectF(62, start_y + index * row_h, 620, row_h - 4),
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
            QRectF(rect.x(), rect.y(), 128, rect.height()),
            label,
            8,
            INK,
            True,
        )

        track = QRectF(
            rect.x() + 132,
            rect.y() + rect.height() / 2 - 6,
            rect.width() - 180,
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
        # Reference-like horizontal fielding section.
        field_panel = QRectF(42, 560, 664, 250)
        self.components.draw(painter, "panel_section", field_panel)

        self._text(
            painter,
            QRectF(62, 575, 280, 30),
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

        list_y = 619
        for index, (pos, value) in enumerate(active_positions[:4]):
            primary = pos == player.position
            chip_rect = QRectF(62, list_y + index * 43, 58, 32)
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
                QRectF(132, list_y + index * 43, 122, 32),
                "Primary" if primary else "Secondary",
                8,
                MUTED,
                True,
            )
            self._text(
                painter,
                QRectF(258, list_y + index * 43, 40, 32),
                str(value),
                9,
                NAVY,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
            )

        self.components.draw(
            painter,
            "field_diamond",
            QRectF(405, 602, 245, 190),
        )

        positions = {
            "C": (528, 771),
            "1B": (611, 710),
            "2B": (578, 651),
            "3B": (445, 710),
            "SS": (478, 651),
            "LF": (424, 618),
            "CF": (528, 598),
            "RF": (632, 618),
        }

        for pos, (cx, cy) in positions.items():
            value = player.number(f"def_{pos.lower()}")
            if value <= 0:
                continue

            primary = pos == player.position
            chip_rect = QRectF(cx - 29, cy - 19, 58, 38)
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

        # Full-width scouting report below, as in the reference card.
        report_panel = QRectF(42, 826, 664, 178)
        self.components.draw(painter, "panel_section", report_panel)

        self._text(
            painter,
            QRectF(62, 840, 280, 30),
            "SCOUTING REPORT",
            10,
            NAVY,
            True,
        )
        self.components.draw(
            painter,
            "divider",
            QRectF(62, 875, 620, 4),
        )
        self._text(
            painter,
            QRectF(62, 887, 620, 92),
            player.get("scouting_report", "스카우팅 리포트가 없습니다."),
            9,
            INK,
            False,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
        )

    def _draw_pitcher_lower(self, painter: QPainter, player: Any) -> None:
        velocity = QRectF(42, 560, 664, 70)
        self.components.draw(painter, "velocity_banner", velocity)

        self._text(
            painter,
            QRectF(62, 571, 270, 44),
            "FASTBALL VELOCITY",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(386, 566, 292, 50),
            f"{player.number('velocity_kmh')} km/h",
            20,
            WHITE,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

        pitch_panel = QRectF(42, 644, 664, 210)
        self.components.draw(painter, "panel_section", pitch_panel)

        self._text(
            painter,
            QRectF(62, 658, 260, 30),
            "PITCH MIX",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(540, 658, 142, 30),
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
            y = 697 + index * 29

            self._text(
                painter,
                QRectF(62, y, 190, 26),
                label,
                8,
                INK,
                True,
            )

            track = QRectF(264, y + 7, 320, 12)
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
                QRectF(600, y, 72, 26),
                str(value),
                9,
                NAVY,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
            )

        report_panel = QRectF(42, 870, 664, 134)
        self.components.draw(painter, "panel_section", report_panel)

        self._text(
            painter,
            QRectF(62, 882, 280, 28),
            "SCOUTING REPORT",
            10,
            NAVY,
            True,
        )
        self.components.draw(
            painter,
            "divider",
            QRectF(62, 912, 620, 4),
        )
        self._text(
            painter,
            QRectF(62, 920, 620, 62),
            player.get("scouting_report", "스카우팅 리포트가 없습니다."),
            8,
            INK,
            False,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
        )
