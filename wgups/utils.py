import re
from datetime import datetime
from typing import Optional

START_TIME = datetime.strptime("8:00", "%H:%M")

# Regex constants
TIME_RE = re.compile(r'(\d{1,2}:\d{2})\s*(am|pm)?', re.I)
_TRUCK_RE = re.compile(r'\btruck\s+(\d+)\b', re.IGNORECASE)

def time_from_str(note: str) -> datetime | None:
    """Extract datetime from note using regex or returns None"""
    m = TIME_RE.search(note)
    if not m:
        return None
    hh_mm, ampm = m.groups()
    format_time = "%I:%M %p" if ampm else "%H:%M"
    return datetime.combine(datetime.today().date(),
                            datetime.strptime(f"{hh_mm} {ampm or ''}".strip(), format_time).time())

def truck_from_note(note: str) -> Optional[int]:
    """Grab X in “truck X”, return X as int, or None if otherwise."""
    m = _TRUCK_RE.search(note)
    return int(m.group(1)) if m else None
