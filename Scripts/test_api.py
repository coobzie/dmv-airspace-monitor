import os
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
STATES_URL = "https://opensky-network.org/api/states/all"


#Approx box around Dulles (IAD)
IAD_BOX = {
    "lamin": 38.7,
    "lamax": 39.3,
    "lomin": -77.8,
    "lomax": -77.2,
    }


# Field names in index order (0 to 16), from the OpenSky docs.
FIELD_NAMES = [
    "icao24",          # 0
    "callsign",        # 1
    "origin_country",  # 2
    "time_position",   # 3
    "last_contact",    # 4
    "longitude",       # 5
    "latitude",        # 6
    "baro_altitude",   # 7
    "on_ground",       # 8
    "velocity",        # 9
    "true_track",      # 10
    "vertical_rate",   # 11
    "sensors",         # 12
    "geo_altitude",    # 13
    "squawk",          # 14
    "spi",             # 15
    "position_source", # 16
]

METERS_TO_FEET = 3.28084
MS_TO_KNOTS = 1.94384
MS_TO_FEET_PER_MIN = 196.85

# Show every column when printing a wide frame
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)

def get_token():
    client_secret = os.getenv("OPENSKY_CLIENT_SECRET")
    client_id = os.getenv("OPENSKY_CLIENT_ID")
    if client_id is None or client_secret is None:
        raise RuntimeError("Missing credentials. Check your .env file.")

    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }


    response = requests.post(TOKEN_URL, data=payload, timeout=10)
    if response.status_code != 200:
        raise RuntimeError(f"Token request failed ({response.status_code}): {response.text}")
    return response.json()["access_token"]



def fetch_states(token, box):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(STATES_URL, headers=headers, params=box, timeout=10)
    if response.status_code != 200:
        raise RuntimeError(f"States request failed ({response.status_code}): {response.text}")
    return response.json()["states"] or []

def clean_states(df):
    df = df.copy()

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

def main():
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)

    token = get_token()
    states = fetch_states(token, IAD_BOX)

    if not states:
        print("No aircraft in the box right now.")
        return

    raw = pd.DataFrame(states, columns=FIELD_NAMES)
    df = clean_states(raw)

    print("Aircraft found:", len(df))
    print(df[["callsign", "latitude", "longitude", "altitude_ft", "velocity_kts", "on_ground"]].head())
    print("Missing callsigns:", df["callsign"].isna().sum())
    print("On the ground:", df["on_ground"].sum())


def explore(df):
    airborne = df[~df["on_ground"]]
    print(f"Airborne: {len(airborne)} | On the ground: {df['on_ground'].sum()}")
    if airborne.empty:
        print("Nothing airborne right now.")
        return

    print("Average altitude (ft):", round(airborne["altitude_ft"].mean()))

    print()
    print("Lowest airborne:")
    print(airborne.nsmallest(3, "altitude_ft")[["callsign", "altitude_ft", "velocity_kts"]])

    print()
    print("Fastest:")
    print(df.nlargest(3, "velocity_kts")[["callsign", "velocity_kts", "on_ground"]])

    print()
    print("Speed by ground status:")
    print(df.groupby("on_ground")["velocity_kts"].agg(["count", "mean", "max"]).round(1))

    print()
    print("Missing callsigns:", df["callsign"].isna().sum())
    print("Origin countries:")
    print(df["origin_country"].value_counts().head())
    explore(df)



if __name__ == "__main__":
    main()


