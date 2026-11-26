import os
import requests
from dotenv import load_dotenv
from .config import TOKEN_URL, STATES_URL

load_dotenv()


def get_token():
    client_id = os.getenv("OPENSKY_CLIENT_ID")
    client_secret = os.getenv("OPENSKY_CLIENT_SECRET")
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