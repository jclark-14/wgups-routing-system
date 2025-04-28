import re
from datetime import time, datetime

EARLY_DEADLINE_CUTOFF = time(9, 15)
DELAY_TRUCK_ID = 3 

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