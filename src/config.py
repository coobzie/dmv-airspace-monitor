#Project-wide settings. Fixed values live here so there is one place to edit.

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
STATES_URL = "https://opensky-network.org/api/states/all"

# Airport centers in decimal degrees. Verify these against an official source.
AIRPORTS = {
    "IAD": {"name": "Washington Dulles International", "lat": 38.9445, "lon": -77.4558},
    "BWI": {"name": "Baltimore/Washington International", "lat": 39.1754, "lon": -76.6683},
    "DCA": {"name": "Reagan Washington National", "lat": 38.8521, "lon": -77.0377},
}

# Half-width of each airport's search box, in degrees (0.25 is about 28 km north-south).
BOX_RADIUS_DEG = 0.25

# Field names in index order (0 to 16), from the OpenSky docs.
# NOTE: longitude (5) comes BEFORE latitude (6).
FIELD_NAMES = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source",
]

METERS_TO_FEET = 3.28084
MS_TO_KNOTS = 1.94384
MS_TO_FEET_PER_MIN = 196.85


def make_box(lat, lon, radius=BOX_RADIUS_DEG):
    """Build an OpenSky bounding box centered on a point."""
    return {
        "lamin": round(lat - radius, 4),
        "lamax": round(lat + radius, 4),
        "lomin": round(lon - radius, 4),
        "lomax": round(lon + radius, 4),
    }