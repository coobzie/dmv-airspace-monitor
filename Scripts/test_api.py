import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
STATES_URL = "https://opensky-network.org/api/states/all"


#Approx box around Dulles (IAD)
# lamin/lamax = latitude (N/S), lomin/lomax = longitude (E/W)
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

client_secret = os.getenv("OPENSKY_CLIENT_SECRET")
client_id = os.getenv("OPENSKY_CLIENT_ID")


# Body of the request
payload = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
}


# data= send the payload form-encoded
# json= would send it as JSON, wrong format
# timeout= stops the script from hanging indefinitely if server stalls or is unreachable
token_response = requests.post(TOKEN_URL, data=payload, timeout=10)

print("Token status:", token_response.status_code)

if token_response.status_code == 200:
    # .json() turns response body into py dictionary
    access_token = token_response.json()["access_token"]

    #Send token in authorization header
    headers = {"Authorization": f"Bearer {access_token}"}

    # params= turns the dictionary into ?lamin=...&lomin=... on the URL
    states_response = requests.get(
        STATES_URL, headers=headers, params=IAD_BOX, timeout=10
    )
    print("States status:", states_response.status_code)

    if states_response.status_code == 200:
        states = states_response.json()["states"]

    
        if states is None:
            print("No aircraft found in the Dulles area.")
        else:
            print("Aircraft found:", len(states))

        first = dict(zip(FIELD_NAMES, states[0]))


        if first["callsign"] is not None:
            first["callsign"] = first["callsign"].strip()

        print("First aircraft, labeled:")
        for name, value in first.items():
            print(f"{name}: {value}")

        print("\nFirst five aircraft:")
        for state in states[:5]:
            aircraft = dict(zip(FIELD_NAMES, state))
            callsign = aircraft["callsign"]
            if callsign is not None:
                callsign = callsign.strip()
            print(
                callsign,
                aircraft["latitude"],
                aircraft["longitude"],
                "on_ground:", aircraft["on_ground"],
            )
    else:
        print("States request failed:", states_response.text)
else:
    print("Token request failed:", token_response.text)
    