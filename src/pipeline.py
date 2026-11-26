import pandas as pd

from .api import fetch_states
from .config import AIRPORTS, make_box
from .processing import build_aircraft_table


def get_aircraft():
    all_states = []
    for info in AIRPORTS.values():
        box = make_box(info["lat"], info["lon"])
        all_states.extend(fetch_states(box))
    return build_aircraft_table(all_states)


if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)

    df = get_aircraft()
    if df.empty:
        print("No aircraft found right now.")
    else:
        print(df.groupby("airport")["icao24"].count())
        print(df[["callsign", "airport", "distance_km", "altitude_ft", "on_ground"]].head(10))