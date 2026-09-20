from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

CARD_WIDTH = 750
CARD_HEIGHT = 1050
PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_CSV = PROJECT_DIR / "PLAYER_RATINGS.csv"
PLAYER_ASSETS = PROJECT_DIR / "assets" / "players"
TEAM_ASSETS = PROJECT_DIR / "assets" / "teams"
OUTPUT_DIR = PROJECT_DIR / "output"

INK = QColor("#18222D")
MUTED = QColor("#6F7B87")
LINE = QColor("#DDE2E7")
PAPER = QColor("#FBFBFA")
PANEL = QColor("#F2F4F5")
ACCENT = QColor("#294A67")
SOFT_ACCENT = QColor("#E8EEF3")
WHITE = QColor("#FFFFFF")


@dataclass(frozen=True)
class PlayerRecord:
    values: dict[str, str]

    def get(self, key: str, default: str = "") -> str:
        return (self.values.get(key) or default).strip()

    def number(self, key: str, default: int = 0) -> int:
        value = self.get(key)
        if not value:
            return default
        try:
            return int(round(float(value)))
        except ValueError:
            return default

    @property
    def player_id(self) -> str:
        return self.get("player_id")

    @property
    def name(self) -> str:
        return self.get("character_name", self.player_id)

    @property
    def team_id(self) -> str:
        return self.get("team_id", "team")

    @property
    def team_name(self) -> str:
        return self.get("team_name", self.team_id)

    @property
    def is_pitcher(self) -> bool:
        return self.get("player_type").upper() == "PITCHER"

    @property
    def position(self) -> str:
        return self.get("primary_position", "-")

    @property
    def player_image(self) -> Path:
        return PLAYER_ASSETS / f"{self.player_id}.png"

    @property
    def team_logo(self) -> Path:
        return TEAM_ASSETS / f"{self.team_id}.png"


def load_players(path: Path) -> list[PlayerRecord]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        rows = [PlayerRecord(dict(row)) for row in csv.DictReader(stream)]
    return [row for row in rows if row.player_id]


def short_hand(value: str) -> str:
    return {"RIGHT": "R", "LEFT": "L", "SWITCH": "S"}.get(value.upper(), value[:1].upper() or "-")


def grade_color(value: int) -> QColor:
    if value >= 70:
        return QColor("#244F43")
    if value >= 60:
        return QColor("#365E78")
    if value >= 50:
        return QColor("#5E6B76")
    if value >= 40:
        return QColor("#8A7048")
    return QColor("#865552")


