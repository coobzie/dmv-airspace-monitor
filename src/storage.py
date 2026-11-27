import sqlite3
import time
from contextlib import closing
from pathlib import Path

import pandas as pd

DB_PATH = Path("data") / "airspace.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshots (
captured_at INTEGER NOT NULL,
icao24 TEXT NOT NULL,
callsign TEXT,
airport TEXT,
latitude REAL,
longitude REAL,
altitude_ft REAL,
velocity_kts REAL,
on_ground INTEGER,
squawk TEXT
);
CREATE INDEX IF NOT EXISTS idx_snapshots_time ON snapshots (captured_at);

CREATE TABLE IF NOT EXISTS alerts (
    captured_at  INTEGER NOT NULL,
    severity     TEXT,
    rule         TEXT,
    icao24       TEXT,
    callsign     TEXT,
    airport      TEXT,
    latitude     REAL,
    longitude    REAL,
    detail       TEXT
);
CREATE INDEX IF NOT EXISTS idx_alerts_time ON alerts (captured_at);
"""

SNAPSHOT_COLUMNS = [
    "icao24", "callsign", "airport", "latitude", "longitude",
    "altitude_ft", "velocity_kts", "on_ground", "squawk",
]


def _connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)  # creates the tables on first use
    return conn

def _hour_bucket(epoch_seconds):
    """Unix seconds -> start of the hour, shown in Eastern time."""
    return (
        pd.to_datetime(epoch_seconds, unit="s", utc=True)
        .dt.floor("h")  # floor in UTC first to avoid daylight-saving ambiguity
        .dt.tz_convert("America/New_York")
    )


def save_snapshot(df, alerts, captured_at=None):
    """Append one capture (every aircraft plus every alert) to the database."""
    captured_at = int(time.time()) if captured_at is None else int(captured_at)

    snapshot = df[SNAPSHOT_COLUMNS].copy()
    snapshot.insert(0, "captured_at", captured_at)
    alert_rows = alerts.copy()
    alert_rows.insert(0, "captured_at", captured_at)

    with closing(_connect()) as conn:
        snapshot.to_sql("snapshots", conn, if_exists="append", index=False)
        alert_rows.to_sql("alerts", conn, if_exists="append", index=False)
        conn.commit()


def load_hourly_counts(hours=48):
    """Average aircraft per capture, by hour and airport (one column per airport)."""
    since = int(time.time()) - hours * 3600
    sql = """
        SELECT captured_at, airport, COUNT(*) AS aircraft
        FROM snapshots
        WHERE captured_at >= ?
        GROUP BY captured_at, airport
    """
    with closing(_connect()) as conn:
        df = pd.read_sql_query(sql, conn, params=(since,))
    if df.empty:
        return df

    df["hour"] = _hour_bucket(df["captured_at"])
    hourly = df.groupby(["hour", "airport"])["aircraft"].mean().unstack("airport")
    return hourly.round(1)


def load_alert_counts(hours=48):
    """Alert observations per hour, one column per rule."""
    since = int(time.time()) - hours * 3600
    sql = "SELECT captured_at, rule FROM alerts WHERE captured_at >= ?"
    with closing(_connect()) as conn:
        df = pd.read_sql_query(sql, conn, params=(since,))
    if df.empty:
        return df

    df["hour"] = _hour_bucket(df["captured_at"])
    return df.groupby(["hour", "rule"]).size().unstack("rule", fill_value=0)


def load_recent_alerts(limit=50):
    """The most recent alert observations, newest first."""
    sql = """
        SELECT captured_at, severity, rule, callsign, airport, detail
        FROM alerts
        ORDER BY captured_at DESC
        LIMIT ?
    """
    with closing(_connect()) as conn:
        df = pd.read_sql_query(sql, conn, params=(limit,))
    if df.empty:
        return df

    df["time"] = pd.to_datetime(df["captured_at"], unit="s", utc=True).dt.tz_convert("America/New_York")
    return df[["time", "severity", "rule", "callsign", "airport", "detail"]]