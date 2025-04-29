import re
from datetime import time, datetime

# Time constants
TODAY = datetime.today().date()
START_TIME = datetime.combine(TODAY, time(8, 0))
EARLY_DEADLINE_CUTOFF = time(9, 15)  
STRICT_DEADLINE_CUTOFF = datetime.strptime("10:00", "%H:%M").time()

# Package status constants
STATUS_AT_HUB = "AT_HUB"
STATUS_EN_ROUTE = "EN_ROUTE"
STATUS_DELIVERED = "DELIVERED"

# Regex for parsing notes
TIME_RE = re.compile(r'(\d{1,2}:\d{2})\s*(am|pm)?', re.I)
TRUCK_RE = re.compile(r'\btruck\s+(\d+)\b', re.IGNORECASE)

# Address normalization mapping
DIRECTION_MAP = {
    "north": "n",
    "south": "s", 
    "east": "e",
    "west": "w"
}