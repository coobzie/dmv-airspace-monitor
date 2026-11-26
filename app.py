from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from src.api import OpenSkyError
from src.config import AIRPORTS, REFRESH_SECONDS
from src.pipeline import get_aircraft

TIMEZONE = ZoneInfo("America/New_York")

st.set_page_config(page_title="DMV Airspace Monitor", page_icon="✈️", layout="wide")
@st.cache_data(ttl=REFRESH_SECONDS, show_spinner="Fetching live aircraft...")
def load_data():
    """Fetch one snapshot. Cached, so every viewer shares it."""
    return get_aircraft(), datetime.now(TIMEZONE)

st.title("DMV Airspace Monitor")
st.caption("Live ADS-B traffic around the DMV airports via the OpenSky Network API.")

with st.sidebar:
    st.header("Filters")
    selected = st.multiselect("Airports", options=list(AIRPORTS), default=list(AIRPORTS))
    show_ground = st.toggle("Include aircraft on the ground", value=True)
    if st.button("Refresh now"):
        st.cache_data.clear()
        st.rerun()
st.caption(f"Data refreshes at most every {REFRESH_SECONDS} seconds to respect OpenSky's credit limits.")


try:
    df, fetched_at = load_data()
except OpenSkyError as exc:
    st.error(f"Live data is unavailable right now: {exc}")
    st.stop()

    if df.empty:
        st.info("No aircraft found near the three airports right now.")
        st.stop()

st.caption(f"Last updated {fetched_at:%H:%M:%S %Z}")

view = df[df["airport"].isin(selected)]
if not show_ground:
    view = view[~view["on_ground"]]

cols = st.columns(len(AIRPORTS) + 1)
cols[0].metric("Aircraft tracked", len(view))
for col, code in zip(cols[1:], AIRPORTS):
    col.metric(code, int((view["airport"] == code).sum()))

if view.empty:
    st.info("No aircraft match the selected filters.")
else:
    st.map(view, latitude="latitude", longitude="longitude")
    table = view[
        ["callsign", "airport", "altitude_ft", "velocity_kts", "squawk", "on_ground", "origin_country"]
    ].round({"altitude_ft": 0, "velocity_kts": 0})
    st.dataframe(table.sort_values(["airport", "callsign"]), hide_index=True)

