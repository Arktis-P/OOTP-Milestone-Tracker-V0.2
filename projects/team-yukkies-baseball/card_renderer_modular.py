from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPixmap
from PySide6.QtSvg import QSvgRenderer


CARD_WIDTH = 750
CARD_HEIGHT = 1050

INK = QColor("#16253A")
MUTED = QColor("#7B8794")
ACCENT = QColor("#2F7FF6")
NAVY = QColor("#163A5C")
WHITE = QColor("#FFFFFF")
PLACEHOLDER = QColor("#EEF2F5")


def _short_hand(value: str) -> str:
    return {"RIGHT": "R", "LEFT": "L", "SWITCH": "S"}.get(
        value.upper(), value[:1].upper() or "-"
    )


class SvgComponentLibrary:
    """Load reusable SVG card parts from templates/components."""

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
    """Render cards from SVG components plus dynamic CSV/player assets."""

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
        pos_rect = QRectF(42, 44, 112, 118)
        self.components.draw(painter, "badge_position", pos_rect)
        self._text(
            painter,
            QRectF(53, 53, 90, 61),
            player.get("uniform_number", "-"),
            29,
            NAVY,
            True,
            Qt.AlignCenter,
        )
        self._text(
            painter,
            QRectF(53, 112, 90, 35),
            player.position,
            12,
            NAVY,
            True,
            Qt.AlignCenter,
        )

        logo_rect = QRectF(588, 44, 118, 118)
        self.components.draw(painter, "logo_slot", logo_rect)
        if not self._draw_image(
            painter,
            player.team_logo,
            logo_rect.adjusted(15, 15, -15, -15),
            contain=True,
        ):
            self._text(
                painter,
                logo_rect,
                "TEAM",
                9,
                MUTED,
                True,
                Qt.AlignCenter,
            )

        photo_frame = QRectF(42, 176, 664, 566)
        photo_inner = QRectF(50, 184, 648, 550)
        clip = QPainterPath()
        clip.addRect(photo_inner)
        painter.save()
        painter.setClipPath(clip)
        if not self._draw_image(painter, player.player_image, photo_inner):
            painter.fillRect(photo_inner, PLACEHOLDER)
            self._text(
                painter,
                QRectF(80, 398, 588, 46),
                "PLAYER IMAGE",
                17,
                MUTED,
                True,
                Qt.AlignCenter,
            )
            self._text(
                painter,
                QRectF(80, 444, 588, 30),
                "우측 패널에서 이미지를 등록하세요",
                9,
                MUTED,
                False,
                Qt.AlignCenter,
            )
        painter.restore()
        self.components.draw(painter, "frame_image", photo_frame)

        ovr_rect = QRectF(581, 618, 124, 124)
        self.components.draw(painter, "badge_ovr", ovr_rect)
        self._text(
            painter,
            QRectF(596, 631, 94, 28),
            "OVR",
            9,
            WHITE,
            True,
            Qt.AlignCenter,
        )
        self._text(
            painter,
            QRectF(590, 657, 106, 65),
            str(player.number("overall")),
            29,
            WHITE,
            True,
            Qt.AlignCenter,
        )

        self._text(
            painter,
            QRectF(46, 758, 520, 52),
            player.name,
            23,
            INK,
            True,
        )
        self._text(
            painter,
            QRectF(46, 807, 520, 26),
            player.team_name,
            9,
            MUTED,
            True,
        )
        self.components.draw(
            painter,
            "divider",
            QRectF(46, 842, 360, 4),
        )

        stats = self._front_stats(player)
        start_x = 42
        gap = 8
        cell_w = (664 - gap * 5) / 6
        for index, (label, value) in enumerate(stats):
            x = start_x + index * (cell_w + gap)
            rect = QRectF(x, 870, cell_w, 106)
            self.components.draw(painter, "stat_cell", rect)
            self._text(
                painter,
                QRectF(x + 4, 879, cell_w - 8, 30),
                label,
                8,
                MUTED,
                True,
                Qt.AlignCenter,
            )
            suffix = " km/h" if label == "VEL" else ""
            self._text(
                painter,
                QRectF(x + 4, 911, cell_w - 8, 48),
                f"{value}{suffix}",
                11 if label == "VEL" else 18,
                NAVY,
                True,
                Qt.AlignCenter,
            )

        bats = _short_hand(player.get("bats"))
        throws = _short_hand(player.get("throws"))
        self._text(
            painter,
            QRectF(46, 992, 658, 22),
            f"{player.get('series')}   ·   B/T {bats}/{throws}",
            8,
            MUTED,
            False,
            Qt.AlignRight | Qt.AlignVCenter,
        )

    def _draw_back(self, painter: QPainter, player: Any) -> None:
        header = QRectF(42, 42, 664, 128)
        self.components.draw(painter, "panel_header", header)

        if not self._draw_image(
            painter,
            player.team_logo,
            QRectF(57, 60, 76, 76),
            contain=True,
        ):
            self._text(
                painter,
                QRectF(56, 58, 80, 80),
                "TEAM",
                8,
                MUTED,
                True,
                Qt.AlignCenter,
            )

        name_x = 150
        self._text(
            painter,
            QRectF(name_x, 56, 400, 38),
            player.name,
            20,
            INK,
            True,
        )
        self._text(
            painter,
            QRectF(name_x, 91, 400, 24),
            player.team_name,
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
            QRectF(name_x, 117, 470, 30),
            f"{player.position} / {bats}-{throws}{arm_slot}",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(612, 56, 70, 58),
            f"#{player.get('uniform_number', '-')}",
            20,
            MUTED,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

        rating_panel = QRectF(42, 188, 664, 334)
        self.components.draw(painter, "panel_section", rating_panel)
        self._text(
            painter,
            QRectF(62, 204, 300, 30),
            "20–80 RATING BREAKDOWN",
            11,
            NAVY,
            True,
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
        start_y = 248
        row_h = 35 if len(rows) == 7 else 40
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
            QRectF(rect.x(), rect.y(), 132, rect.height()),
            label,
            8,
            INK,
            True,
        )
        track = QRectF(
            rect.x() + 140,
            rect.y() + rect.height() / 2 - 7,
            rect.width() - 190,
            14,
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
            QRectF(rect.right() - 42, rect.y(), 42, rect.height()),
            str(value),
            9,
            NAVY,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

    def _draw_batter_lower(self, painter: QPainter, player: Any) -> None:
        field_panel = QRectF(42, 540, 320, 434)
        report_panel = QRectF(376, 540, 330, 434)
        self.components.draw(painter, "panel_section", field_panel)
        self.components.draw(painter, "panel_section", report_panel)

        self._text(
            painter,
            QRectF(62, 556, 260, 30),
            "FIELDING POSITIONS",
            10,
            NAVY,
            True,
        )
        self.components.draw(
            painter,
            "field_diamond",
            QRectF(82, 610, 240, 190),
        )

        positions = {
            "C": (202, 774),
            "1B": (280, 716),
            "2B": (250, 654),
            "3B": (124, 716),
            "SS": (154, 654),
            "LF": (88, 610),
            "CF": (202, 590),
            "RF": (316, 610),
        }
        for pos, (cx, cy) in positions.items():
            value = player.number(f"def_{pos.lower()}")
            if value <= 0:
                continue
            primary = pos == player.position
            chip = QRectF(cx - 28, cy - 18, 56, 36)
            self.components.draw(
                painter,
                "position_chip_primary" if primary else "position_chip",
                chip,
            )
            self._text(
                painter,
                chip,
                f"{pos} {value}",
                7,
                WHITE if primary else NAVY,
                True,
                Qt.AlignCenter,
            )

        self._text(
            painter,
            QRectF(62, 826, 280, 28),
            f"PRIMARY  {player.position}",
            8,
            MUTED,
            True,
        )

        self._text(
            painter,
            QRectF(396, 556, 270, 30),
            "SCOUTING REPORT",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(396, 598, 270, 338),
            player.get("scouting_report", "스카우팅 리포트가 없습니다."),
            9,
            INK,
            False,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
        )

    def _draw_pitcher_lower(self, painter: QPainter, player: Any) -> None:
        velocity = QRectF(42, 540, 664, 74)
        self.components.draw(painter, "velocity_banner", velocity)
        self._text(
            painter,
            QRectF(62, 553, 260, 46),
            "FASTBALL VELOCITY",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(390, 548, 286, 52),
            f"{player.number('velocity_kmh')} km/h",
            20,
            WHITE,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

        pitch_panel = QRectF(42, 630, 664, 198)
        self.components.draw(painter, "panel_section", pitch_panel)
        self._text(
            painter,
            QRectF(62, 646, 250, 28),
            "PITCH MIX",
            10,
            NAVY,
            True,
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
        for index, (label, value) in enumerate(active[:8]):
            col = index % 2
            row = index // 2
            x = 62 + col * 310
            y = 681 + row * 34
            self._text(
                painter,
                QRectF(x, y, 170, 28),
                label,
                8,
                INK,
                True,
            )
            track = QRectF(x + 172, y + 8, 86, 12)
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
                QRectF(x + 263, y, 31, 28),
                str(value),
                8,
                NAVY,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
            )

        report_panel = QRectF(42, 844, 664, 130)
        self.components.draw(painter, "panel_section", report_panel)
        self._text(
            painter,
            QRectF(62, 856, 250, 26),
            "SCOUTING REPORT",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(62, 884, 620, 72),
            player.get("scouting_report", "스카우팅 리포트가 없습니다."),
            8,
            INK,
            False,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
        )
