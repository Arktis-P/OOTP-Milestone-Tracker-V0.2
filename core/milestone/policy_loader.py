"""
Milestone Policy Loader (Phase 4.1)
Reads milestone definitions from CSV policy files.
"""

import os
import csv
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

DEFAULT_POLICY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "milestones.csv")


@dataclass
class MilestonePolicy:
    category: str
    key: str
    label: str
    scope: str  # game, season, career, team_game, team_season
    stat: str
    threshold: str  # numeric or composite (e.g. "30-30")
    direction: str  # higher, lower, boolean
    grade: str  # common, uncommon, rare, epic, legendary
    track_from: Optional[float] = None
    near_n: Optional[float] = None
    description_template: str = ""

    @property
    def numeric_threshold(self) -> float:
        try:
            return float(self.threshold)
        except ValueError:
            return 0.0


class PolicyLoader:
    @classmethod
    def load_from_csv(cls, csv_path: str = DEFAULT_POLICY_PATH) -> List[MilestonePolicy]:
        if not os.path.exists(csv_path):
            return []

        policies: List[MilestonePolicy] = []
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    tf = float(row["track_from"]) if row.get("track_from") and row["track_from"].strip() else None
                    nn = float(row["near_n"]) if row.get("near_n") and row["near_n"].strip() else None
                    policies.append(
                        MilestonePolicy(
                            category=row["category"].strip(),
                            key=row["key"].strip(),
                            label=row["label"].strip(),
                            scope=row["scope"].strip(),
                            stat=row["stat"].strip(),
                            threshold=row["threshold"].strip(),
                            direction=row["direction"].strip(),
                            grade=row["grade"].strip(),
                            track_from=tf,
                            near_n=nn,
                            description_template=row.get("description_template", "").strip(),
                        )
                    )
                except Exception:
                    continue
        return policies
