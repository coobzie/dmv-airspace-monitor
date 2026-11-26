import numpy as np
import pandas as pd

from .config import (
    AIRPORTS, FIELD_NAMES, METERS_TO_FEET, MS_TO_KNOTS, MS_TO_FEET_PER_MIN,
)


def clean_states(df):
    """Take the raw states DataFrame and return a cleaned copy."""
    df = df.copy()

    # Without a position we can't map or measure distance, so drop those rows.
    df = df.dropna(subset=["latitude", "longitude"])

    df["callsign"] = df["callsign"].str.strip().replace("", pd.NA)
    df = df.drop(columns=["sensors"])

    df["altitude_ft"] = df["baro_altitude"] * METERS_TO_FEET
    df["geo_altitude_ft"] = df["geo_altitude"] * METERS_TO_FEET
    df["velocity_kts"] = df["velocity"] * MS_TO_KNOTS
    df["vertical_rate_fpm"] = df["vertical_rate"] * MS_TO_FEET_PER_MIN

    df["position_time"] = (
        pd.to_datetime(df["time_position"], unit="s", utc=True)
        .dt.tz_convert("America/New_York")
    )
    df["last_contact_time"] = (
        pd.to_datetime(df["last_contact"], unit="s", utc=True)
        .dt.tz_convert("America/New_York")
    )
    return df


def dedupe_aircraft(df):
    """Overlapping boxes can return the same aircraft twice; keep the freshest report."""
    return (
        df.sort_values("last_contact", ascending=False)
        .drop_duplicates(subset="icao24", keep="first")
    )


def haversine_km(lat1, lon1, lat2, lon2):
    """Great-circle distance in kilometers. Works on pandas Series."""
    earth_radius_km = 6371.0
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi = phi2 - phi1
    dlambda = np.radians(lon2) - np.radians(lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return 2 * earth_radius_km * np.arcsin(np.sqrt(a))


def add_nearest_airport(df):
    """Label each aircraft with its nearest airport and the distance to it."""
    df = df.copy()
    distances = pd.DataFrame(
        {
            code: haversine_km(df["latitude"], df["longitude"], info["lat"], info["lon"])
            for code, info in AIRPORTS.items()
        }
    )
    df["airport"] = distances.idxmin(axis=1)
    df["distance_km"] = distances.min(axis=1)
    return df


def build_aircraft_table(states):
    """Raw state vectors (from any number of boxes) -> one clean, labeled table."""
    if not states:
        return pd.DataFrame()
    raw = pd.DataFrame(states, columns=FIELD_NAMES)
    df = clean_states(raw)
    if df.empty:
        return df
    df = dedupe_aircraft(df)
    df = add_nearest_airport(df)
    return df.reset_index(drop=True)