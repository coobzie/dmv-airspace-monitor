Pass a pre-built token via token_manager
Pass client_id and client_secret (oAuth2)
Token requests sent to https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token
Grant type is client_credentials
Tokens expire after 30min

Top level fields retrieve:
get_arrivals_by_airport
get_departures_by_airport
get_flights_by_aircraft
get_flights_from_interval
get_my_states
get_states
get_track_by_aircraft

Top level fields return:
class opensky_api.OpenSkyStates
class opensky_api.StateVector
class opensky_api.FlightData
class opensky_api.Waypoint
class opensky_api.FlightTrack


URL to return all states vector: https://opensky-network.org/api/states/all

bounding box of WGS84 coordinates, use:
lamin type:float lower bound for latitude in decimal degrees
lomin type:float lower bound for longitude in decimal degrees
lamax type:float upper bound for latitude in decimal degrees
lomax type:float upper bound for longitude in decimal degrees

Can request category of any aircraft by adding parameter "extended" type:integer set to 1

small box requests cost 1 credit



0

icao24

string

Unique ICAO 24-bit address of the transponder in hex string representation.

1

callsign

string

Callsign of the vehicle (8 chars). Can be null if no callsign has been received.

2

origin_country

string

Country name inferred from the ICAO 24-bit address.

3

time_position

int

Unix timestamp (seconds) for the last position update. Can be null if no position report was received by OpenSky within the past 15s.

4

last_contact

int

Unix timestamp (seconds) for the last update in general. This field is updated for any new, valid message received from the transponder.

5

longitude

float

WGS-84 longitude in decimal degrees. Can be null.

6

latitude

float

WGS-84 latitude in decimal degrees. Can be null.

7

baro_altitude

float

Barometric altitude in meters. Can be null.

8

on_ground

boolean

Boolean value which indicates if the position was retrieved from a surface position report.

9

velocity

float

Velocity over ground in m/s. Can be null.

10

true_track

float

True track in decimal degrees clockwise from north (north=0°). Can be null.

11

vertical_rate

float

Vertical rate in m/s. A positive value indicates that the airplane is climbing, a negative value indicates that it descends. Can be null.

12

sensors

int[]

IDs of the receivers which contributed to this state vector. Is null if no filtering for sensor was used in the request.

13

geo_altitude

float

Geometric altitude in meters. Can be null.

14

squawk

string

The transponder code aka Squawk. Can be null.

15

spi

boolean

Whether flight status indicates special purpose indicator.

16

position_source

int

Origin of this state’s position.

0 = ADS-B

1 = ASTERIX

2 = MLAT

3 = FLARM

17

category

int

Aircraft category.

0 = No information at all

1 = No ADS-B Emitter Category Information

2 = Light (< 15500 lbs)

3 = Small (15500 to 75000 lbs)

4 = Large (75000 to 300000 lbs)

5 = High Vortex Large (aircraft such as B-757)

6 = Heavy (> 300000 lbs)

7 = High Performance (> 5g acceleration and 400 kts)

8 = Rotorcraft

9 = Glider / sailplane

10 = Lighter-than-air

11 = Parachutist / Skydiver

12 = Ultralight / hang-glider / paraglider

13 = Reserved

14 = Unmanned Aerial Vehicle

15 = Space / Trans-atmospheric vehicle

16 = Surface Vehicle – Emergency Vehicle

17 = Surface Vehicle – Service Vehicle

18 = Point Obstacle (includes tethered balloons)

19 = Cluster Obstacle

20 = Line Obstacle




Fields most likely needed for map:
6 - latitude
5 - longitude
0 - icao24
1 - callsign

Fields needed for Squawk alerts:
14 - squawk
0 - icao24
1 - callsign
6 - latitude
5 - longitude
7 - baro_altitude
4 - last_contact

Field for on runway or in air:
8 - on_ground


IAD box needed to be cut short to the east as it may overlap with DCA.

Airport label is airport closest to, not necessarily flying to.