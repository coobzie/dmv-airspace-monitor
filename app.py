import streamlit as st

from src.config import AIRPORTS
from src.pipeline import get_aircraft

st.set_page_config(page_title="DMV Airspace Monitor", page_icon="✈️", layout="wide")

st.title("DMV Airspace Monitor")
st.caption("Live ADS-B traffic around the DMV airports via the OpenSky Network API.")

with st.sidebar:
    st.header("Filters")
    selected = st.multiselect("Airports", options=list(AIRPORTS), default=list(AIRPORTS))
    show_ground = st.toggle("Include aircraft on the ground", value=True)


df = get_aircraft()
if df.empty:
    st.info("No aircraft found in the area right now.")
    st.stop()

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

