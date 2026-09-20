from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)
from PySide6.QtSvg import QSvgRenderer

from card_layout_v2 import (
    BACK_BATTER,
    BACK_COMMON,
    BACK_PITCHER,
    CARD_HEIGHT,
    CARD_WIDTH,
    FRONT,
    PALETTE,
    RATING,
    TYPOGRAPHY,
)

INK = QColor(PALETTE["ink"])
MUTED = QColor("#69798A")
NAVY = QColor(PALETTE["navy"])
ACCENT = QColor(PALETTE["blue"])
ACCENT_BRIGHT = QColor(PALETTE["blue_bright"])
SILVER = QColor(PALETTE["silver"])
WHITE = QColor(PALETTE["white"])
PAPER = QColor(PALETTE["paper"])
SOFT = QColor(PALETTE["paper_alt"])
GRID = QColor(PALETTE["track"])


def _rect(spec: tuple[int, int, int, int]) -> QRectF:
    return QRectF(*spec)


def _short_hand(value: str) -> str:
    return {"RIGHT": "R", "LEFT": "L", "SWITCH": "S"}.get(
        value.upper(), value[:1].upper() or "-"
    )


def _arm_slot(value: str) -> str:
    labels = {
        "OVERHAND": "Overhand",
        "THREE_QUARTER": "Three-Quarter",
        "SIDEARM": "Sidearm",
        "UNDERHAND": "Underhand",
    }
    return labels.get(value.upper(), value.replace("_", " ").title())


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
    """Reference-driven 9:16 Team Yukkies baseball-card renderer."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = Path(project_dir)
        self.components = SvgComponentLibrary(
            self.project_dir / "templates" / "baseball_v2"
        )

    def render(self, player: Any, side: str) -> QImage:
        image = QImage(
            CARD_WIDTH,
            CARD_HEIGHT,
            QImage.Format_ARGB32_Premultiplied,
        )
        image.fill(PAPER)

        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.TextAntialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        self.components.draw(
            painter,
            "common/card_shell",
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

    def _font(
        self,
        size: int,
        bold: bool = False,
        *,
        condensed: bool = False,
        italic: bool = False,
    ) -> QFont:
        # Card typography is canvas-locked. Use pixel sizes so preview and
        # exported PNG preserve the same proportions regardless of display DPI.
        font = QFont("Bahnschrift" if condensed else "Malgun Gothic")
        font.setPixelSize(int(round(size)))
        font.setWeight(QFont.Bold if bold else QFont.Normal)
        # Slightly relax the previous ultra-condensed setting. The reference
        # uses a narrow sports-card face, but not to the point of crowding.
        font.setStretch(82 if condensed else 100)
        font.setItalic(italic)
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
        *,
        condensed: bool = False,
        italic: bool = False,
    ) -> None:
        painter.setPen(color)
        painter.setFont(self._font(size, bold, condensed=condensed, italic=italic))
        painter.drawText(rect, align, text)

    def _fit_text(
        self,
        painter: QPainter,
        rect: QRectF,
        text: str,
        size: int,
        min_size: int,
        color: QColor = INK,
        bold: bool = True,
        align: Qt.AlignmentFlag = Qt.AlignLeft | Qt.AlignVCenter,
        *,
        condensed: bool = True,
    ) -> None:
        chosen = size
        while chosen > min_size:
            font = self._font(chosen, bold, condensed=condensed)
            if QFontMetricsF(font).horizontalAdvance(text) <= rect.width():
                break
            chosen -= 1
        self._text(
            painter,
            rect,
            text,
            chosen,
            color,
            bold,
            align,
            condensed=condensed,
        )

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

    def _bt(self, player: Any) -> str:
        return f"{_short_hand(player.get('bats'))}/{_short_hand(player.get('throws'))}"

    def _draw_outline_badge(
        self,
        painter: QPainter,
        rect: QRectF,
        text: str,
        *,
        fill: QColor = PAPER,
        text_color: QColor = NAVY,
        font_size: int = 18,
    ) -> None:
        painter.save()
        path = QPainterPath()
        cut = min(16.0, rect.height() * 0.22)
        path.moveTo(rect.left() + cut, rect.top())
        path.lineTo(rect.right() - cut, rect.top())
        path.lineTo(rect.right(), rect.top() + cut)
        path.lineTo(rect.right(), rect.bottom() - cut)
        path.lineTo(rect.right() - cut, rect.bottom())
        path.lineTo(rect.left() + cut, rect.bottom())
        path.lineTo(rect.left(), rect.bottom() - cut)
        path.lineTo(rect.left(), rect.top() + cut)
        path.closeSubpath()
        painter.fillPath(path, fill)
        painter.setPen(QPen(SILVER, 3))
        painter.drawPath(path)
        painter.restore()
        self._text(
            painter,
            rect,
            text,
            font_size,
            text_color,
            True,
            Qt.AlignCenter,
            condensed=True,
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
                QRectF(inner.x(), inner.center().y() - 34, inner.width(), 42),
                "PLAYER IMAGE",
                21,
                MUTED,
                True,
                Qt.AlignCenter,
                condensed=True,
            )
            self._text(
                painter,
                QRectF(inner.x(), inner.center().y() + 12, inner.width(), 32),
                "우측 패널에서 선수 이미지를 등록하세요",
                10,
                MUTED,
                False,
                Qt.AlignCenter,
            )

        painter.restore()
        self.components.draw(
            painter,
            "common/photo_frame",
            _rect(FRONT["photo_outer"]),
        )

    def _draw_front_header(self, painter: QPainter, player: Any) -> None:
        self.components.draw(
            painter,
            "common/front_header",
            _rect(FRONT["header"]),
        )

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
                TYPOGRAPHY["front_team"],
                MUTED,
                True,
                Qt.AlignCenter,
                condensed=True,
            )

        self._fit_text(
            painter,
            _rect(FRONT["name"]),
            player.name,
            TYPOGRAPHY["front_name"],
            TYPOGRAPHY["front_name_min"],
            INK,
            True,
        )
        self._text(
            painter,
            _rect(FRONT["team"]),
            player.team_name.upper(),
            TYPOGRAPHY["front_team"],
            NAVY,
            True,
            condensed=True,
        )
        self._text(
            painter,
            _rect(FRONT["ovr_label"]),
            "OVR",
            TYPOGRAPHY["ovr_label"],
            WHITE,
            True,
            Qt.AlignCenter,
            condensed=True,
        )
        self._text(
            painter,
            _rect(FRONT["ovr_value"]),
            str(player.number("overall")),
            TYPOGRAPHY["ovr_value"],
            WHITE,
            True,
            Qt.AlignCenter,
            condensed=True,
        )

    def _draw_front_identity(self, painter: QPainter, player: Any) -> None:
        self.components.draw(
            painter,
            "common/position_badge",
            _rect(FRONT["position_badge"]),
        )
        self._text(
            painter,
            _rect(FRONT["position_text"]),
            player.position,
            TYPOGRAPHY["position"],
            WHITE,
            True,
            Qt.AlignCenter,
            condensed=True,
        )
        self._draw_outline_badge(
            painter,
            _rect(FRONT["number"]),
            f"#{player.get('uniform_number', '-')}",
            font_size=TYPOGRAPHY["number"],
        )
        self._draw_outline_badge(
            painter,
            _rect(FRONT["handedness"]),
            self._bt(player),
            font_size=TYPOGRAPHY["handedness"],
        )

    def _draw_front_stats(
        self,
        painter: QPainter,
        stats: list[tuple[str, str, str | None]],
    ) -> None:
        panel = _rect(FRONT["stats"])
        self.components.draw(painter, "common/front_stats_rail", panel)

        cell_w = panel.width() / len(stats)
        painter.save()
        painter.setPen(QPen(NAVY, 2))
        for index in range(1, len(stats)):
            x = panel.x() + index * cell_w
            painter.drawLine(
                int(x),
                int(panel.y() + 38),
                int(x),
                int(panel.y() + 137),
            )
        painter.restore()

        for index, (label, value, unit) in enumerate(stats):
            x = panel.x() + index * cell_w
            self._text(
                painter,
                QRectF(x + 5, panel.y() + 30, cell_w - 10, 35),
                label,
                TYPOGRAPHY["stat_label"],
                INK,
                True,
                Qt.AlignCenter,
                condensed=True,
            )
            self._text(
                painter,
                QRectF(x + 5, panel.y() + 67, cell_w - 10, 66),
                value,
                TYPOGRAPHY["stat_value"] if unit is None else TYPOGRAPHY["stat_value_velocity"],
                INK,
                True,
                Qt.AlignCenter,
                condensed=True,
            )
            if unit:
                self._text(
                    painter,
                    QRectF(x + 5, panel.y() + 124, cell_w - 10, 25),
                    unit,
                    TYPOGRAPHY["stat_unit"],
                    INK,
                    True,
                    Qt.AlignCenter,
                    condensed=True,
                )

    def _draw_front_footer(self, painter: QPainter, player: Any) -> None:
        footer = _rect(FRONT["footer"])
        self.components.draw(
            painter,
            "common/divider",
            QRectF(footer.x() + 84, footer.y() + 6, footer.width() - 168, 4),
        )
        self._text(
            painter,
            QRectF(footer.x(), footer.y() + 8, footer.width(), footer.height() - 8),
            player.team_name.upper(),
            TYPOGRAPHY["footer"],
            NAVY,
            True,
            Qt.AlignCenter,
            condensed=True,
        )

    def _draw_batter_front(self, painter: QPainter, player: Any) -> None:
        self._draw_front_artwork(painter, player)
        self._draw_front_header(painter, player)
        self._draw_front_identity(painter, player)
        stats = [
            ("CON", str(player.number("contact")), None),
            ("POW", str(player.number("power")), None),
            ("GAP", str(player.number("gap")), None),
            ("EYE", str(player.number("eye")), None),
            ("SPD", str(self._speed(player)), None),
            ("FLD", str(self._primary_fielding(player)), None),
        ]
        self._draw_front_stats(painter, stats)
        self._draw_front_footer(painter, player)

    def _draw_pitcher_front(self, painter: QPainter, player: Any) -> None:
        self._draw_front_artwork(painter, player)
        self._draw_front_header(painter, player)
        self._draw_front_identity(painter, player)
        stats = [
            ("STF", str(player.number("stuff")), None),
            ("MOV", str(player.number("movement")), None),
            ("CTL", str(player.number("control")), None),
            ("CMD", str(player.number("command")), None),
            ("STA", str(player.number("stamina")), None),
            ("VEL", str(player.number("velocity_kmh")), "km/h"),
        ]
        self._draw_front_stats(painter, stats)
        self._draw_front_footer(painter, player)

    def _draw_back_header(self, painter: QPainter, player: Any) -> None:
        self.components.draw(
            painter,
            "common/back_header",
            _rect(BACK_COMMON["header"]),
        )

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
                13,
                MUTED,
                True,
                Qt.AlignCenter,
                condensed=True,
            )

        self._fit_text(
            painter,
            _rect(BACK_COMMON["name"]),
            player.name,
            TYPOGRAPHY["back_name"],
            TYPOGRAPHY["back_name_min"],
            INK,
            True,
        )
        self._text(
            painter,
            _rect(BACK_COMMON["team"]),
            player.team_name.upper(),
            TYPOGRAPHY["back_team"],
            NAVY,
            True,
            condensed=True,
        )

        profile = f"{player.position} / {self._bt(player)}"
        if player.is_pitcher and player.get("arm_slot"):
            profile += f" / {_arm_slot(player.get('arm_slot'))}"
        profile += f" / #{player.get('uniform_number', '-')}"
        self._fit_text(
            painter,
            _rect(BACK_COMMON["profile"]),
            profile,
            TYPOGRAPHY["back_profile"],
            TYPOGRAPHY["back_profile_min"],
            NAVY,
            True,
        )
        self._text(
            painter,
            _rect(BACK_COMMON["franchise"]),
            player.get("series"),
            TYPOGRAPHY["back_franchise"],
            INK,
            False,
            Qt.AlignLeft | Qt.AlignVCenter,
            condensed=True,
            italic=True,
        )
        self._text(
            painter,
            _rect(BACK_COMMON["number"]),
            f"#{player.get('uniform_number', '-')}",
            TYPOGRAPHY["back_number"],
            QColor("#AAB3BD"),
            True,
            Qt.AlignRight | Qt.AlignVCenter,
            condensed=True,
        )
        tagline = player.get("team_tagline", "PLAY\nBRIGHTER\nTOGETHER")
        self._text(
            painter,
            _rect(BACK_COMMON["tagline"]),
            tagline,
            TYPOGRAPHY["back_tagline"],
            MUTED,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
            condensed=True,
            italic=True,
        )

    def _draw_rating_panel(
        self,
        painter: QPainter,
        panel_spec: tuple[int, int, int, int],
        rows: list[tuple[str, int]],
    ) -> None:
        panel = _rect(panel_spec)
        self.components.draw(painter, "common/section_panel", panel)
        self._text(
            painter,
            QRectF(panel.x() + RATING["title_left"], panel.y() + 14, 470, 58),
            "20–80 Detailed Ratings",
            TYPOGRAPHY["section_title"],
            INK,
            True,
            condensed=True,
        )
        self._text(
            painter,
            QRectF(panel.right() - 320, panel.y() + 21, 286, 48),
            "SCALE: 20 (LOW) – 80 (ELITE)",
            TYPOGRAPHY["scale_note"],
            NAVY,
            False,
            Qt.AlignRight | Qt.AlignVCenter,
            condensed=True,
        )

        label_x = panel.x() + 34
        bar_x = panel.x() + RATING["bar_left"]
        value_w = RATING["value_width"]
        value_x = panel.right() - 35 - value_w
        bar_w = value_x - 22 - bar_x
        scale_y = panel.y() + RATING["scale_top"]
        row_top = panel.y() + RATING["rows_top"]
        row_h = (panel.height() - RATING["rows_top"] - 26) / len(rows)

        painter.save()
        painter.setPen(QPen(GRID, 1))
        for index, scale in enumerate((20, 30, 40, 50, 60, 70, 80)):
            x = bar_x + (bar_w * index / 6)
            painter.drawLine(
                int(x),
                int(row_top - 4),
                int(x),
                int(panel.bottom() - 20),
            )
            self._text(
                painter,
                QRectF(x - 24, scale_y, 48, 28),
                str(scale),
                TYPOGRAPHY["scale_tick"],
                INK,
                False,
                Qt.AlignCenter,
                condensed=True,
            )
        painter.restore()

        for index, (label, value) in enumerate(rows):
            y = row_top + index * row_h
            self._text(
                painter,
                QRectF(label_x, y, RATING["label_width"] - 36, row_h),
                label,
                TYPOGRAPHY["rating_label"],
                INK,
                True,
                condensed=True,
            )

            track = QRectF(bar_x, y + row_h / 2 - 10, bar_w, 20)
            self.components.draw(painter, "common/rating_track", track)
            ratio = max(0.0, min(1.0, (value - 20) / 60))
            if ratio > 0:
                painter.save()
                painter.setClipRect(
                    QRectF(track.x(), track.y(), track.width() * ratio, track.height())
                )
                self.components.draw(painter, "common/rating_fill", track)
                painter.restore()

            self._text(
                painter,
                QRectF(value_x, y, value_w, row_h),
                str(value),
                TYPOGRAPHY["rating_value"],
                INK,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
                condensed=True,
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

    def _draw_position_chip(
        self,
        painter: QPainter,
        rect: QRectF,
        pos: str,
        value: int | None,
        primary: bool,
    ) -> None:
        painter.save()
        painter.setBrush(ACCENT if primary else PAPER)
        painter.setPen(QPen(WHITE if primary else NAVY, 3))
        painter.drawRoundedRect(rect, 8, 8)
        painter.restore()
        text = pos if value is None else f"{pos}\n{value}"
        self._text(
            painter,
            rect,
            text,
            TYPOGRAPHY["position_chip"] if value is None else TYPOGRAPHY["position_chip_value"],
            WHITE if primary else NAVY,
            True,
            Qt.AlignCenter,
            condensed=True,
        )

    def _draw_fielding_panel(self, painter: QPainter, player: Any) -> None:
        panel = _rect(BACK_BATTER["fielding"])
        self.components.draw(painter, "common/section_panel", panel)
        self._text(
            painter,
            QRectF(panel.x() + 32, panel.y() + 12, 360, 52),
            "Fielding Positions",
            TYPOGRAPHY["section_title"],
            INK,
            True,
            condensed=True,
        )

        entries = self._active_fielding(player)
        list_x = panel.x() + 34
        list_y = panel.y() + 82
        visible_list = entries[:4]
        for index, (pos, value) in enumerate(visible_list):
            y = list_y + index * 55
            primary = pos == player.position
            chip = QRectF(list_x, y, 72, 44)
            self._draw_position_chip(painter, chip, pos, None, primary)
            self._text(
                painter,
                QRectF(list_x + 92, y, 124, 44),
                "Primary" if primary else "Secondary",
                TYPOGRAPHY["field_role"],
                INK,
                False,
                Qt.AlignLeft | Qt.AlignVCenter,
                condensed=True,
            )
            self._text(
                painter,
                QRectF(list_x + 214, y, 50, 44),
                str(value),
                TYPOGRAPHY["field_value"],
                INK,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
                condensed=True,
            )

        field = QRectF(panel.x() + 326, panel.y() + 64, 486, 248)
        self.components.draw(painter, "batter/field_diamond", field)
        marker_pos = {
            "C": (0.50, 0.88),
            "1B": (0.75, 0.66),
            "2B": (0.62, 0.45),
            "3B": (0.25, 0.66),
            "SS": (0.38, 0.45),
            "LF": (0.20, 0.23),
            "CF": (0.50, 0.14),
            "RF": (0.80, 0.23),
        }
        for pos, value in entries:
            px, py = marker_pos[pos]
            chip = QRectF(
                field.x() + field.width() * px - 34,
                field.y() + field.height() * py - 30,
                68,
                60,
            )
            self._draw_position_chip(
                painter,
                chip,
                pos,
                value,
                pos == player.position,
            )

    def _draw_scouting_panel(
        self,
        painter: QPainter,
        panel_spec: tuple[int, int, int, int],
        player: Any,
    ) -> None:
        panel = _rect(panel_spec)
        self.components.draw(painter, "common/section_panel", panel)
        self._text(
            painter,
            QRectF(panel.x() + 32, panel.y() + 12, 360, 52),
            "Scouting Report",
            TYPOGRAPHY["section_title"],
            INK,
            True,
            condensed=True,
        )
        painter.save()
        painter.setPen(QPen(GRID, 2))
        painter.drawLine(
            int(panel.x() + 32),
            int(panel.y() + 68),
            int(panel.right() - 32),
            int(panel.y() + 68),
        )
        painter.restore()
        self._text(
            painter,
            QRectF(
                panel.x() + 34,
                panel.y() + 82,
                panel.width() - 68,
                panel.height() - 120,
            ),
            player.get("scouting_report", "스카우팅 리포트가 없습니다."),
            TYPOGRAPHY["scouting_body"],
            INK,
            False,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
            condensed=False,
        )
        self._text(
            painter,
            QRectF(panel.x(), panel.bottom() - 38, panel.width(), 28),
            player.team_name.upper(),
            TYPOGRAPHY["footer"],
            NAVY,
            True,
            Qt.AlignCenter,
            condensed=True,
        )

    def _draw_batter_back(self, painter: QPainter, player: Any) -> None:
        self._draw_back_header(painter, player)
        rows = [
            ("Contact", player.number("contact")),
            ("Power", player.number("power")),
            ("Gap", player.number("gap")),
            ("Eye", player.number("eye")),
            ("Baserunning", player.number("baserunning")),
            ("Stealing", player.number("stealing")),
            ("Arm", player.number("arm")),
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
        return [
            (label, player.number(key))
            for label, key in pitches
            if player.number(key) > 0
        ]

    def _draw_velocity_banner(self, painter: QPainter, player: Any) -> None:
        panel = _rect(BACK_PITCHER["velocity"])
        self.components.draw(painter, "pitcher/velocity_banner", panel)
        self._text(
            painter,
            QRectF(panel.x() + 32, panel.y() + 7, 430, panel.height() - 14),
            "Fastball Velocity",
            TYPOGRAPHY["section_title"],
            INK,
            True,
            Qt.AlignLeft | Qt.AlignVCenter,
            condensed=True,
        )
        self._text(
            painter,
            QRectF(panel.x() + 515, panel.y() + 3, 180, panel.height() - 8),
            str(player.number("velocity_kmh")),
            TYPOGRAPHY["velocity_value"],
            WHITE,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
            condensed=True,
        )
        self._text(
            painter,
            QRectF(panel.x() + 704, panel.y() + 14, 108, panel.height() - 24),
            "km/h",
            TYPOGRAPHY["velocity_unit"],
            WHITE,
            True,
            Qt.AlignLeft | Qt.AlignVCenter,
            condensed=True,
        )

    def _draw_pitch_arsenal(self, painter: QPainter, player: Any) -> None:
        panel = _rect(BACK_PITCHER["pitch_arsenal"])
        self.components.draw(painter, "common/section_panel", panel)
        self._text(
            painter,
            QRectF(panel.x() + 32, panel.y() + 10, 360, 52),
            "Pitch Arsenal",
            TYPOGRAPHY["section_title"],
            INK,
            True,
            condensed=True,
        )
        self._text(
            painter,
            QRectF(panel.right() - 220, panel.y() + 14, 184, 42),
            "20–80 GRADE",
            TYPOGRAPHY["scale_note"],
            NAVY,
            False,
            Qt.AlignRight | Qt.AlignVCenter,
            condensed=True,
        )

        active = self._active_pitches(player)
        visible = active[:6]
        row_top = panel.y() + 68
        row_h = 32
        for index, (label, value) in enumerate(visible):
            y = row_top + index * row_h
            self._fit_text(
                painter,
                QRectF(panel.x() + 32, y, 250, row_h),
                label,
                TYPOGRAPHY["pitch_label"],
                TYPOGRAPHY["pitch_label_min"],
                INK,
                True,
            )
            track = QRectF(panel.x() + 292, y + 8, 404, 18)
            self.components.draw(painter, "common/rating_track", track)
            ratio = max(0.0, min(1.0, (value - 20) / 60))
            if ratio > 0:
                painter.save()
                painter.setClipRect(
                    QRectF(track.x(), track.y(), track.width() * ratio, track.height())
                )
                self.components.draw(painter, "common/rating_fill", track)
                painter.restore()
            self._text(
                painter,
                QRectF(panel.right() - 102, y, 66, row_h),
                str(value),
                TYPOGRAPHY["pitch_value"],
                INK,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
                condensed=True,
            )

        if len(active) > len(visible):
            self._text(
                painter,
                QRectF(panel.x() + 32, panel.bottom() - 28, panel.width() - 68, 20),
                f"+{len(active) - len(visible)} OTHER PITCHES",
                TYPOGRAPHY["small_note"],
                MUTED,
                False,
                Qt.AlignRight | Qt.AlignVCenter,
                condensed=True,
            )

    def _draw_pitcher_back(self, painter: QPainter, player: Any) -> None:
        self._draw_back_header(painter, player)
        rows = [
            ("Stuff", player.number("stuff")),
            ("Movement", player.number("movement")),
            ("Control", player.number("control")),
            ("Command", player.number("command")),
            ("Stamina", player.number("stamina")),
            ("Fielding", player.number("pitcher_fielding")),
        ]
        self._draw_rating_panel(painter, BACK_PITCHER["ratings"], rows)
        self._draw_velocity_banner(painter, player)
        self._draw_pitch_arsenal(painter, player)
        self._draw_scouting_panel(painter, BACK_PITCHER["scouting"], player)
