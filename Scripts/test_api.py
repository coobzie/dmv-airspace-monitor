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
    "lomax": -77.0,
    }

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
        data = states_response.json()

        # "states" is none when no aircraft are in box
        states = data["states"]
        if states is None:
            print("No aircraft found in the Dulles area.")
        else:
            print("Aircraft found:", len(states))
            print("First state vector:", states[0])
    else:
        print("States request failed:", states_response.text)
else:
    print("Token request failed:", token_response.text)
    