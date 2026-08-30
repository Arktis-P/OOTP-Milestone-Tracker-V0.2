import json
from typing import Dict

from PySide6.QtWidgets import (
    QCheckBox, QDialog, QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from ...milestones.game_evaluator import DEFAULT_GAME_MILESTONE_SETTINGS


class GameMilestoneSettingsDialog(QDialog):
    FAMILY_LABELS = {
        "GAME_HITS": "Hits",
        "GAME_RBI": "RBI",
        "GAME_HR": "Home Runs",
        "GAME_SB": "Stolen Bases",
        "GAME_STRIKEOUTS": "Strikeouts",
    }

    def __init__(self, repo, parent=None):
        super().__init__(parent)
        self.repo = repo
        self.setWindowTitle("Game Milestone Settings")
        self.setMinimumWidth(400)

        self.widgets: Dict[str, tuple[QCheckBox, QLineEdit]] = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        form_layout = QFormLayout()
        form_layout.setSpacing(8)

        current_settings = self.repo.get_game_milestone_rule_settings()

        for key, label_text in self.FAMILY_LABELS.items():
            cfg = current_settings.get(key, DEFAULT_GAME_MILESTONE_SETTINGS[key])
            cb = QCheckBox(label_text)
            cb.setChecked(cfg.get("enabled", True))

            t_str = ", ".join(str(x) for x in cfg.get("thresholds", []))
            line_edit = QLineEdit(t_str)
            line_edit.setPlaceholderText("e.g. 4, 5, 6, 7")

            form_layout.addRow(cb, line_edit)
            self.widgets[key] = (cb, line_edit)

        layout.addLayout(form_layout)

        # Action Buttons
        btn_layout = QHBoxLayout()
        reset_btn = QPushButton("Reset Defaults")
        reset_btn.clicked.connect(self.reset_defaults)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self.on_save)

        btn_layout.addWidget(reset_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def reset_defaults(self):
        for key, (cb, line_edit) in self.widgets.items():
            default_cfg = DEFAULT_GAME_MILESTONE_SETTINGS[key]
            cb.setChecked(default_cfg["enabled"])
            line_edit.setText(", ".join(str(x) for x in default_cfg["thresholds"]))

    def validate_and_parse(self) -> tuple[bool, Dict]:
        new_settings = {}
        for key, (cb, line_edit) in self.widgets.items():
            enabled = cb.isChecked()
            raw_text = line_edit.text().strip()

            if enabled:
                if not raw_text:
                    QMessageBox.warning(self, "Validation Error", f"Enabled family '{self.FAMILY_LABELS[key]}' requires at least one threshold.")
                    return False, {}

                parts = [p.strip() for p in raw_text.replace(";", ",").split(",") if p.strip()]
                thresholds = []
                for p in parts:
                    try:
                        val = int(p)
                        if val <= 0:
                            QMessageBox.warning(self, "Validation Error", f"Thresholds for '{self.FAMILY_LABELS[key]}' must be positive integers.")
                            return False, {}
                        thresholds.append(val)
                    except ValueError:
                        QMessageBox.warning(self, "Validation Error", f"Invalid threshold '{p}' in '{self.FAMILY_LABELS[key]}'. Must be positive integers.")
                        return False, {}

                if not thresholds:
                    QMessageBox.warning(self, "Validation Error", f"Enabled family '{self.FAMILY_LABELS[key]}' requires at least one threshold.")
                    return False, {}

                # Sort ascending, unique
                thresholds = sorted(list(dict.fromkeys(thresholds)))
            else:
                thresholds = []

            new_settings[key] = {"enabled": enabled, "thresholds": thresholds}

        return True, new_settings

    def on_save(self):
        valid, new_settings = self.validate_and_parse()
        if not valid:
            return

        try:
            self.repo.save_game_milestone_rule_settings(new_settings)
            self.repo.rebuild_game_milestone_achievements(new_settings)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save settings: {str(e)}")
