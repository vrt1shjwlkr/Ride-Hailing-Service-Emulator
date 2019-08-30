from __future__ import division
from rhse_util import *
import simpy, os, datetime, random, simplejson, urllib, logging, math, sys

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

# decision configurations

# This function analyses the perceived ETA of driver for real/obfuscated locations and decides whether to serve or not based on linear threshold

def decision_lin_thresh(driver, env):
    location = list(driver.server.database.drivers.distinct("locations",{"userID":driver.id}))
    driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
    in_spl_zone=check_driver_loc(driverLocation)
    eta_t = 15*driver.tolerance if (not driver.uniform_eta and in_spl_zone) else driver.tolerance

    eta_tolerance = eta_t if (driver.req_refusal_count <= 2) else (driver.tolerance + 50*(driver.req_refusal_count - 2))
    print('First decision ETA tolerance {} of Driver {}'.format(eta_tolerance, driver.id))
    if driver.matchedRider.real_loc_req:
        print('Real location: Driver {} received request from Rider {}'.format(driver.id, driver.matchedRider.id))
        diff = driver.matchedRider.driver_eta - eta_tolerance
        if driver.matchedRider.driver_eta > eta_tolerance and random.random() > (diff/eta_tolerance):
            # print('Real Location: Rider {} request rejected sending request to next available driver'.format(driver.matchedRider.id))
            driver.real_send_request_to_next_driver(env)
            return False
        else:
            print('Real Location: Rider {} request accepted by Driver {} at time {}'.format(driver.matchedRider.id, driver.id, env.now))
            driver.matchedRider.real_accept_eta = driver.matchedRider.driver_eta
            return True
    else:
        print('Obfuscated location: Driver {} received request from Rider {}'.format(driver.id, driver.matchedRider.id))
        driver.perceived_eta = driver.calculate_obf_loc_eta()
        diff = driver.perceived_eta - eta_tolerance
        if driver.perceived_eta > eta_tolerance and random.random() > (diff/eta_tolerance):
            if(driver.matchedRider.driver_eta < eta_tolerance):
                print('Driver {} did not accept request of Rider {} due to obfsucated location; increasing numOfExtraTrials'.format(driver.id, driver.matchedRider.id))
                driver.matchedRider.numOfExtraTrials += 1
            else:
                pass
            # print('Obfuscated Location: Rider {} request rejected sending request to next available driver'.format(driver.matchedRider.id))
            driver.obf_send_request_to_next_driver(env)
            # Relocate the driver by adding small noise to her current location
            # driver.relocate()
            return False
        else:
            if second_decision_driver(driver, env):
                print('Obfuscated location: Driver {}: Accepted Rider {}'.format(driver.id, driver.matchedRider.id))
                return True
            else:
                return False

# This function calculates the direction of request location with respect to the location of driver.
# If the direction is out of preferred angle of the driver, chances of acceptance of ride decrease 
# linearly for the request.

def direction(driver, location):
    d_location = list(driver.server.database.drivers.distinct("locations",{"userID":driver.id}))
    DL = [d_location[0].get('coordinates')[0] - location[0], d_location[0].get('coordinates')[1] - location[1]]
    DL_angle = math.degrees(math.atan2(DL[1], DL[0]))
    angle_threshold = driver.dir_tolerance
    dir_diff = 0
    mid_driver_pref = driver.prefered_dir + angle_threshold/2
    opp_mid_driver_pref = mid_driver_pref - 180
    angle = opp_mid_driver_pref if opp_mid_driver_pref > -180 else (opp_mid_driver_pref + 360)

    if (driver.prefered_dir + angle_threshold) >= 180:
        if ((DL_angle > driver.prefered_dir) and (DL_angle < 180)) or ((DL_angle > -180) and (DL_angle <(driver.prefered_dir + angle_threshold - 360))):
            print('Rider {} pick up location in preferred direction'.format(driver.matchedRider.id))
            return False
        else:
            dir_diff = min(abs(driver.prefered_dir - DL_angle), abs(DL_angle - (driver.prefered_dir + angle_threshold - 360)))
            print('Rider {} pick up location NOT in preferred direction; difference {}'.format(driver.matchedRider.id, dir_diff))            
            diff = abs(angle - opp_mid_driver_pref)/(360 - angle_threshold)
            if random.random() < diff:
                return False
            else:
                return True
    else:
        if ((DL_angle > driver.prefered_dir) and (DL_angle < (driver.prefered_dir + angle_threshold))):
            print('Rider {} pick up location in preferred direction'.format(driver.matchedRider.id))
            return False
        else:
            dir_diff = min(abs(driver.prefered_dir - DL_angle), abs(driver.prefered_dir + angle_threshold - DL_angle))
            print('Rider {} pick up location NOT in preferred direction; difference {}'.format(driver.matchedRider.id, dir_diff))
            diff = abs(angle - opp_mid_driver_pref)/(360 - angle_threshold)
            if random.random() < diff:
                return False
            else:
                return True

