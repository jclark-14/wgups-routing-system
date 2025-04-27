import re
from datetime import datetime
from typing import Optional

START_TIME = datetime.strptime("8:00", "%H:%M")

# Regex constants
TIME_RE = re.compile(r'(\d{1,2}:\d{2})\s*(am|pm)?', re.I)
_TRUCK_RE = re.compile(r'\btruck\s+(\d+)\b', re.IGNORECASE)

DIRECTION_MAP = {
    "north": "n",
    "south": "s",
    "east": "e",
    "west": "w"
}

# Model status options
STATUS_AT_HUB = "AT_HUB"
STATUS_EN_ROUTE = "EN_ROUTE"
STATUS_DELIVERED = "DELIVERED"

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

def normalize(address: str) -> str:
    # Normalize address string
    address = address.replace("\n", " ").replace(".", "").lower().strip()
    address = address.split("(")[0].strip()
    words = address.split()
    normalized_words = [DIRECTION_MAP.get(word, word) for word in words]
    return " ".join(normalized_words)
