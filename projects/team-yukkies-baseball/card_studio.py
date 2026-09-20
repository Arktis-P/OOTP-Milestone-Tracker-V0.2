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

from card_layout_v2 import CARD_HEIGHT, CARD_WIDTH
from card_renderer_modular import ModularCardRenderer
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




class CardStudioWindow(QMainWindow):
    def __init__(self, csv_path: Path | None = None) -> None:
        super().__init__()
        self.csv_path = csv_path or DEFAULT_CSV
        self.players: list[PlayerRecord] = []
        self.current: PlayerRecord | None = None
        self.side = "front"
        self.renderer = ModularCardRenderer(PROJECT_DIR)

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
        self.preview.setMinimumSize(450, 800)
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
        self.status = QLabel(f"미리보기와 PNG 출력은 동일한 {CARD_WIDTH} × {CARD_HEIGHT} (9:16) 렌더를 사용합니다.")
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
