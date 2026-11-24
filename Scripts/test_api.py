import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

client_secret = os.getenv("OPENSKY_CLIENT_SECRET")
client_id = os.getenv("OPENSKY_CLIENT_ID")

print("Client ID loaded:", client_id is not None)
print("Client Secret loaded:", client_secret is not None)


# Body of the request
payload = {
    "grant_type": "client_credentials",
    "client_id": client_id,
    "client_secret": client_secret,
}


# data= send the payload form-encoded
# json= would send it as JSON, wrong format
# timeout= stops the script from hanging indefinitely if server stalls or is unreachable
response = requests.post(TOKEN_URL, data=payload, timeout=10)

print("Status code:", response.status_code)

if response.status_code == 200:
    # .json() turns response body into py dictionary
    token_data = response.json()

    #Which fields did the server return?
    print("Response keys:", list(token_data.keys()))

    #Print only the first 10 of the token
    access_token = token_data["access_token"]
    print("Token starts with", access_token[:10])

    #How long is the token valid in seconds?
    print("Expires in (seconds):", token_data["expires_in"])

else:
    #Safe to print, failed contains no token
    print("Request failed:", response.text)

