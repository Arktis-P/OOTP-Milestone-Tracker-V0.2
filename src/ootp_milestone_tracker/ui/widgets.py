from PySide6.QtCore import QRectF, QSize, Qt
from PySide6.QtGui import QPainter, QPalette, QPen
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QProgressBar, QVBoxLayout, QWidget


class StatBox(QFrame):
    def __init__(self, label: str, value: str = "-"):
        super().__init__()
        self.setObjectName("statBox")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(2)
        label_widget = QLabel(label)
        label_widget.setObjectName("muted")
        self.value_widget = QLabel(value)
        self.value_widget.setObjectName("statValue")
        layout.addWidget(label_widget)
        layout.addWidget(self.value_widget)

    def set_value(self, value) -> None:
        self.value_widget.setText(str(value))


class MilestoneGauge(QWidget):
    def __init__(self, row: dict):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 7)
        layout.setSpacing(4)

        top = QHBoxLayout()
        title = QLabel(row["label"])
        title.setObjectName("sectionTitle")
        numbers = QLabel(f'{row["current_value"]:,.0f} / {row["target_value"]:,.0f}  ·  {row["progress"]:.1f}%')
        numbers.setObjectName("muted")
        top.addWidget(title)
        top.addStretch(1)
        top.addWidget(numbers)

        progress = QProgressBar()
        progress.setRange(0, 1000)
        progress.setValue(int(min(float(row["progress"]), 100.0) * 10))
        progress.setTextVisible(False)

        meta = QLabel(f'{row["scope"].upper()} · {row["stat_key"]}')
        meta.setObjectName("muted")
        meta.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addLayout(top)
        layout.addWidget(progress)
        layout.addWidget(meta)


class MilestoneLadderBar(QWidget):
    """Compact painted bar that shows several career thresholds on one scale."""

    def __init__(self, current_value: float, thresholds):
        super().__init__()
        self.current_value = float(current_value)
        self.thresholds = tuple(sorted(float(value) for value in thresholds))
        self.setMinimumHeight(42)

    def sizeHint(self):
        return QSize(520, 46)

    def paintEvent(self, event):
        if not self.thresholds:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = self.palette()
        accent = palette.color(QPalette.ColorRole.Highlight)
        track = palette.color(QPalette.ColorRole.Mid)
        text = palette.color(QPalette.ColorRole.Text)
        muted = palette.color(QPalette.ColorRole.PlaceholderText)

        left = 8.0
        right = max(left + 1.0, float(self.width()) - 8.0)
        width = right - left
        bar_y = 5.0
        bar_h = 8.0
        max_target = self.thresholds[-1]
        progress = 0.0 if max_target <= 0 else min(max(self.current_value / max_target, 0.0), 1.0)

        track_rect = QRectF(left, bar_y, width, bar_h)
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(track)
        painter.drawRoundedRect(track_rect, 4.0, 4.0)

        if progress > 0:
            painter.setBrush(accent)
            painter.drawRoundedRect(QRectF(left, bar_y, width * progress, bar_h), 4.0, 4.0)

        metrics = painter.fontMetrics()
        for target in self.thresholds:
            ratio = 0.0 if max_target <= 0 else target / max_target
            x = left + width * ratio
            achieved = self.current_value >= target
            tick_color = accent if achieved else text
            painter.setPen(QPen(tick_color, 1.0))
            painter.drawLine(int(x), int(bar_y - 3), int(x), int(bar_y + bar_h + 4))

            label = f"{target:,.0f}"
            label_width = metrics.horizontalAdvance(label) + 8
            label_x = min(max(x - label_width / 2.0, left), right - label_width)
            painter.setPen(accent if achieved else muted)
            painter.drawText(
                QRectF(label_x, 22.0, label_width, 18.0),
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

        painter.end()


class MilestoneLadderGauge(QWidget):
    """One gauge for a milestone series such as 2,000/2,500/3,000/3,500 hits."""

    def __init__(self, title: str, current_value: float, thresholds, unit: str = ""):
        super().__init__()
        thresholds = tuple(sorted(thresholds))
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 9)
        layout.setSpacing(3)

        top = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")

        next_target = next((value for value in thresholds if current_value < value), None)
        if next_target is None:
            summary = f"{current_value:,.0f} {unit}  ·  {thresholds[-1]:,} achieved"
        else:
            remaining = max(0, int(round(next_target - current_value)))
            summary = f"{current_value:,.0f} {unit}  ·  {remaining:,} to {next_target:,}"
        numbers = QLabel(summary.strip())
        numbers.setObjectName("muted")

        top.addWidget(title_label)
        top.addStretch(1)
        top.addWidget(numbers)

        layout.addLayout(top)
        layout.addWidget(MilestoneLadderBar(current_value, thresholds))