# This function analyses active drivers and riders around rider's pick up location and returns surge factor. Surge factor
# is equal to ( number of ride requests in a region / number of drivers waiting for ride requests in the region)

def calculate_surge(rider, real_loc):
    active_req = 0
    active_drivers = 0

    rider_db = rider.server.database.riders
    driver_db = rider.server.database.drivers
    '''
    Commented piece of code finds the region of rider and caluculates surge in the region
    if real_loc or rider.real_loc_req:
                    rider_region = rider_db.distinct("region",{"userID":rider.id})[0]
                else:
                    try:
                        location = rider.obfuscatedReqeustLocation
                        region_row = int(rider.server.regions * ((location[0] - rider.server.regionLat1)/(rider.server.regionLat2-rider.server.regionLat1)))
                        region_col = int(rider.server.regions * ((location[1] - rider.server.regionLon1)/(rider.server.regionLon2-rider.server.regionLon1)))
                        rider_region = (rider.server.regions * region_col) + region_row
                    except:
                        print('***** Exception occured ***** {} {} {}'.format(location, rider.matchedDriver.id, rider.id))
                print('Rider {} region is {}'.format(driver.matchedRider.id, rider_region))

    region_riders = list(rider_db.distinct("userID",{"region":rider_region})) 
    region_drivers = list(driver_db.distinct("userID",{"region":rider_region}))'''

    if real_loc or rider.real_loc_req:
        region_riders = list(rider.server.database.riders.find({"locations":{"$near":{"$geometry":{"type": "Point", "coordinates":rider.rideRequestLocation},"$maxDistance":2000}}}))
        region_drivers = list(rider.server.database.drivers.find({"locations":{"$near":{"$geometry":{"type": "Point", "coordinates":rider.rideRequestLocation},"$maxDistance":2000}}}))
    else:
        region_riders = list(rider.server.database.riders.find({"location_obf":{"$near":{"$geometry":{"type": "Point", "coordinates":rider.obfuscatedReqeustLocation},"$maxDistance":2000}}}))
        region_drivers = list(rider.server.database.drivers.find({"locations":{"$near":{"$geometry":{"type": "Point", "coordinates":rider.obfuscatedReqeustLocation},"$maxDistance":2000}}}))

    # print(region_drivers[0].get('userID'))
    for i in range(len(region_drivers)):
        if rider.server.driverObjects[region_drivers[i].get('userID')].state == WAITING_FOR_RIDE_REQ:
            active_drivers += 1
        else:
            continue

    for i in range(len(region_riders)):
        if rider.server.riderObjects[region_riders[i].get('userID')].state == LOOKING_FOR_DRIVER or rider.server.riderObjects[region_riders[i].get('userID')].state == WAITING_FOR_DRIVER_ACCEPTANCE:
            active_req += 1
        else:
            continue

    surge_factor = (active_req/active_drivers) if active_drivers != 0 else -1
    surge_factor = surge_factor if surge_factor > 1 or surge_factor == -1 else 1

    return surge_factor

# This function analyses the perceived ETA of driver for real/obfuscated locations and decides whether to serve or not based on hard threshold