class CardRenderer:
    def render(self, player: PlayerRecord, side: str) -> QImage:
        image = QImage(CARD_WIDTH, CARD_HEIGHT, QImage.Format_ARGB32_Premultiplied)
        image.fill(PAPER)
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
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

    def _rounded_rect(
        self,
        painter: QPainter,
        rect: QRectF,
        fill: QColor,
        radius: float = 12,
        border: QColor | None = None,
    ) -> None:
        painter.setBrush(fill)
        painter.setPen(QPen(border, 1) if border else Qt.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

    def _draw_image(self, painter: QPainter, path: Path, rect: QRectF, contain: bool = False) -> bool:
        if not path.exists():
            return False
        pixmap = QPixmap(str(path))
        if pixmap.isNull():
            return False
        mode = Qt.KeepAspectRatio if contain else Qt.KeepAspectRatioByExpanding
        scaled = pixmap.scaled(int(rect.width()), int(rect.height()), mode, Qt.SmoothTransformation)
        source_x = max(0, (scaled.width() - int(rect.width())) // 2)
        source_y = max(0, (scaled.height() - int(rect.height())) // 2)
        target = QRectF(rect)
        if contain:
            target = QRectF(0, 0, scaled.width(), scaled.height())
            target.moveCenter(rect.center())
            painter.drawPixmap(target, scaled, QRectF(scaled.rect()))
        else:
            painter.drawPixmap(
                target,
                scaled,
                QRectF(source_x, source_y, rect.width(), rect.height()),
            )
        return True

    def _draw_header_rule(self, painter: QPainter, label: str) -> None:
        self._text(painter, QRectF(48, 28, 430, 30), label.upper(), 9, MUTED, True)
        painter.setPen(QPen(ACCENT, 3))
        painter.drawLine(48, 67, 702, 67)

    def _draw_front(self, painter: QPainter, player: PlayerRecord) -> None:
        self._draw_header_rule(painter, player.team_name)
        self._text(painter, QRectF(48, 78, 210, 34), player.get("card_type", "BASE"), 10, ACCENT, True)
        self._text(
            painter,
            QRectF(518, 78, 184, 34),
            f"#{player.get('uniform_number', '-')}  {player.position}",
            13,
            INK,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )

        photo_rect = QRectF(48, 124, 654, 612)
        self._rounded_rect(painter, photo_rect, PANEL, 18, LINE)
        path = QPainterPath()
        path.addRoundedRect(photo_rect, 18, 18)
        painter.save()
        painter.setClipPath(path)
        if not self._draw_image(painter, player.player_image, photo_rect):
            painter.fillRect(photo_rect, QColor("#EEF1F3"))
            self._text(
                painter,
                QRectF(88, 366, 574, 48),
                "PLAYER IMAGE",
                18,
                QColor("#A0A8AF"),
                True,
                Qt.AlignCenter,
            )
            self._text(
                painter,
                QRectF(88, 414, 574, 34),
                "우측 패널에서 이미지를 등록하세요",
                10,
                MUTED,
                False,
                Qt.AlignCenter,
            )
        painter.restore()

        logo_rect = QRectF(568, 146, 105, 105)
        self._rounded_rect(painter, logo_rect, QColor(255, 255, 255, 226), 15)
        if not self._draw_image(
            painter,
            player.team_logo,
            logo_rect.adjusted(12, 12, -12, -12),
            contain=True,
        ):
            self._text(painter, logo_rect, "LOGO", 9, MUTED, True, Qt.AlignCenter)

        ovr_rect = QRectF(69, 150, 105, 112)
        self._rounded_rect(painter, ovr_rect, QColor(255, 255, 255, 232), 15)
        self._text(painter, QRectF(79, 157, 85, 28), "OVR", 9, MUTED, True, Qt.AlignCenter)
        self._text(
            painter,
            QRectF(73, 184, 97, 65),
            str(player.number("overall")),
            31,
            ACCENT,
            True,
            Qt.AlignCenter,
        )

        self._text(painter, QRectF(48, 754, 654, 54), player.name, 25, INK, True)
        subtitle = f"{player.get('series')}  ·  {player.team_name}"
        self._text(painter, QRectF(48, 807, 654, 31), subtitle, 10, MUTED)

        stats = self._front_stats(player)
        box_y = 860
        gap = 8
        box_w = (654 - gap * 5) / 6
        for index, (label, value) in enumerate(stats):
            x = 48 + index * (box_w + gap)
            rect = QRectF(x, box_y, box_w, 112)
            self._rounded_rect(painter, rect, WHITE, 12, LINE)
            self._text(
                painter,
                QRectF(x + 4, box_y + 13, box_w - 8, 26),
                label,
                9,
                MUTED,
                True,
                Qt.AlignCenter,
            )
            numeric = value.replace(" km/h", "")
            color = ACCENT
            try:
                color = grade_color(int(numeric)) if "km/h" not in value else ACCENT
            except ValueError:
                pass
            self._text(
                painter,
                QRectF(x + 4, box_y + 43, box_w - 8, 50),
                value,
                17 if "km/h" not in value else 11,
                color,
                True,
                Qt.AlignCenter,
            )

        bats = short_hand(player.get("bats"))
        throws = short_hand(player.get("throws"))
        self._text(
            painter,
            QRectF(48, 992, 654, 24),
            f"B/T  {bats}/{throws}",
            9,
            MUTED,
            True,
            Qt.AlignRight,
        )

    def _front_stats(self, player: PlayerRecord) -> list[tuple[str, str]]:
        if player.is_pitcher:
            return [
                ("STF", str(player.number("stuff"))),
                ("MOV", str(player.number("movement"))),
                ("CTL", str(player.number("control"))),
                ("CMD", str(player.number("command"))),
                ("STA", str(player.number("stamina"))),
                ("VEL", f"{player.number('velocity_kmh')} km/h"),
            ]
        fld_key = f"def_{player.position.lower()}"
        speed = round((player.number("baserunning") + player.number("stealing")) / 2)
        return [
            ("CON", str(player.number("contact"))),
            ("POW", str(player.number("power"))),
            ("GAP", str(player.number("gap"))),
            ("EYE", str(player.number("eye"))),
            ("SPD", str(speed)),
            ("FLD", str(player.number(fld_key))),
        ]

    def _draw_back(self, painter: QPainter, player: PlayerRecord) -> None:
        self._draw_header_rule(painter, f"{player.name} · scouting card")
        self._text(painter, QRectF(48, 86, 480, 52), player.name, 23, INK, True)
        self._text(
            painter,
            QRectF(48, 135, 480, 31),
            f"{player.team_name}  ·  #{player.get('uniform_number', '-')}  ·  {player.position}",
            10,
            MUTED,
        )

        if not self._draw_image(
            painter,
            player.team_logo,
            QRectF(604, 84, 98, 82),
            contain=True,
        ):
            self._rounded_rect(painter, QRectF(620, 96, 82, 58), PANEL, 10, LINE)
            self._text(painter, QRectF(620, 96, 82, 58), "LOGO", 8, MUTED, True, Qt.AlignCenter)

        info_y = 190
        left_rect = QRectF(48, info_y, 406, 298)
        right_rect = QRectF(470, info_y, 232, 298)
        self._rounded_rect(painter, left_rect, WHITE, 14, LINE)
        self._rounded_rect(painter, right_rect, WHITE, 14, LINE)
        self._text(painter, QRectF(68, info_y + 18, 366, 28), "RATINGS", 10, ACCENT, True)

        if player.is_pitcher:
            rating_keys = [
                ("STUFF", "stuff"),
                ("MOVEMENT", "movement"),
                ("CONTROL", "control"),
                ("COMMAND", "command"),
                ("STAMINA", "stamina"),
                ("FIELDING", "pitcher_fielding"),
            ]
        else:
            rating_keys = [
                ("CONTACT", "contact"),
                ("POWER", "power"),
                ("GAP", "gap"),
                ("EYE", "eye"),
                ("BASERUN", "baserunning"),
                ("STEAL", "stealing"),
                ("ARM", "arm"),
            ]

        bar_y = info_y + 58
        available_height = 218
        row_h = available_height / len(rating_keys)
        for index, (label, key) in enumerate(rating_keys):
            y = bar_y + index * row_h
            self._draw_rating_bar(
                painter,
                QRectF(68, y, 366, row_h - 5),
                label,
                player.number(key),
            )

        self._text(painter, QRectF(490, info_y + 18, 192, 28), "PROFILE", 10, ACCENT, True)
        bats = short_hand(player.get("bats"))
        throws = short_hand(player.get("throws"))
        profile_lines = [
            ("OVR", str(player.number("overall"))),
            ("POS", player.position),
            ("B/T", f"{bats}/{throws}"),
            ("ROLE", player.get("role", "-")),
        ]
        if player.is_pitcher:
            profile_lines.insert(
                3,
                ("ARM SLOT", player.get("arm_slot", "-").replace("_", " ")),
            )
        y = info_y + 60
        for label, value in profile_lines:
            self._text(painter, QRectF(490, y, 76, 26), label, 8, MUTED, True)
            self._text(
                painter,
                QRectF(565, y, 117, 26),
                value,
                9,
                INK,
                True,
                Qt.AlignRight | Qt.AlignVCenter,
            )
            y += 42

        if player.is_pitcher:
            self._draw_pitcher_detail(painter, player, 512)
        else:
            self._draw_batter_detail(painter, player, 512)

        scout_rect = QRectF(48, 780, 654, 214)
        self._rounded_rect(painter, scout_rect, WHITE, 14, LINE)
        self._text(painter, QRectF(68, 798, 614, 28), "SCOUTING REPORT", 10, ACCENT, True)
        self._text(
            painter,
            QRectF(68, 837, 614, 136),
            player.get("scouting_report", "스카우팅 리포트가 없습니다."),
            10,
            INK,
            False,
            Qt.AlignLeft | Qt.AlignTop | Qt.TextWordWrap,
        )
        self._text(
            painter,
            QRectF(48, 1012, 654, 20),
            player.get("series"),
            8,
            MUTED,
            False,
            Qt.AlignRight,
        )

    def _draw_rating_bar(
        self,
        painter: QPainter,
        rect: QRectF,
        label: str,
        value: int,
    ) -> None:
        self._text(
            painter,
            QRectF(rect.x(), rect.y(), 92, rect.height()),
            label,
            7,
            MUTED,
            True,
        )
        self._text(
            painter,
            QRectF(rect.right() - 36, rect.y(), 36, rect.height()),
            str(value),
            8,
            INK,
            True,
            Qt.AlignRight | Qt.AlignVCenter,
        )
        track = QRectF(rect.x() + 100, rect.center().y() - 4, rect.width() - 146, 8)
        self._rounded_rect(painter, track, QColor("#E7EAED"), 4)
        ratio = max(0.0, min(1.0, (value - 20) / 60))
        if ratio > 0:
            fill = QRectF(
                track.x(),
                track.y(),
                max(5, track.width() * ratio),
                track.height(),
            )
            self._rounded_rect(painter, fill, grade_color(value), 4)

    def _draw_batter_detail(
        self,
        painter: QPainter,
        player: PlayerRecord,
        y: int,
    ) -> None:
        rect = QRectF(48, y, 654, 242)
        self._rounded_rect(painter, rect, WHITE, 14, LINE)
        self._text(
            painter,
            QRectF(68, y + 18, 614, 28),
            "DEFENSIVE POSITIONS",
            10,
            ACCENT,
            True,
        )

        center = QPointF(375, y + 155)
        size = 126
        diamond = QPainterPath()
        diamond.moveTo(center.x(), center.y() - size / 2)
        diamond.lineTo(center.x() + size / 2, center.y())
        diamond.lineTo(center.x(), center.y() + size / 2)
        diamond.lineTo(center.x() - size / 2, center.y())
        diamond.closeSubpath()
        painter.setBrush(QColor("#F3F5F4"))
        painter.setPen(QPen(LINE, 2))
        painter.drawPath(diamond)

        positions = {
            "C": (375, y + 214),
            "1B": (455, y + 166),
            "2B": (421, y + 124),
            "3B": (295, y + 166),
            "SS": (329, y + 124),
            "LF": (244, y + 95),
            "CF": (375, y + 76),
            "RF": (506, y + 95),
        }
        for pos, (x, py) in positions.items():
            value = player.number(f"def_{pos.lower()}")
            if value <= 0:
                continue
            primary = pos == player.position
            badge = QRectF(x - 27, py - 18, 54, 36)
            self._rounded_rect(
                painter,
                badge,
                ACCENT if primary else SOFT_ACCENT,
                9,
                ACCENT if not primary else None,
            )
            self._text(
                painter,
                badge,
                f"{pos} {value}",
                8,
                WHITE if primary else ACCENT,
                True,
                Qt.AlignCenter,
            )

        self._text(painter, QRectF(68, y + 70, 122, 22), "주 포지션", 8, MUTED, True)
        self._rounded_rect(painter, QRectF(68, y + 103, 28, 18), ACCENT, 5)
        self._text(painter, QRectF(105, y + 98, 90, 28), player.position, 9, INK, True)
        self._text(
            painter,
            QRectF(68, y + 145, 122, 22),
            "표시된 위치만 소화",
            8,
            MUTED,
        )

    def _draw_pitcher_detail(
        self,
        painter: QPainter,
        player: PlayerRecord,
        y: int,
    ) -> None:
        rect = QRectF(48, y, 654, 242)
        self._rounded_rect(painter, rect, WHITE, 14, LINE)
        self._text(painter, QRectF(68, y + 18, 300, 28), "PITCH ARSENAL", 10, ACCENT, True)
        velocity = player.number("velocity_kmh")
        self._text(
            painter,
            QRectF(500, y + 13, 182, 40),
            f"{velocity} km/h",
            17,
            ACCENT,
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
            (name, player.number(key))
            for name, key in pitches
            if player.number(key) > 0
        ]
        if not active:
            self._text(
                painter,
                QRectF(68, y + 82, 614, 80),
                "등록된 구종이 없습니다.",
                10,
                MUTED,
                False,
                Qt.AlignCenter,
            )
            return
        columns = 2
        cell_w = 296
        for index, (name, value) in enumerate(active[:8]):
            col = index % columns
            row = index // columns
            x = 68 + col * 314
            py = y + 68 + row * 40
            self._text(painter, QRectF(x, py, cell_w - 52, 28), name, 8, INK, True)
            self._rounded_rect(
                painter,
                QRectF(x + cell_w - 44, py + 3, 44, 24),
                SOFT_ACCENT,
                7,
            )
            self._text(
                painter,
                QRectF(x + cell_w - 44, py + 3, 44, 24),
                str(value),
                8,
                ACCENT,
                True,
                Qt.AlignCenter,
            )


class CardStudioWindow(QMainWindow):
    def __init__(self, csv_path: Path | None = None) -> None:
        super().__init__()
        self.csv_path = csv_path or DEFAULT_CSV
        self.players: list[PlayerRecord] = []
        self.current: PlayerRecord | None = None
        self.side = "front"
        self.renderer = CardRenderer()

        PLAYER_ASSETS.mkdir(parents=True, exist_ok=True)
        TEAM_ASSETS.mkdir(parents=True, exist_ok=True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

        self.setWindowTitle("Team Yukkies Card Studio")
        self.resize(1420, 900)
        self.setMinimumSize(1100, 720)
        self._build_ui()
        self._apply_style()
        self.reload_csv()

    def _build_ui(self) -> None:
        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        header = QWidget()
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 14, 24, 14)
        title = QLabel("TEAM YUKKIES  /  CARD STUDIO")
        title.setObjectName("appTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        self.csv_label = QLabel()
        self.csv_label.setObjectName("muted")
        header_layout.addWidget(self.csv_label)
        open_csv = QPushButton("CSV 열기")
        open_csv.clicked.connect(self.choose_csv)
        reload_button = QPushButton("새로고침")
        reload_button.clicked.connect(self.reload_csv)
        header_layout.addWidget(open_csv)
        header_layout.addWidget(reload_button)
        root_layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_player_panel())
        splitter.addWidget(self._build_preview_panel())
        splitter.addWidget(self._build_inspector_panel())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)
        splitter.setSizes([290, 760, 330])
        root_layout.addWidget(splitter, 1)
        self.setCentralWidget(root)

    def _section_title(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("sectionTitle")
        return label

    def _build_player_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("sidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        layout.addWidget(self._section_title("선수"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("이름 또는 작품 검색")
        self.search.textChanged.connect(self._filter_players)
        layout.addWidget(self.search)
        self.player_list = QListWidget()
        self.player_list.currentItemChanged.connect(self._player_selected)
        layout.addWidget(self.player_list, 1)
        return panel

    def _build_preview_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("previewPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(24, 18, 24, 18)
        layout.setSpacing(14)
        tabs = QHBoxLayout()
        self.front_button = QPushButton("앞면")
        self.back_button = QPushButton("뒷면")
        for button in (self.front_button, self.back_button):
            button.setCheckable(True)
            button.setObjectName("segment")
            tabs.addWidget(button)
        self.front_button.setChecked(True)
        self.front_button.clicked.connect(lambda: self.set_side("front"))
        self.back_button.clicked.connect(lambda: self.set_side("back"))
        tabs.addStretch()
        layout.addLayout(tabs)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setAlignment(Qt.AlignCenter)
        self.preview = QLabel("선수를 선택하세요")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(520, 650)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        scroll.setWidget(self.preview)
        layout.addWidget(scroll, 1)
        return panel

    def _build_inspector_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("sidePanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        layout.addWidget(self._section_title("선수 정보"))
        self.info = QLabel("-")
        self.info.setWordWrap(True)
        self.info.setObjectName("infoBlock")
        layout.addWidget(self.info)

        layout.addSpacing(10)
        layout.addWidget(self._section_title("에셋"))
        self.player_asset_status = QLabel("선수 이미지: -")
        self.team_asset_status = QLabel("팀 로고: -")
        self.player_asset_status.setObjectName("muted")
        self.team_asset_status.setObjectName("muted")
        layout.addWidget(self.player_asset_status)
        player_asset = QPushButton("선수 이미지 등록 / 교체")
        player_asset.clicked.connect(self.register_player_image)
        layout.addWidget(player_asset)
        layout.addWidget(self.team_asset_status)
        team_asset = QPushButton("팀 로고 등록 / 교체")
        team_asset.clicked.connect(self.register_team_logo)
        layout.addWidget(team_asset)

        layout.addSpacing(10)
        layout.addWidget(self._section_title("내보내기"))
        export_side = QPushButton("현재 면 PNG 저장")
        export_side.setObjectName("primary")
        export_side.clicked.connect(self.export_current)
        export_both = QPushButton("앞면 + 뒷면 PNG 저장")
        export_both.clicked.connect(self.export_both)
        layout.addWidget(export_side)
        layout.addWidget(export_both)
        layout.addStretch()
        self.status = QLabel("CSV와 에셋 변경은 미리보기에 즉시 반영됩니다.")
        self.status.setWordWrap(True)
        self.status.setObjectName("muted")
        layout.addWidget(self.status)
        return panel

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #F7F8F8; color: #18222D; font-family: "Malgun Gothic"; font-size: 13px; }
            #header { background: #FFFFFF; border-bottom: 1px solid #DDE2E7; }
            #appTitle { font-size: 15px; font-weight: 700; letter-spacing: 1px; }
            #sidePanel { background: #FFFFFF; }
            #previewPanel { background: #F2F4F5; }
            #sectionTitle { font-size: 13px; font-weight: 700; }
            #muted { color: #78838E; font-size: 11px; }
            #infoBlock { background: #F7F8F8; border: 1px solid #E1E5E8; border-radius: 8px; padding: 12px; }
            QLineEdit { background: #FFFFFF; border: 1px solid #D8DDE2; border-radius: 7px; padding: 9px 10px; }
            QListWidget { background: transparent; border: none; outline: none; }
            QListWidget::item { padding: 10px 9px; border-radius: 7px; margin: 1px 0; }
            QListWidget::item:selected { background: #E8EEF3; color: #1E3C55; }
            QPushButton { background: #FFFFFF; border: 1px solid #D4DAE0; border-radius: 7px; padding: 8px 12px; }
            QPushButton:hover { border-color: #AAB4BD; background: #FAFBFB; }
            QPushButton:pressed { background: #F0F2F3; }
            QPushButton#primary { background: #294A67; color: #FFFFFF; border-color: #294A67; font-weight: 700; }
            QPushButton#segment { min-width: 90px; }
            QPushButton#segment:checked { background: #294A67; color: white; border-color: #294A67; }
            QSplitter::handle { background: #E2E6E9; width: 1px; }
            QScrollArea { background: transparent; }
            """
        )

    def choose_csv(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "PLAYER_RATINGS CSV 선택",
            str(self.csv_path.parent),
            "CSV (*.csv)",
        )
        if not filename:
            return
        self.csv_path = Path(filename)
        self.reload_csv()

    def reload_csv(self) -> None:
        if not self.csv_path.exists():
            QMessageBox.warning(
                self,
                "CSV 없음",
                f"CSV 파일을 찾을 수 없습니다.\n{self.csv_path}",
            )
            return
        try:
            self.players = load_players(self.csv_path)
        except Exception as exc:
            QMessageBox.critical(self, "CSV 오류", f"CSV를 읽지 못했습니다.\n{exc}")
            return
        self.csv_label.setText(f"{self.csv_path.name} · {len(self.players)} players")
        previous_id = self.current.player_id if self.current else None
        self._populate_players(previous_id)

    def _populate_players(self, select_id: str | None = None) -> None:
        self.player_list.clear()
        query = self.search.text().strip().lower()
        selected_row = -1
        for player in self.players:
            haystack = f"{player.name} {player.get('series')} {player.position}".lower()
            if query and query not in haystack:
                continue
            item = QListWidgetItem(
                f"{player.name}\n{player.position}  ·  {player.get('series')}"
            )
            item.setData(Qt.UserRole, player.player_id)
            self.player_list.addItem(item)
            if select_id and player.player_id == select_id:
                selected_row = self.player_list.count() - 1
        if self.player_list.count():
            self.player_list.setCurrentRow(selected_row if selected_row >= 0 else 0)

    def _filter_players(self) -> None:
        self._populate_players(self.current.player_id if self.current else None)

    def _player_selected(
        self,
        current: QListWidgetItem | None,
        _previous: QListWidgetItem | None,
    ) -> None:
        if current is None:
            return
        player_id = current.data(Qt.UserRole)
        self.current = next(
            (p for p in self.players if p.player_id == player_id),
            None,
        )
        self.refresh_current()

    def set_side(self, side: str) -> None:
        self.side = side
        self.front_button.setChecked(side == "front")
        self.back_button.setChecked(side == "back")
        self.refresh_preview()

    def refresh_current(self) -> None:
        player = self.current
        if not player:
            return
        bats = short_hand(player.get("bats"))
        throws = short_hand(player.get("throws"))
        self.info.setText(
            f"<b>{player.name}</b><br>"
            f"{player.get('series')}<br><br>"
            f"{player.team_name} · #{player.get('uniform_number', '-')} · {player.position}<br>"
            f"OVR {player.number('overall')} · B/T {bats}/{throws}<br>"
            f"{player.get('role', '')}"
        )
        self.player_asset_status.setText(
            f"선수 이미지: {'등록됨' if player.player_image.exists() else '미등록'}"
        )
        self.team_asset_status.setText(
            f"팀 로고: {'등록됨' if player.team_logo.exists() else '미등록'}"
        )
        self.refresh_preview()

    def refresh_preview(self) -> None:
        if not self.current:
            return
        image = self.renderer.render(self.current, self.side)
        pixmap = QPixmap.fromImage(image)
        width = max(420, min(680, self.preview.width() - 24))
        height = max(560, self.preview.height() - 24)
        scaled = pixmap.scaled(
            width,
            height,
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.preview.setPixmap(scaled)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if self.current:
            self.refresh_preview()

    def _register_asset(self, target: Path, label: str) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self,
            f"{label} 선택",
            str(PROJECT_DIR),
            "Images (*.png *.jpg *.jpeg *.webp *.bmp)",
        )
        if not filename:
            return
        image = QImage(filename)
        if image.isNull():
            QMessageBox.warning(self, "이미지 오류", "선택한 이미지를 읽을 수 없습니다.")
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        if not image.save(str(target), "PNG"):
            QMessageBox.warning(
                self,
                "저장 오류",
                f"이미지를 저장하지 못했습니다.\n{target}",
            )
            return
        self.status.setText(f"{label} 저장: {target.relative_to(PROJECT_DIR)}")
        self.refresh_current()

    def register_player_image(self) -> None:
        if self.current:
            self._register_asset(self.current.player_image, "선수 이미지")

    def register_team_logo(self) -> None:
        if self.current:
            self._register_asset(self.current.team_logo, "팀 로고")

    def export_current(self) -> None:
        if not self.current:
            return
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        default = OUTPUT_DIR / f"{self.current.player_id}_{self.side}.png"
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "PNG 저장",
            str(default),
            "PNG (*.png)",
        )
        if not filename:
            return
        path = Path(filename)
        image = self.renderer.render(self.current, self.side)
        if image.save(str(path), "PNG"):
            self.status.setText(f"PNG 저장 완료: {path}")
        else:
            QMessageBox.warning(self, "저장 오류", "PNG 저장에 실패했습니다.")

    def export_both(self) -> None:
        if not self.current:
            return
        folder = QFileDialog.getExistingDirectory(
            self,
            "앞면/뒷면 저장 폴더",
            str(OUTPUT_DIR),
        )
        if not folder:
            return
        target_dir = Path(folder)
        for side in ("front", "back"):
            path = target_dir / f"{self.current.player_id}_{side}.png"
            if not self.renderer.render(self.current, side).save(str(path), "PNG"):
                QMessageBox.warning(
                    self,
                    "저장 오류",
                    f"PNG 저장에 실패했습니다.\n{path}",
                )
                return
        self.status.setText(f"2개 PNG 저장 완료: {target_dir}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Team Yukkies player-card preview and PNG exporter"
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=DEFAULT_CSV,
        help="PLAYER_RATINGS.csv path",
    )
    args = parser.parse_args()

    app = QApplication(sys.argv[:1])
    app.setApplicationName("Team Yukkies Card Studio")
    app.setStyle("Fusion")
    window = CardStudioWindow(args.csv)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
