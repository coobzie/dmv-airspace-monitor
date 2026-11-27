from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from src.api import OpenSkyError
from src.config import AIRPORTS, REFRESH_SECONDS
from src.pipeline import get_aircraft
from src.rules import RULES, run_rules

TIMEZONE = ZoneInfo("America/New_York")
COLOR_AIRBORNE = "#1f77b4"
COLOR_GROUND = "#868e96"
COLOR_ALERT = "#e03131"

st.set_page_config(page_title="DMV Airspace Monitor", page_icon="✈️", layout="wide")


@st.cache_data(ttl=REFRESH_SECONDS, show_spinner="Fetching live aircraft...")
def load_data():
    """Fetch one snapshot. Cached, so every viewer shares it."""
    df = get_aircraft()
    return df, run_rules(df), datetime.now(TIMEZONE)

def safe_name(row):
    name = row["Callsign"] if pd.notna(row["Callsign"]) else row["ICAO24"]
    return "".join(ch for ch in str(name) if ch.isalnum())






#Load data

st.title("DMV Airspace Monitor")
st.caption("Live ADS-B traffic around the DMV airports via the OpenSky Network API.")


#Sidebar

with st.sidebar:
    st.header("Filters")
    selected = st.multiselect("Airports", options=list(AIRPORTS), default=list(AIRPORTS))
    show_ground = st.toggle("Include aircraft on the ground", value=True)
    if st.button("Refresh now"):
        st.cache_data.clear()
        st.rerun()
st.caption(f"Data refreshes at most every {REFRESH_SECONDS} seconds to respect OpenSky's credit limits.")


try:
    df, alerts, fetched_at = load_data()
except OpenSkyError as exc:
    st.error(f"Live data is unavailable right now: {exc}")
    st.stop()

    if df.empty:
        st.info("No aircraft found near the three airports right now.")
        st.stop()

st.caption(f"Last updated {fetched_at:%H:%M:%S %Z}")


#Apply filters

view = df[df["airport"].isin(selected)]
if not show_ground:
    view = view[~view["on_ground"]]
alerts_view = alerts[alerts["Airport"].isin(selected)]

#Alert banner
high = alerts_view[alerts_view["Severity"] == "High"]
for _, alert in high.iterrows():
    st.error(f"HIGH: {safe_name(alert)} near {alert['Airport']}. {alert['Detail']}")
lower = len(alerts_view) - len(high)
if lower:
    st.warning(f"{lower} lower-severity flags. See the alerts tab.")


#Metrics

cols = st.columns(len(AIRPORTS) + 1)
cols[0].metric("Aircraft tracked", len(view))
for col, code in zip(cols[1:], AIRPORTS):
    subset = view[view["airport"] == code]
    col.metric(code, len(subset), help=f"{int((~subset['on_ground']).sum())} airborne")

#Tabs
tab_map, tab_aircraft, tab_alerts = st.tabs(["Live map", "Aircraft", "Alerts"])

with tab_map:
    if view.empty:
        st.info("No aircraft match the current filters.")
    else:
        map_df = view[["latitude", "longitude", "icao24", "on_ground"]].copy()
        map_df["color"] = COLOR_AIRBORNE
        map_df.loc[map_df["on_ground"], "color"] = COLOR_GROUND
        map_df.loc[map_df["icao24"].isin(alerts_view["icao24"]), "color"] = COLOR_ALERT
        st.map(map_df, latitude="latitude", longitude="longitude", color="color", size=300)
        st.caption("Blue: airborne. Gray: on the ground. Red: flagged by a rule.")

with tab_aircraft:
    table = view[
        ["callsign", "airport", "altitude_ft", "velocity_kts", "vertical_rate_fpm",
         "squawk", "on_ground", "origin_country", "last_contact_time"]
    ].round({"altitude_ft": 0, "velocity_kts": 0, "vertical_rate_fpm": 0})
    st.dataframe(table.sort_values(["airport", "callsign"]), hide_index=True)

with tab_alerts:
    if alerts_view.empty:
        st.success("No rules triggered right now.")
    else:
        st.dataframe(
            alerts_view[["severity", "rule", "callsign", "airport", "detail"]],
            hide_index=True,
        )
    st.subheader("What each rule means")
    for rule in RULES:
        with st.expander(f"{rule['name']} ({rule['severity']})"):
            st.write(rule["description"])
            st.caption(f"Where it can be wrong: {rule['limitation']}")

