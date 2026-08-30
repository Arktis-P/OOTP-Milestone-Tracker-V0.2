from PySide6.QtCore import Qt
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
