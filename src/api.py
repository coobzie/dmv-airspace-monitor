import logging
import os
import time

import requests
from dotenv import load_dotenv

from .config import TOKEN_URL, STATES_URL

load_dotenv()
logger = logging.getLogger(__name__)

TOKEN_SAFETY_MARGIN = 60  # renew the token this many seconds before it expires


class OpenSkyError(Exception):
    """We could not get data from OpenSky. The message is safe to show to users."""


# Module-level cache: lives as long as the Python process does.
_token_cache = {"token": None, "expires_at": 0.0}


def _request_new_token():
    client_id = os.getenv("OPENSKY_CLIENT_ID")
    client_secret = os.getenv("OPENSKY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise OpenSkyError("API credentials are not configured.")

    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
    }
    try:
        response = requests.post(TOKEN_URL, data=payload, timeout=10)
    except requests.exceptions.RequestException as exc:
        raise OpenSkyError("Could not reach the OpenSky login server.") from exc

    if response.status_code != 200:
        logger.warning("Token request failed: %s %s", response.status_code, response.text[:200])
        raise OpenSkyError(f"OpenSky login failed (HTTP {response.status_code}).")

    data = response.json()
    _token_cache["token"] = data["access_token"]
    _token_cache["expires_at"] = time.time() + data["expires_in"] - TOKEN_SAFETY_MARGIN
    return _token_cache["token"]


def get_token():
    """Return a valid token, requesting a new one only when needed."""
    if _token_cache["token"] and time.time() < _token_cache["expires_at"]:
        return _token_cache["token"]
    return _request_new_token()


def fetch_states(box, _retry=True):
    """Return the raw state vectors inside a bounding box (an empty list if none)."""
    headers = {"Authorization": f"Bearer {get_token()}"}
    try:
        response = requests.get(STATES_URL, headers=headers, params=box, timeout=15)
    except requests.exceptions.RequestException as exc:
        raise OpenSkyError("Could not reach OpenSky.") from exc

    if response.status_code == 401 and _retry:
        _token_cache["token"] = None  # the token was rejected, so force a fresh one
        return fetch_states(box, _retry=False)
    if response.status_code == 429:
        raise OpenSkyError("OpenSky rate limit reached. Try again later.")
    if response.status_code != 200:
        logger.warning("States request failed: %s %s", response.status_code, response.text[:200])
        raise OpenSkyError(f"OpenSky returned HTTP {response.status_code}.")

    return response.json()["states"] or []