def decision_hard_thresh(driver, env):
    location = list(driver.server.database.drivers.distinct("locations",{"userID":driver.id}))
    driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
    in_spl_zone=check_driver_loc(driverLocation)
    eta_t = 15*driver.tolerance if (not driver.uniform_eta and in_spl_zone) else driver.tolerance

    eta_tolerance = eta_t if (driver.req_refusal_count <= 2) else (driver.tolerance + 50*(driver.req_refusal_count - 2))
    # print('First decision ETA tolerance {} of Driver {}'.format(eta_tolerance, driver.id))
    if driver.matchedRider.real_loc_req:
        # print('Real location: Driver {} received request from Rider {}'.format(driver.id, driver.matchedRider.id))
        if(driver.matchedRider.driver_eta > eta_tolerance):
            print('Real Location: Rider {} request rejected by Driver {} sending request to next available driver'.format(driver.matchedRider.id, driver.id))
            driver.real_send_request_to_next_driver(env)
            return False
        else:
            # print('Real Location: Rider {} request accepted by Driver {} at time {}; {}'.format(driver.matchedRider.id, driver.id, env.now, driver.matchedRider.obf_loc_processing_start))
            driver.matchedRider.real_accept_eta = driver.matchedRider.driver_eta
            return True
    else:
        # print('Obfuscated location: Driver {} received request from Rider {}, {}'.format(driver.id, driver.matchedRider.id, driver.matchedRider.obf_loc_processing_start))
        driver.perceived_eta = driver.calculate_obf_loc_eta()
        if(driver.perceived_eta > eta_tolerance):
            if(driver.matchedRider.driver_eta < eta_tolerance):
                print('Driver {} did not accept request of Rider {} due to obfsucated location; increasing numOfExtraTrials'.format(driver.id, driver.matchedRider.id))
                driver.matchedRider.numOfExtraTrials += 1
            else:
                pass
            # print('Obfuscated Location: Rider {} request rejected sending request to next available driver'.format(driver.matchedRider.id))
            driver.obf_send_request_to_next_driver(env)
            # Relocate the driver by adding small noise to her current location
            # driver.relocate()
            return False
        else:
            if second_decision_driver(driver, env):
                # print('Obfuscated location: Driver {}: Accepted Rider {}'.format(driver.id, driver.matchedRider.id))
                return True
            else:
                return False

# This function analyses the perceived ETA of driver for real/obfuscated locations and decides whether to serve or not based on exponential threshold

def decision_exp_thresh(driver, env):
    location = list(driver.server.database.drivers.distinct("locations",{"userID":driver.id}))
    driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
    in_spl_zone=check_driver_loc(driverLocation)
    eta_t = 15*driver.tolerance if (not driver.uniform_eta and in_spl_zone) else driver.tolerance

    eta_tolerance = eta_t if (driver.req_refusal_count <= 2) else (driver.tolerance + 50*(driver.req_refusal_count - 2))
    # print('First decision ETA tolerance {} of Driver {}'.format(eta_tolerance, driver.id))
    if driver.matchedRider.real_loc_req:
        # print('Real location: Driver {} received request from Rider {}'.format(driver.id, driver.matchedRider.id))
        diff = eta_tolerance - driver.matchedRider.driver_eta

        if driver.matchedRider.driver_eta > eta_tolerance and random.random() < math.exp(diff/500):
            print('Real Location: Rider {} request rejected by Driver {} sending request to next available driver'.format(driver.matchedRider.id, driver.id))
            driver.real_send_request_to_next_driver(env)
            return False
        else:
            # print('Real Location: Rider {} request accepted by Driver {} at time {}'.format(driver.matchedRider.id, driver.id, env.now))
            driver.matchedRider.real_accept_eta = driver.matchedRider.driver_eta
            return True
    else:
        # print('Obfuscated location: Driver {} received request from Rider {}'.format(driver.id, driver.matchedRider.id))
        driver.perceived_eta = driver.calculate_obf_loc_eta()
        diff = eta_tolerance - driver.perceived_eta
        if driver.perceived_eta > eta_tolerance and random.random() < math.exp(diff/500):
            if(driver.matchedRider.driver_eta < eta_tolerance):
                print('Driver {} did not accept request of Rider {} due to obfsucated location; increasing numOfExtraTrials'.format(driver.id, driver.matchedRider.id))
                driver.matchedRider.numOfExtraTrials += 1
            else:
                pass
            # print('Obfuscated Location: Rider {} request rejected sending request to next available driver'.format(driver.matchedRider.id))
            driver.obf_send_request_to_next_driver(env)
            # Relocate the driver by adding small noise to her current location
            # driver.relocate()
            return False
        else:
            if second_decision_driver(driver, env):
                # print('Obfuscated location: Driver {}: Accepted Rider {}'.format(driver.id, driver.matchedRider.id))
                return True
            else:
                return False

# This function accepts rides based on logarithmic probability

