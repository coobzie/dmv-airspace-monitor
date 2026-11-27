import time

import pandas as pd

from .config import (
    EMERGENCY_SQUAWKS, SLOW_LOW_MAX_FT, SLOW_LOW_MAX_KTS, STABLE_CONTACT_SECONDS,
)

ALERT_COLUMNS = [
    "Severity", "Rule", "ICAO24", "Callsign", "Airport", "Latitude", "Longitude", "Detail",
]
SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}

# --- Checks: each returns a True/False value per aircraft ---

def _emergency_squawk(df, now):
    return df["squawk"].isin(list(EMERGENCY_SQUAWKS))


def _slow_low(df, now):
    # Missing speed or altitude compares as False, so those aircraft are not flagged.
    return (
        (~df["on_ground"])
        & (df["velocity_kts"] < SLOW_LOW_MAX_KTS)
        & (df["altitude_ft"] < SLOW_LOW_MAX_FT)
    )


def _airborne_no_callsign(df, now):
    return (~df["on_ground"]) & df["callsign"].isna()


def _stale_contact(df, now):
    return (now - df["last_contact"]) > STABLE_CONTACT_SECONDS


# --- Detail text: one human-readable line per alert ---

def _detail_squawk(row, now):
    return f"Squawk {row['squawk']}: {EMERGENCY_SQUAWKS[row['squawk']]}"


def _detail_slow_low(row, now):
    return (
        f"{row['velocity_kts']:.0f} kts at {row['altitude_ft']:.0f} ft, "
        f"{row['distance_km']:.1f} km from {row['airport']}"
    )


def _detail_no_callsign(row, now):
    return f"Airborne without a callsign, {row['distance_km']:.1f} km from {row['airport']}"


def _detail_stale(row, now):
    return f"No message received for {now - row['last_contact']:.0f} seconds"


RULES = [
    {
        "name": "emergency_squawk",
        "severity": "high",
        "description": "Transponder is squawking 7500 (hijack), 7600 (radio failure) or 7700 (emergency).",
        "limitation": "Pilots sometimes enter these codes by accident or during training, so a flag is a prompt to look, not proof of an emergency.",
        "check": _emergency_squawk,
        "detail": _detail_squawk,
    },
    {
        "name": "slow_low_flier",
        "severity": "medium",
        "description": f"Airborne below {SLOW_LOW_MAX_FT} ft and slower than {SLOW_LOW_MAX_KTS} kts.",
        "limitation": "Helicopters, gliders and light aircraft on approach routinely do this. Aircraft with missing altitude or speed are never flagged.",
        "check": _slow_low,
        "detail": _detail_slow_low,
    },
    {
        "name": "airborne_no_callsign",
        "severity": "low",
        "description": "Airborne aircraft that is not transmitting a callsign.",
        "limitation": "Many private and general aviation aircraft legitimately send no callsign.",
        "check": _airborne_no_callsign,
        "detail": _detail_no_callsign,
    },
    {
        "name": "stale_contact",
        "severity": "low",
        "description": f"No message received from the aircraft for over {STALE_CONTACT_SECONDS} seconds.",
        "limitation": "Usually a coverage gap or a receiver delay, not anything the aircraft did.",
        "check": _stale_contact,
        "detail": _detail_stale,
    },
]


def run_rules(df, now=None):
    """Apply every rule to the aircraft table and return one row per alert."""
    if df.empty:
        return pd.DataFrame(columns=ALERT_COLUMNS)

    now = time.time() if now is None else now
    alerts = []
    for rule in RULES:
        flagged = df[rule["check"](df, now)]
        for _, row in flagged.iterrows():
            alerts.append(
                {
                    "severity": rule["severity"],
                    "rule": rule["name"],
                    "icao24": row["icao24"],
                    "callsign": row["callsign"],
                    "airport": row["airport"],
                    "latitude": row["latitude"],
                    "longitude": row["longitude"],
                    "detail": rule["detail"](row, now),
                }
            )

    out = pd.DataFrame(alerts, columns=ALERT_COLUMNS)
    out = out.sort_values("severity", key=lambda s: s.map(SEVERITY_ORDER), kind="stable")
    return out.reset_index(drop=True)