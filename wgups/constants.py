import re
from datetime import time, datetime

# === Time Constants ===

TODAY = datetime.today().date()  # Anchor date for all datetime comparisons
START_TIME = datetime.combine(TODAY, time(8, 0))  # Trucks depart at 8:00 AM

EARLY_DEADLINE_CUTOFF = time(9, 15)  # Used to prioritize critical packages
STRICT_DEADLINE_CUTOFF = datetime.strptime("10:00", "%H:%M").time()  # 10:00 AM delivery window

# === Package Status Constants ===

STATUS_AT_HUB = "AT_HUB"
STATUS_EN_ROUTE = "EN_ROUTE"
STATUS_DELIVERED = "DELIVERED"

# === Regex Patterns for Parsing Notes ===

TIME_RE = re.compile(r'(\d{1,2}:\d{2})\s*(am|pm)?', re.I)  # Parses timestamps like '9:05 AM'
TRUCK_RE = re.compile(r'\btruck\s+(\d+)\b', re.IGNORECASE)  # Extracts assigned truck number

# === Address Normalization ===

# Replaces directional words in addresses (e.g., 'South' -> 's')
DIRECTION_MAP = {
    "north": "n",
    "south": "s", 
    "east": "e",
    "west": "w"
}
