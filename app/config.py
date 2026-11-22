import os
from pathlib import Path

DB_PATH = Path(os.environ.get("HOMEMETER_DB", "homemeter.db"))
LOG_PATH = Path(os.environ.get("HOMEMETER_LOG", "homemeter.log"))

# A month counts as a spike when usage beats the recent average by this share
SPIKE_THRESHOLD = 0.20
SPIKE_HISTORY_MONTHS = 3
HISTORY_MONTHS = 6

# Warn when usage is this close to the next, more expensive tariff block
BLOCK_WARNING_UNITS = {"electricity": 5.0, "water": 1.0}

MIN_PASSWORD_LENGTH = 8
MAX_PEOPLE_PER_HOUSEHOLD = 50
# Highest meter value accepted, to catch typing mistakes like an extra zero
MAX_METER_VALUE = 10_000_000

RWANDA_DISTRICTS = [
    "Gasabo", "Kicukiro", "Nyarugenge",
    "Burera", "Gakenke", "Gicumbi", "Musanze", "Rulindo",
    "Gisagara", "Huye", "Kamonyi", "Muhanga", "Nyamagabe", "Nyanza", "Nyaruguru", "Ruhango",
    "Bugesera", "Gatsibo", "Kayonza", "Kirehe", "Ngoma", "Nyagatare", "Rwamagana",
    "Karongi", "Ngororero", "Nyabihu", "Nyamasheke", "Rubavu", "Rusizi", "Rutsiro",
]

# (utility, lower_units, upper_units_inclusive, price in RWF per unit)
# Electricity: REG residential tariff effective 1 October 2025.
# Water: starting values only; the admin updates them from the current WASAC schedule.
DEFAULT_TARIFFS = [
    ("electricity", 0, 20, 89),
    ("electricity", 20, 50, 310),
    ("electricity", 50, None, 369),
    ("water", 0, 5, 340),
    ("water", 5, 20, 720),
    ("water", 20, 50, 845),
    ("water", 50, None, 877),
]

SAVING_TIPS = {
    "electricity": [
        "Switch off and unplug the TV, decoder and chargers at night.",
        "Replace old bulbs with LED bulbs; they use about 80% less power.",
        "Iron clothes in one batch instead of a few pieces every day.",
        "Boil only the water you need in the kettle.",
        "Keep the fridge door closed and away from the stove.",
    ],
    "water": [
        "Fix dripping taps and leaking toilets quickly.",
        "Turn off the tap while brushing teeth or washing dishes.",
        "Collect rainwater for cleaning and watering plants.",
        "Wash clothes with full loads instead of small ones.",
        "Use a bucket instead of a running hose to wash a car.",
    ],
}
