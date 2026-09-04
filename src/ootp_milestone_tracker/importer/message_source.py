import os
import re
from pathlib import Path
from typing import List, Optional, Generator, Dict, Tuple
from ootp_milestone_tracker.importer.message_models import RawMessage

PLAYER_TAG_RE = re.compile(r'<([^:>]+):player#(\d+)>')
TEAM_TAG_RE = re.compile(r'<([^:>]+):team#(\d+)>')

def parse_raw_message_file(filepath: Path) -> Optional[RawMessage]:
    try:
        filename = filepath.name
        msg_id_match = re.search(r'message(\d+)\.txt', filename, re.IGNORECASE)
        if not msg_id_match:
            return None
        msg_id = int(msg_id_match.group(1))
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            raw_text = f.read()
            
        players = [(m.group(1), int(m.group(2))) for m in PLAYER_TAG_RE.finditer(raw_text)]
        teams = [(m.group(1), int(m.group(2))) for m in TEAM_TAG_RE.finditer(raw_text)]
        
        return RawMessage.create(
            msg_id=msg_id,
            filename=filename,
            filepath=str(filepath),
            raw_text=raw_text,
            players=players,
            teams=teams
        )
    except Exception:
        return None

def discover_messages(save_dir: Path, min_msg_id: Optional[int] = None) -> Generator[RawMessage, None, None]:
    msg_dir = save_dir / "messages"
    if not msg_dir.exists():
        return
    
    files = list(msg_dir.glob("message*.txt"))
    # Sort by numeric message ID
    def extract_id(p: Path) -> int:
        m = re.search(r'message(\d+)\.txt', p.name, re.IGNORECASE)
        return int(m.group(1)) if m else 0
        
    sorted_files = sorted(files, key=extract_id)
    
    for f in sorted_files:
        if min_msg_id is not None:
            msg_id = extract_id(f)
            if msg_id <= min_msg_id:
                continue
        raw_msg = parse_raw_message_file(f)
        if raw_msg:
            yield raw_msg