def decision_log_thresh(driver, env):
    location = list(driver.server.database.drivers.distinct("locations",{"userID":driver.id}))
    driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
    in_spl_zone=check_driver_loc(driverLocation)
    eta_t = 15*driver.tolerance if (not driver.uniform_eta and in_spl_zone) else driver.tolerance

    eta_tolerance = eta_t if (driver.req_refusal_count <= 2) else (driver.tolerance + 50*(driver.req_refusal_count - 2))
    # print('First decision ETA tolerance {} of Driver {}'.format(eta_tolerance, driver.id))
    if driver.matchedRider.real_loc_req:
        # print('Real location: Driver {} received request from Rider {}'.format(driver.id, driver.matchedRider.id))
        diff = eta_tolerance - driver.matchedRider.driver_eta #if driver.matchedRider.driver_eta > eta_tolerance else 0
        # if driver.matchedRider.driver_eta > eta_tolerance and random.random() < (1 - math.log((2 - math.exp(diff)), 2)):
        if driver.matchedRider.driver_eta > eta_tolerance and random.random() < math.exp(diff/10):
            print('Real Location: Rider {} request rejected by Driver {} sending request to next available driver'.format(driver.matchedRider.id, driver.id))
            driver.real_send_request_to_next_driver(env)
            return False
        else:
            # print('Real Location: Rider {} request accepted by Driver {} at time {}'.format(driver.matchedRider.id, driver.id, env.now))
            driver.matchedRider.real_accept_eta = driver.matchedRider.driver_eta
            return True
    else:
        # print('Obfuscated location: Driver {} received request from Rider {}'.format(driver.id, driver.matchedRider.id))
        driver.perceived_eta = driver.calculate_obf_loc_eta()
        diff = eta_tolerance - driver.perceived_eta #if #driver.perceived_eta > eta_tolerance else 0
        if driver.perceived_eta > eta_tolerance and random.random() < math.exp(diff/10):
            if(driver.matchedRider.driver_eta < eta_tolerance):
                print('Driver {} did not accept request of Rider {} due to obfsucated location; increasing numOfExtraTrials'.format(driver.id, driver.matchedRider.id))
                driver.matchedRider.numOfExtraTrials += 1
            else:
                pass
            # print('Obfuscated Location: Rider {} request rejected sending request to next available driver'.format(driver.matchedRider.id))
            driver.obf_send_request_to_next_driver(env)
            # Relocate the driver by adding small noise to her current location
            # driver.relocate()
            return False
        else:
            if second_decision_driver(driver, env):
                # print('Obfuscated location: Driver {}: Accepted Rider {}'.format(driver.id, driver.matchedRider.id))
                return True
            else:
                return False

# This function analyses the perceived ETA of driver for real/obfuscated locations and decides whether to serve or not based on direction of the 
# perceived location with respect to driver's own location.

def decision_dir_thresh(driver, env):
    location = list(driver.server.database.drivers.distinct("locations",{"userID":driver.id}))
    driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
    in_spl_zone=check_driver_loc(driverLocation)
    eta_t = 15*driver.tolerance if (not driver.uniform_eta and in_spl_zone) else driver.tolerance

    eta_tolerance = eta_t if (driver.req_refusal_count <= 2) else (driver.tolerance + 50*(driver.req_refusal_count - 2))
    print('First decision ETA tolerance {} of Driver {}'.format(eta_tolerance, driver.id))
    if driver.matchedRider.real_loc_req:
        print('Real location: Driver {} received request from Rider {}'.format(driver.id, driver.matchedRider.id))
        diff = driver.matchedRider.driver_eta - driver.tolerance
        if driver.matchedRider.driver_eta > driver.tolerance and not direction(driver, driver.matchedRider.rideRequestLocation):
            # print('Real Location: Rider {} request rejected sending request to next available driver'.format(driver.matchedRider.id))
            driver.real_send_request_to_next_driver(env)
            return False
        else:
            print('Real Location: Rider {} request accepted by Driver {} at time {}'.format(driver.matchedRider.id, driver.id, env.now))
            driver.matchedRider.real_accept_eta = driver.matchedRider.driver_eta
            return True
    else:
        print('Obfuscated location: Driver {} received request from Rider {}'.format(driver.id, driver.matchedRider.id))
        driver.perceived_eta = driver.calculate_obf_loc_eta()
        diff = driver.perceived_eta - driver.tolerance
        if driver.perceived_eta > driver.tolerance and not direction(driver.matchedRider.obfuscatedReqeustLocation):
            if(driver.matchedRider.driver_eta < driver.tolerance):
                print('Driver {} did not accept request due to obfsucated location; increasing numOfExtraTrials'.format(driver.id))
                driver.matchedRider.numOfExtraTrials += 1
            else:
                pass
            # print('Obfuscated Location: Rider {} request rejected sending request to next available driver'.format(driver.matchedRider.id))
            driver.obf_send_request_to_next_driver(env)
            # Relocate the driver by adding small noise to her current location
            driver.relocate()
            return False
        else:
            if second_decision_driver(driver, env):
                print('Obfuscated location: Driver {}: Accepted Rider {}'.format(driver.id, driver.matchedRider.id))
                return True
            else:
                return False

