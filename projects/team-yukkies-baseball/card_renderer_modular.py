from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtSvg import QSvgRenderer

from card_layout import (
    BACK_BATTER,
    BACK_COMMON,
    BACK_PITCHER,
    CARD_HEIGHT,
    CARD_WIDTH,
    FRONT,
    RATING,
)

INK = QColor("#14233A")
MUTED = QColor("#7B8794")
NAVY = QColor("#153B61")
ACCENT = QColor("#2F7FF6")
WHITE = QColor("#FFFFFF")
SOFT = QColor("#F3F6F8")
GRID = QColor("#D8E0E7")


def _rect(spec: tuple[int, int, int, int]) -> QRectF:
    return QRectF(*spec)


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
    """Reference-driven baseball card renderer with four separate compositions."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.components = SvgComponentLibrary(
            self.project_dir / "templates" / "baseball"
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
            "base_frame",
            QRectF(0, 0, CARD_WIDTH, CARD_HEIGHT),
        )

        if side == "back":
            if player.is_pitcher:
                self._draw_pitcher_back(painter, player)
            else:
                self._draw_batter_back(painter, player)
        else:
            if player.is_pitcher:
                self._draw_pitcher_front(painter, player)
            else:
                self._draw_batter_front(painter, player)

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

    def _primary_fielding(self, player: Any) -> int:
        return player.number(f"def_{player.position.lower()}")

    def _speed(self, player: Any) -> int:
        return round(
            (player.number("baserunning") + player.number("stealing")) / 2
        )

    def _draw_front_artwork(self, painter: QPainter, player: Any) -> None:
        inner = _rect(FRONT["photo_inner"])
        clip = QPainterPath()
        clip.addRect(inner)
        painter.save()
        painter.setClipPath(clip)

        if not self._draw_image(painter, player.player_image, inner):
            painter.fillRect(inner, SOFT)
            self._text(
                painter,
                QRectF(inner.x(), inner.center().y() - 28, inner.width(), 34),
                "PLAYER IMAGE",
                17,
                MUTED,
                True,
                Qt.AlignCenter,
            )
            self._text(
                painter,
                QRectF(inner.x(), inner.center().y() + 8, inner.width(), 26),
                "우측 패널에서 이미지를 등록하세요",
                8,
                MUTED,
                False,
                Qt.AlignCenter,
            )

        painter.restore()
        self.components.draw(
            painter,
            "front_photo_frame",
            _rect(FRONT["photo_outer"]),
        )

    def _draw_front_header(
        self,
        painter: QPainter,
        player: Any,
        *,
        pitcher: bool,
    ) -> None:
        self.components.draw(painter, "front_header", _rect(FRONT["header"]))

        logo_rect = _rect(FRONT["logo"])
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
                10,
                MUTED,
                True,
                Qt.AlignCenter,
            )

        self._text(painter, _rect(FRONT["name"]), player.name, 23, INK, True)
        self._text(
            painter,
            _rect(FRONT["team"]),
            player.team_name.upper(),
            9,
            NAVY,
            True,
        )

        if pitcher:
            self._text(
                painter,
                _rect(FRONT["number_pitcher"]),
                f"#{player.get('uniform_number', '-')}",
                12,
                NAVY,
                True,
            )

        self._text(
            painter,
            _rect(FRONT["ovr_label"]),
            "OVR",
            8,
            WHITE,
            True,
            Qt.AlignCenter,
        )
        self._text(
            painter,
            _rect(FRONT["ovr_value"]),
            str(player.number("overall")),
            31,
            WHITE,
            True,
            Qt.AlignCenter,
        )

    def _draw_front_position(
        self,
        painter: QPainter,
        player: Any,
        *,
        pitcher: bool,
    ) -> None:
        self.components.draw(
            painter,
            "position_badge",
            _rect(FRONT["position_badge"]),
        )
        self._text(
            painter,
            _rect(FRONT["position_text"]),
            player.position,
            25,
            WHITE,
            True,
            Qt.AlignCenter,
        )
        if not pitcher:
            self._text(
                painter,
                _rect(FRONT["number_batter"]),
                f"#{player.get('uniform_number', '-')}",
                18,
                NAVY,
                True,
            )

    def _draw_front_stats(
        self,
        painter: QPainter,
        stats: list[tuple[str, str]],
    ) -> None:
        panel_name = "front_stats_7" if len(stats) == 7 else "front_stats_6"
        panel = _rect(FRONT["stats"])
        self.components.draw(painter, panel_name, panel)

        cell_w = panel.width() / len(stats)
        for index, (label, value) in enumerate(stats):
            x = panel.x() + index * cell_w
            self._text(
                painter,
                QRectF(x + 4, panel.y() + 11, cell_w - 8, 28),
                label,
                8,
                MUTED,
                True,
                Qt.AlignCenter,
            )
            self._text(
                painter,
                QRectF(x + 4, panel.y() + 40, cell_w - 8, 53),
                value,
                18,
                NAVY,
                True,
                Qt.AlignCenter,
            )

    def _draw_front_footer(self, painter: QPainter, player: Any) -> None:
        footer = _rect(FRONT["footer"])
        self.components.draw(
            painter,
            "divider",
            QRectF(footer.x() + 35, footer.y() + 3, footer.width() - 70, 4),
        )
        self._text(
            painter,
            QRectF(
                footer.x(),
                footer.y() + 8,
                footer.width(),
                footer.height() - 8,
            ),
            player.team_name.upper(),
            7,
            MUTED,
            True,
            Qt.AlignCenter,
        )

    def _draw_batter_front(self, painter: QPainter, player: Any) -> None:
        self._draw_front_artwork(painter, player)
        self._draw_front_header(painter, player, pitcher=False)
        self._draw_front_position(painter, player, pitcher=False)

        stats = [
            ("CON", str(player.number("contact"))),
            ("POW", str(player.number("power"))),
            ("EYE", str(player.number("eye"))),
            ("SPD", str(self._speed(player))),
            ("BSR", str(player.number("baserunning"))),
            ("FLD", str(self._primary_fielding(player))),
            ("ARM", str(player.number("arm"))),
        ]
        self._draw_front_stats(painter, stats)
        self._draw_front_footer(painter, player)

    def _draw_pitcher_front(self, painter: QPainter, player: Any) -> None:
        self._draw_front_artwork(painter, player)
        self._draw_front_header(painter, player, pitcher=True)
        self._draw_front_position(painter, player, pitcher=True)

        stats = [
            ("STF", str(player.number("stuff"))),
            ("MOV", str(player.number("movement"))),
            ("CTL", str(player.number("control"))),
            ("CMD", str(player.number("command"))),
            ("STA", str(player.number("stamina"))),
            ("FLD", str(player.number("pitcher_fielding"))),
        ]
        self._draw_front_stats(painter, stats)
        self._draw_front_footer(painter, player)

    def _draw_back_header(self, painter: QPainter, player: Any) -> None:
        self.components.draw(painter, "back_header", _rect(BACK_COMMON["header"]))

        logo_rect = _rect(BACK_COMMON["logo"])
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
                10,
                MUTED,
                True,
                Qt.AlignCenter,
            )

        self._text(painter, _rect(BACK_COMMON["name"]), player.name, 22, INK, True)
        self._text(
            painter,
            _rect(BACK_COMMON["team"]),
            player.team_name.upper(),
            9,
            MUTED,
            True,
        )

        bats = _short_hand(player.get("bats"))
        throws = _short_hand(player.get("throws"))
        arm_slot = ""
        if player.is_pitcher and player.get("arm_slot"):
            arm_slot = f" / {player.get('arm_slot').replace('_', ' ').title()}"

        self._text(
            painter,
            _rect(BACK_COMMON["profile"]),
            f"{player.position} / {bats}-{throws}{arm_slot}",
            10,
            NAVY,
            True,
        )
        self._text(
            painter,
            _rect(BACK_COMMON["number"]),
            f"#{player.get('uniform_number', '-')}",
            20,
            MUTED,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

    def _draw_rating_panel(
        self,
        painter: QPainter,
        panel_spec: tuple[int, int, int, int],
        rows: list[tuple[str, int]],
    ) -> None:
        panel = _rect(panel_spec)
        self.components.draw(painter, "back_section", panel)
        self._text(
            painter,
            QRectF(
                panel.x() + RATING["title_x"],
                panel.y() + RATING["title_y"],
                RATING["title_w"],
                RATING["title_h"],
            ),
            "20–80 RATING BREAKDOWN",
            11,
            NAVY,
            True,
        )

        bar_x = panel.x() + RATING["bar_x"]
        bar_w = RATING["bar_w"]
        scale_y = panel.y() + 49
        for index, scale in enumerate((20, 30, 40, 50, 60, 70, 80)):
            x = bar_x + (bar_w * index / 6)
            self._text(
                painter,
                QRectF(x - 16, scale_y, 32, 18),
                str(scale),
                7,
                MUTED,
                False,
                Qt.AlignCenter,
            )

        row_top = panel.y() + 72
        row_h = (panel.height() - 86) / len(rows)

        painter.setPen(QPen(GRID, 1))
        for index in range(7):
            x = bar_x + (bar_w * index / 6)
            painter.drawLine(
                int(x),
                int(row_top - 2),
                int(x),
                int(panel.bottom() - 12),
            )

        for index, (label, value) in enumerate(rows):
            y = row_top + index * row_h
            self._text(
                painter,
                QRectF(
                    panel.x() + RATING["label_x"],
                    y,
                    RATING["bar_x"] - RATING["label_x"] - 12,
                    row_h,
                ),
                label,
                8,
                INK,
                True,
            )

            track = QRectF(bar_x, y + row_h / 2 - 7, bar_w, 14)
            self.components.draw(painter, "rating_track", track)
            ratio = max(0.0, min(1.0, (value - 20) / 60))
            if ratio > 0:
                painter.save()
                painter.setClipRect(
                    QRectF(track.x(), track.y(), track.width() * ratio, track.height())
                )
                self.components.draw(painter, "rating_fill", track)
                painter.restore()

            self._text(
                painter,
                QRectF(
                    panel.x() + RATING["value_x"],
                    y,
                    RATING["value_w"],
                    row_h,
                ),
                str(value),
                9,
                NAVY,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
            )

    def _active_fielding(self, player: Any) -> list[tuple[str, int]]:
        entries: list[tuple[str, int]] = []
        for pos in ("C", "1B", "2B", "3B", "SS", "LF", "CF", "RF"):
            value = player.number(f"def_{pos.lower()}")
            if value > 0:
                entries.append((pos, value))

        entries.sort(
            key=lambda item: (
                0 if item[0] == player.position else 1,
                -item[1],
                item[0],
            )
        )
        return entries

    def _draw_fielding_panel(self, painter: QPainter, player: Any) -> None:
        panel = _rect(BACK_BATTER["fielding"])
        self.components.draw(painter, "back_section", panel)
        self._text(
            painter,
            QRectF(panel.x() + 22, panel.y() + 12, 300, 32),
            "FIELDING POSITIONS",
            11,
            NAVY,
            True,
        )

        entries = self._active_fielding(player)
        list_x = panel.x() + 22
        list_y = panel.y() + 60
        for index, (pos, value) in enumerate(entries[:4]):
            y = list_y + index * 39
            primary = pos == player.position
            chip = QRectF(list_x, y, 58, 32)
            self.components.draw(
                painter,
                "position_chip_primary" if primary else "position_chip",
                chip,
            )
            self._text(
                painter,
                chip,
                pos,
                8,
                WHITE if primary else NAVY,
                True,
                Qt.AlignCenter,
            )
            self._text(
                painter,
                QRectF(list_x + 72, y, 112, 32),
                "Primary" if primary else "Secondary",
                8,
                MUTED,
                True,
            )
            self._text(
                painter,
                QRectF(list_x + 186, y, 38, 32),
                str(value),
                9,
                NAVY,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
            )

        field = QRectF(panel.x() + 300, panel.y() + 53, 330, 194)
        self.components.draw(painter, "field_diamond", field)

        marker_pos = {
            "C": (0.50, 0.87),
            "1B": (0.74, 0.65),
            "2B": (0.62, 0.46),
            "3B": (0.26, 0.65),
            "SS": (0.38, 0.46),
            "LF": (0.20, 0.25),
            "CF": (0.50, 0.15),
            "RF": (0.80, 0.25),
        }

        for pos, value in entries:
            px, py = marker_pos[pos]
            chip = QRectF(
                field.x() + field.width() * px - 25,
                field.y() + field.height() * py - 17,
                50,
                34,
            )
            primary = pos == player.position
            self.components.draw(
                painter,
                "position_chip_primary" if primary else "position_chip",
                chip,
            )
            self._text(
                painter,
                chip,
                f"{pos}\n{value}",
                7,
                WHITE if primary else NAVY,
                True,
                Qt.AlignCenter,
            )

    def _draw_scouting_panel(
        self,
        painter: QPainter,
        panel_spec: tuple[int, int, int, int],
        player: Any,
    ) -> None:
        panel = _rect(panel_spec)
        self.components.draw(painter, "back_section", panel)
        self._text(
            painter,
            QRectF(panel.x() + 22, panel.y() + 12, 300, 32),
            "SCOUTING REPORT",
            11,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(
                panel.x() + 22,
                panel.y() + 58,
                panel.width() - 44,
                panel.height() - 76,
            ),
            player.get("scouting_report", "스카우팅 리포트가 없습니다."),
            9,
            INK,
            False,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
        )

    def _draw_batter_back(self, painter: QPainter, player: Any) -> None:
        self._draw_back_header(painter, player)
        rows = [
            ("CONTACT", player.number("contact")),
            ("POWER", player.number("power")),
            ("EYE", player.number("eye")),
            ("SPEED", self._speed(player)),
            ("BASERUNNING", player.number("baserunning")),
            ("FIELDING", self._primary_fielding(player)),
            ("ARM", player.number("arm")),
        ]
        self._draw_rating_panel(painter, BACK_BATTER["ratings"], rows)
        self._draw_fielding_panel(painter, player)
        self._draw_scouting_panel(painter, BACK_BATTER["scouting"], player)

    def _active_pitches(self, player: Any) -> list[tuple[str, int]]:
        pitches = [
            ("Four-Seam Fastball", "pitch_four_seam"),
            ("Sinker", "pitch_sinker"),
            ("Cutter", "pitch_cutter"),
            ("Slider", "pitch_slider"),
            ("Sweeper", "pitch_sweeper"),
            ("Slurve", "pitch_slurve"),
            ("Curveball", "pitch_curveball"),
            ("Knuckle Curve", "pitch_knuckle_curve"),
            ("Slow Curve", "pitch_slow_curve"),
            ("Changeup", "pitch_changeup"),
            ("Splitter", "pitch_splitter"),
            ("Forkball", "pitch_forkball"),
            ("Screwball", "pitch_screwball"),
            ("Knuckleball", "pitch_knuckleball"),
        ]
        active = [
            (label, player.number(key))
            for label, key in pitches
            if player.number(key) > 0
        ]
        active.sort(key=lambda item: (-item[1], item[0]))
        return active

    def _draw_velocity_banner(self, painter: QPainter, player: Any) -> None:
        panel = _rect(BACK_PITCHER["velocity"])
        self.components.draw(painter, "velocity_banner", panel)
        self._text(
            painter,
            QRectF(panel.x() + 22, panel.y() + 8, 280, panel.height() - 16),
            "FASTBALL VELOCITY",
            11,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(panel.x() + 370, panel.y() + 5, 260, panel.height() - 10),
            f"{player.number('velocity_kmh')} km/h",
            20,
            WHITE,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

    def _draw_pitch_mix(self, painter: QPainter, player: Any) -> None:
        panel = _rect(BACK_PITCHER["pitch_mix"])
        self.components.draw(painter, "back_section", panel)
        self._text(
            painter,
            QRectF(panel.x() + 22, panel.y() + 12, 270, 32),
            "PITCH MIX",
            11,
            NAVY,
            True,
        )
        self._text(
            painter,
            QRectF(panel.right() - 150, panel.y() + 12, 128, 32),
            "20–80 GRADE",
            7,
            MUTED,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

        active = self._active_pitches(player)
        visible = active[:6]
        row_top = panel.y() + 54
        row_h = 25
        for index, (label, value) in enumerate(visible):
            y = row_top + index * row_h
            self._text(
                painter,
                QRectF(panel.x() + 22, y, 180, row_h),
                label,
                8,
                INK,
                True,
            )
            track = QRectF(panel.x() + 210, y + 6, 345, 13)
            self.components.draw(painter, "rating_track", track)

            ratio = max(0.0, min(1.0, (value - 20) / 60))
            if ratio > 0:
                painter.save()
                painter.setClipRect(
                    QRectF(track.x(), track.y(), track.width() * ratio, track.height())
                )
                self.components.draw(painter, "rating_fill", track)
                painter.restore()

            self._text(
                painter,
                QRectF(panel.right() - 70, y, 48, row_h),
                str(value),
                9,
                NAVY,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
            )

        if len(active) > len(visible):
            self._text(
                painter,
                QRectF(panel.x() + 22, panel.bottom() - 28, panel.width() - 44, 18),
                f"+{len(active) - len(visible)} OTHER PITCHES",
                7,
                MUTED,
                False,
                Qt.AlignRight | Qt.AlignVCenter,
            )

    def _draw_pitcher_back(self, painter: QPainter, player: Any) -> None:
        self._draw_back_header(painter, player)
        rows = [
            ("STUFF", player.number("stuff")),
            ("MOVEMENT", player.number("movement")),
            ("CONTROL", player.number("control")),
            ("COMMAND", player.number("command")),
            ("STAMINA", player.number("stamina")),
            ("FIELDING", player.number("pitcher_fielding")),
        ]
        self._draw_rating_panel(painter, BACK_PITCHER["ratings"], rows)
        self._draw_velocity_banner(painter, player)
        self._draw_pitch_mix(painter, player)
        self._draw_scouting_panel(painter, BACK_PITCHER["scouting"], player)
