"""
OOTP News Message Parser & Classification Engine (Phase 9)
Parses messageN.txt files for trades, awards (MVP, Cy Young, ROTY, HOF), injuries, contracts.
"""

import os
import glob
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class ParsedNewsMessage:
    message_id: str
    file_path: str
    subject: str
    event_type: str  # mvp, cy_young, roty, trade, fa, injury, hof, world_series, etc.
    player_name: str
    team_name: str
    date_str: str
    body_text: str
    status: str = "new"


class MessageParser:
    AWARD_REGEX = re.compile(r"(MVP|Cy Young|Rookie of the Year|Gold Glove|Platinum Stick|Hall of Fame)", re.IGNORECASE)

    @classmethod
    def parse_message_file(cls, file_path: str) -> Optional[ParsedNewsMessage]:
        if not os.path.exists(file_path):
            return None

        filename = os.path.basename(file_path)
        msg_id = os.path.splitext(filename)[0]

        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        subject = ""
        date_str = "2026-07-01"
        event_type = "general"
        player_name = ""
        team_name = ""

        # Extract subject line if HTML/text header present
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if lines:
            subject = lines[0][:120]

        content_lower = content.lower()
        if "mvp" in content_lower or "most valuable player" in content_lower:
            event_type = "mvp"
        elif "cy young" in content_lower:
            event_type = "cy_young"
        elif "rookie of the year" in content_lower:
            event_type = "roty"
        elif "traded" in content_lower or "trade" in content_lower:
            event_type = "trade"
        elif "injured" in content_lower or "injury" in content_lower:
            event_type = "injury"
        elif "hall of fame" in content_lower:
            event_type = "hof"

        return ParsedNewsMessage(
            message_id=msg_id,
            file_path=file_path,
            subject=subject,
            event_type=event_type,
            player_name=player_name,
            team_name=team_name,
            date_str=date_str,
            body_text=content[:500],
        )

    @classmethod
    def scan_messages_dir(cls, messages_dir: str) -> List[ParsedNewsMessage]:
        if not os.path.exists(messages_dir):
            return []

        pattern = os.path.join(messages_dir, "message*.txt")
        files = glob.glob(pattern)
        parsed_list: List[ParsedNewsMessage] = []

        for f_path in files[:100]:  # Cap scan for responsiveness
            msg = cls.parse_message_file(f_path)
            if msg:
                parsed_list.append(msg)
        return parsed_list
