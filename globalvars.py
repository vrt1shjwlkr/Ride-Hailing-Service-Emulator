# This file contains all the globals required at different stages of the simulation
# include this file in all other files.
from __future__ import division
# rider states

SATISFIED=0
LOOKING_FOR_DRIVER=1
WAITING_FOR_DRIVER_ACCEPTANCE=2
WAITING_FOR_DRIVER_PICKUP=3
RIDING=4

# driver states
OFFLINE=5
WAITING_FOR_RIDE_REQ=6
RIDE_REQ_ACCEPTED=7
WAITING_FOR_RIDER_PICKUP=8
LOOKING_FOR_DRIVER_WAITING=9

# Uber cost variables derived from uberBlack service in NYC {http://uberestimate.com/prices/New-York-City/}
fuel_cost = 0
base_fare = 7

# Avenue Franklin Delano Roosevelt, 75008 Paris, France -----> Arc de Triomphe, Paris, France : 1.4km, 298sec according to Uber Movements => ~240 seconds/Km
# According to NYC uber rates, per minute charges = 0.65 => 2.6/240seconds
# According to NYC uber rates, per Km charges = ~2.4$ => per 240 seconds charges ~ 2.4 + 2.6 = 5

fare_per_sec = (5/240)
service_charge = 0
min_fare = 15

SEARCH_RAD=2500
MAX_SEARCH_RAD=2500

EXTRA_TRIAL_PENALTY=10


# rider states
SATISFIED=0
LOOKING_FOR_DRIVER=1
WAITING_FOR_DRIVER_ACCEPTANCE=2
WAITING_FOR_DRIVER_PICKUP=3
RIDING=4
# driver states
OFFLINE=5
WAITING_FOR_RIDE_REQ=6
RIDE_REQ_ACCEPTED=7
WAITING_FOR_RIDER_PICKUP=8