def decision_driver(driver, env, real_loc_req):
    surge_factor = calculate_surge(driver.matchedRider, real_loc_req)
    driver.surge_factor = surge_factor
    
    # location = list(driver.server.database.drivers.distinct("locations",{"userID":driver.id}))
    # driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
    # in_spl_zone=check_driver_loc(driverLocation)
    # eta_t = 15*driver.tolerance if (not driver.uniform_eta and in_spl_zone) else driver.tolerance
    # if in_spl_zone and not driver.uniform_dm:
    #     driver.dd_surge_neg='log'
    #     driver.dd_surge_more_than_one='log'
    #     driver.dd_surge_less_than_one='log'
    # else:
    #     driver.dd_surge_neg='hard'
    #     driver.dd_surge_more_than_one='hard'
    #     driver.dd_surge_less_than_one='hard'

    if surge_factor == -1:
        # No drivers in the rider's region => HIGH priority request - LOG
        if driver.dd_surge_neg == 'exp':
            return decision_exp_thresh(driver, env)
        elif driver.dd_surge_neg == 'log':
            return decision_log_thresh(driver, env)
        elif driver.dd_surge_neg == 'hard':
            return decision_hard_thresh(driver, env)

    elif surge_factor > 1:
        # More requests than number of drivers in rider's region => MEDIUM priority - EXP
        if driver.dd_surge_more_than_one == 'exp':
            return decision_exp_thresh(driver, env)
        elif driver.dd_surge_more_than_one == 'log':
            return decision_log_thresh(driver, env)
        elif driver.dd_surge_more_than_one == 'hard':
            return decision_hard_thresh(driver, env)

    else:
        # More drivers than number of requests in rider's region => LOW priority - HARD
        if driver.dd_surge_less_than_one == 'exp':
            return decision_exp_thresh(driver, env)
        elif driver.dd_surge_less_than_one == 'log':
            return decision_log_thresh(driver, env)
        elif driver.dd_surge_less_than_one == 'hard':
            return decision_hard_thresh(driver, env)

def second_decision_driver(driver, env):
    # surge_factor = calculate_surge(driver.matchedRider, False)
    # driver.surge_factor = surge_factor
    
    # location = list(driver.server.database.drivers.distinct("locations",{"userID":driver.id}))
    # driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
    # in_spl_zone=check_driver_loc(driverLocation)
    # eta_t = 15*driver.tolerance if (not driver.uniform_eta and in_spl_zone) else driver.tolerance
    # if in_spl_zone and not driver.uniform_dm:
    #     driver.dd_surge_neg='log'
    #     driver.dd_surge_more_than_one='log'
    #     driver.dd_surge_less_than_one='log'
    # else:
    #     driver.dd_surge_neg='hard'
    #     driver.dd_surge_more_than_one='hard'
    #     driver.dd_surge_less_than_one='hard'

    if driver.surge_factor == -1:
        # No drivers in the rider's region => HIGH priority request - LOG
        if driver.dd_surge_neg == 'exp':
            return driver.obf_location_decision_exp_threshold(env)
        elif driver.dd_surge_neg == 'log':
            return driver.obf_location_decision_log_threshold(env)
        elif driver.dd_surge_neg == 'hard':
            return driver.obf_location_decision_hard_threshold(env)

    elif driver.surge_factor > 1:
        # More requests than number of drivers in rider's region => MEDIUM priority - EXP
        if driver.dd_surge_more_than_one == 'exp':
            return driver.obf_location_decision_exp_threshold(env)
        elif driver.dd_surge_more_than_one == 'log':
            return driver.obf_location_decision_log_threshold(env)
        elif driver.dd_surge_more_than_one == 'hard':
            return driver.obf_location_decision_hard_threshold(env)

    else:
        # More drivers than number of requests in rider's region => LOW priority - HARD
        if driver.dd_surge_less_than_one == 'exp':
            return driver.obf_location_decision_exp_threshold(env)
        elif driver.dd_surge_less_than_one == 'log':
            return driver.obf_location_decision_log_threshold(env)
        elif driver.dd_surge_less_than_one == 'hard':
            return driver.obf_location_decision_hard_threshold(env)
