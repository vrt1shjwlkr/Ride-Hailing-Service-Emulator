from __future__ import division
import simpy, os, datetime, random, simplejson, urllib, logging, math, sys
from pymongo import MongoClient
from driver_decision import *
from distance_apis import *
from lppm import *
from lppmConstantNoise import *
from rhse_util import *
from globalvars import *

'''
This class imitates driver behaviours by implementing relevant functions.
'''

class Driver:
    def __init__(self, driverID, server, debug_, eta_tolerance, dd_surge_neg, dd_surge_less_than_one, dd_surge_more_than_one, gen_utility, mech_name, privacy_level,z_qlg, g_res,uniform_eta,uniform_dm,uniform):
        self.server=server
        self.debug_=debug_
        self.id=driverID
        self.state = WAITING_FOR_RIDE_REQ
        self.matchedRider = None
        self.rideDestination = None
        self.gen_utility = gen_utility
        self.prefered_dir = random.randint(-180, 180)
        self.tolerance = eta_tolerance
        self.dir_tolerance = 180
        self.dd_surge_neg = dd_surge_neg
        self.dd_surge_less_than_one = dd_surge_less_than_one
        self.dd_surge_more_than_one = dd_surge_more_than_one
        self.blocked = False
        self.block_clock = 0
        self.mech_name = mech_name
        self.privacy_level = privacy_level
        self.req_refusal_count = 0
        self.surge_factor = None
        self.z_qlg=z_qlg
        self.g_res=g_res
        self.uniform=uniform # used for greedy remapping and nonuniform distribution cases
        self.uniform_eta=uniform_eta
        self.uniform_dm=uniform_dm
        # Utility parameters
        self.ridePickupLocation = None
        self.perceived_eta = None
        self.real_num_ride_req = 0
        self.real_acc_rides = 0
        self.real_acc_rate = None
        self.real_earnings = []

        self.obfuscaedRidePickupLocation = None
        self.obf_num_ride_req = 0
        self.obf_acc_rides = 0
        self.obf_acc_rate = None
        self.reject_accepted_ride = 0
        self.obf_earnings = []

    def cal_earning(self, real_loc_req, rideRequestLocation, rideDestination, driver_eta):
        surge = self.surge_factor if self.surge_factor > 1 else 1
        if real_loc_req:
            # calculating utility of the ride for real locations
            location = list(self.server.database.drivers.distinct("locations",{"userID":self.id}))
            driverLocation_lat = location[0].get("coordinates")[0]
            driverLocation_lon = location[0].get("coordinates")[1]

            AL_PUL = driver_eta
            PUL_DSTN = osrm_distance(rideRequestLocation, rideDestination)
            fare = base_fare + (fare_per_sec*PUL_DSTN*surge)

            earning = fare if fare >= min_fare else min_fare
            earning = earning - (AL_PUL*fuel_cost)
            self.real_earnings.append(earning)
        else:
            # calculating utility of the ride for obfuscated locations
            location = list(self.server.database.drivers.distinct("locations",{"userID":self.id}))
            driverLocation_lat = location[0].get("coordinates")[0]
            driverLocation_lon = location[0].get("coordinates")[1]
            AL_PUL = driver_eta
            PUL_DSTN = osrm_distance(rideRequestLocation, rideDestination)
            fare = base_fare + (fare_per_sec*PUL_DSTN*surge)

            earning = fare if fare >= min_fare else min_fare
            earning = earning - (AL_PUL*fuel_cost)
            self.obf_earnings.append(earning)

    '''
    This function does processing post real request acceptance by driver.
    '''

    def real_req_accpeted(self, env):
        # Rider utility
        self.matchedRider.real_loc_req_accept_time = (env.now + 1)
        try:
            self.matchedRider.real_ride_start_time = (((self.matchedRider.real_loc_req_accept_time - self.matchedRider.first_req_time) * self.matchedRider.req_delay) + self.matchedRider.driver_eta) + self.matchedRider.real_num_of_trials*300
        except:
            print('***** Exception occured ***** concerned param values are {} {} {} {} {}'.format(self.matchedRider.id, self.matchedRider.real_loc_req_accept_time, self.matchedRider.first_req_time, self.matchedRider.req_delay, self.matchedRider.driver_eta))

        self.matchedRider.real_loc_accepted_driver = self.id
        self.matchedRider.real_last_match_distance = SEARCH_RAD
        self.matchedRider.real_location_drivers = None
        self.matchedRider.state = LOOKING_FOR_DRIVER
        if self.matchedRider.obf_ride_start_time:
            rhs_util = self.matchedRider.obf_ride_start_time - self.matchedRider.real_ride_start_time
            # Log the ride details wrt rider
            ride_details = [self.matchedRider.num_of_trials]
            ride_details.append(self.matchedRider.numOfExtraTrials)
            ride_details.append(self.matchedRider.real_num_of_trials)
            ride_details.append(1)
            ride_details.append(1)
            ride_details.append(self.matchedRider.first_req_time)
            ride_details.append(self.matchedRider.obf_loc_req_accept_time)
            ride_details.append(self.matchedRider.obf_ride_start_time)
            ride_details.append(self.matchedRider.real_loc_req_accept_time)
            ride_details.append(self.matchedRider.real_ride_start_time)
            ride_details.append(1000 * self.matchedRider.gen_utility)
            ride_details.append(rhs_util)
            ride_details.append(self.matchedRider.num_real_loc_drivers)
            ride_details.append(self.matchedRider.avg_etas_real_loc_drivers)
            ride_details.append(self.matchedRider.avg_real_acc_rate)
            ride_details.append(self.matchedRider.avg_real_surge)
            ride_details.append(self.matchedRider.num_obf_loc_drivers)
            ride_details.append(self.matchedRider.avg_etas_obf_loc_drivers)
            ride_details.append(self.matchedRider.avg_obf_acc_rate)
            ride_details.append(self.matchedRider.avg_obf_surge)
            ride_details.append(self.matchedRider.obf_real_eta)
            ride_details.append(self.matchedRider.privacy_level)
            ride_details.append(self.matchedRider.min_eta_real_loc_drivers)
            ride_details.append(self.matchedRider.min_eta_obf_loc_drivers)
            ride_details.append(self.matchedRider.real_accept_eta_tolerance)
            ride_details.append(self.matchedRider.obf_accept_eta_tolerance)
            ride_details.append(self.matchedRider.real_accept_eta)
            ride_details.append(self.matchedRider.obf_accept_eta)
            ride_details.append(self.matchedRider.euclidean_dist)
            expected_gen_ql=((math.log(self.matchedRider.privacy_level)/(self.matchedRider.gen_utility*1000))**2)*(math.exp(-math.log(self.matchedRider.privacy_level)*self.matchedRider.euclidean_dist/(self.matchedRider.gen_utility*1000)))*self.matchedRider.euclidean_dist
            expected_tai_ql=((math.log(self.matchedRider.privacy_level)/(self.matchedRider.gen_utility*1000))**2)*(math.exp(-math.log(self.matchedRider.privacy_level)*self.matchedRider.euclidean_dist/(self.matchedRider.gen_utility*1000)))*(rhs_util)
            ride_details.append(expected_gen_ql)
            ride_details.append(expected_tai_ql)
            self.matchedRider.rideDetails.append(ride_details)

            self.matchedRider.real_accept_eta_tolerance = None
            self.matchedRider.obf_accept_eta_tolerance = None
            print('Rider {} Real location: Time to start ride {}; Obfuscated location: Time to start ride {}'.format(self.matchedRider.id, self.matchedRider.real_ride_start_time, self.matchedRider.obf_ride_start_time))
        else:
            if self.debug_=='HIGH':
                print('Rider {} Real location: Time to start ride {}; Obfuscated location: Yet to process'.format(self.matchedRider.id, self.matchedRider.real_ride_start_time))

        self.matchedRider.real_loc_req = False
        self.matchedRider = None
 
    '''
    This function does processing post obfuscated location request acceptance by driver.
    '''

    def obf_req_accepted(self, env):
        self.matchedRider.obf_loc_req_accept_time = (env.now + 1)
        # self.blocked = True
        # self.block_clock = 1+int(self.matchedRider.obf_accept_eta/100)

        try:
            self.matchedRider.obf_ride_start_time = (((self.matchedRider.obf_loc_req_accept_time - self.matchedRider.obf_loc_processing_start) * self.matchedRider.req_delay) + self.matchedRider.driver_eta) + self.matchedRider.num_of_trials*300
        except:
            print('***** Exception occured ***** concerned param values are {} {} {} {} {}'.format(self.matchedRider.id, self.matchedRider.obf_loc_req_accept_time, self.matchedRider.obf_loc_processing_start, self.matchedRider.req_delay, self.matchedRider.driver_eta))

        self.matchedRider.obf_loc_accepted_driver = self.id
        self.matchedRider.obf_last_match_distance = SEARCH_RAD
        self.matchedRider.obf_location_drivers = None
        avg_real_dist_from_drivers = 0
        avg_obf_dist_from_drivers = 0
        if self.matchedRider.real_ride_start_time:
            rhs_util = self.matchedRider.obf_ride_start_time - self.matchedRider.real_ride_start_time
            # Log the ride details wrt rider
            ride_details = [self.matchedRider.num_of_trials]
            ride_details.append(self.matchedRider.numOfExtraTrials)
            ride_details.append(self.matchedRider.real_num_of_trials)
            ride_details.append(1)
            ride_details.append(1)
            ride_details.append(self.matchedRider.first_req_time)
            ride_details.append(self.matchedRider.obf_loc_req_accept_time)
            ride_details.append(self.matchedRider.obf_ride_start_time)
            ride_details.append(self.matchedRider.real_loc_req_accept_time)
            ride_details.append(self.matchedRider.real_ride_start_time)
            ride_details.append(1000 * self.matchedRider.gen_utility)
            ride_details.append(rhs_util)
            ride_details.append(self.matchedRider.num_real_loc_drivers)
            ride_details.append(self.matchedRider.avg_etas_real_loc_drivers)
            ride_details.append(self.matchedRider.avg_real_acc_rate)
            ride_details.append(self.matchedRider.avg_real_surge)
            ride_details.append(self.matchedRider.num_obf_loc_drivers)
            ride_details.append(self.matchedRider.avg_etas_obf_loc_drivers)
            ride_details.append(self.matchedRider.avg_obf_acc_rate)
            ride_details.append(self.matchedRider.avg_obf_surge)
            ride_details.append(self.matchedRider.obf_real_eta)
            ride_details.append(self.matchedRider.privacy_level)
            ride_details.append(self.matchedRider.min_eta_real_loc_drivers)
            ride_details.append(self.matchedRider.min_eta_obf_loc_drivers)
            ride_details.append(self.matchedRider.real_accept_eta_tolerance)
            ride_details.append(self.matchedRider.obf_accept_eta_tolerance)
            ride_details.append(self.matchedRider.real_accept_eta)
            ride_details.append(self.matchedRider.obf_accept_eta)
            ride_details.append(self.matchedRider.euclidean_dist)
            expected_gen_ql=((math.log(self.matchedRider.privacy_level)/(self.matchedRider.gen_utility*1000))**2)*math.exp(-math.log(self.matchedRider.privacy_level)*self.matchedRider.euclidean_dist/(self.matchedRider.gen_utility*1000))*self.matchedRider.euclidean_dist
            expected_tai_ql=((math.log(self.matchedRider.privacy_level)/(self.matchedRider.gen_utility*1000))**2)*math.exp(-math.log(self.matchedRider.privacy_level)*self.matchedRider.euclidean_dist/(self.matchedRider.gen_utility*1000))*rhs_util
            ride_details.append(expected_gen_ql)
            ride_details.append(expected_tai_ql)
            self.matchedRider.rideDetails.append(ride_details)

            self.matchedRider.real_accept_eta_tolerance = None
            self.matchedRider.obf_accept_eta_tolerance = None
            print('Rider {} Real location: Time to start ride {}; Obfuscated location: Time to start ride - {}'.format(self.matchedRider.id, self.matchedRider.real_ride_start_time, self.matchedRider.obf_ride_start_time))
        else:
            pass
        self.state = RIDE_REQ_ACCEPTED

    '''
    This function will relocate driver in case if she doesn't accept the ride request.
    '''

    def relocate(self):
        self.prefered_dir = random.randint(-180, 180)
        location = list(self.server.database.drivers.distinct("locations",{"userID":self.id}))

        # Following code should be used when driver locations are not obfuscated
        [driverLocation_lat, driverLocation_lon]=obfuscate_loc('circular', [location[0].get("coordinates")[0], location[0].get("coordinates")[1]], 0.2, None, z_qlg=self.z_qlg)
        spl_zone_lat1=self.server.regionLat1
        spl_zone_lon1=self.server.regionLon1
        spl_zone_lat2=self.server.regionLat1+(self.server.regionLat2-self.server.regionLat1)/2
        spl_zone_lon2=self.server.regionLon1+(self.server.regionLon2-self.server.regionLon1)/2
        [driverLocation_lat, driverLocation_lon]=truncate_loc(spl_zone_lat1,spl_zone_lon1,spl_zone_lat2,spl_zone_lon2, [driverLocation_lat, driverLocation_lon])
        # [driverLocation_lat, driverLocation_lon]=truncate_loc(self.server.regionLat1, self.server.regionLon1, self.server.regionLat2, self.server.regionLon2, [driverLocation_lat, driverLocation_lon])

        while check_validity(self.server, [driverLocation_lat, driverLocation_lon]) == False:
            [driverLocation_lat, driverLocation_lon] = obfuscate_loc('circular', [location[0].get("coordinates")[0], location[0].get("coordinates")[1]], 0.2, None, z_qlg=self.z_qlg)

        if self.debug_=='HIGH':
            print('Relocating Driver {} to {} {}'.format(self.id, driverLocation_lat, driverLocation_lon))
        region_row = int(self.server.regions * ((driverLocation_lat - self.server.regionLat1)/(self.server.regionLat2-self.server.regionLat1)))
        region_col = int(self.server.regions * ((driverLocation_lon - self.server.regionLon1)/(self.server.regionLon2-self.server.regionLon1)))
        region = (self.server.regions * region_col) + region_row
        
        dbDrivers = self.server.database.drivers
        dbDrivers.update(
            {"userID":self.id},
            {
                "userID":self.id,
                "userType":"driver",
                "region":region,
                "locations":{
                    "type":"Point",
                    "coordinates":[driverLocation_lat, driverLocation_lon]
                }
            }
        )
        '''
        # Following code should be used when driver locations are also obfuscated
        [driverLocation_lat, driverLocation_lon] = obfuscate_loc('circular', [location[0].get("coordinates")[0], location[0].get("coordinates")[1]], 0.2, None)
        [driverLocation_lat_obf, driverLocation_lon_obf] = obfuscate_loc(self.mech_name, [driverLocation_lat, driverLocation_lon], self.gen_utility, self.privacy_level)
        while check_validity(self.server, [driverLocation_lat_obf, driverLocation_lon_obf]) == False:
            [driverLocation_lat_obf, driverLocation_lon_obf] = obfuscate_loc(self.mech_name, [driverLocation_lat, driverLocation_lon], self.gen_utility, self.privacy_level)
        region_row_obf = int(self.server.regions * ((driverLocation_lat_obf - self.server.regionLat1)/(self.server.regionLat2-self.server.regionLat1)))
        region_col_obf = int(self.server.regions * ((driverLocation_lon_obf - self.server.regionLon1)/(self.server.regionLon2-self.server.regionLon1)))
        region_obf = (self.server.regions * region_col_obf) + region_row_obf

        dbDrivers = self.server.database.drivers
        dbDrivers.update(
            {"userID":self.id},
            {
                "userID":self.id,
                "userType":"driver",
                "region":region,
                "locations":{
                    "type":"Point",
                    "coordinates":[driverLocation_lat, driverLocation_lon]
                },
                "region_obf":region_obf,
                "location_obf":{
                    "type":"Point",
                    "coordinates":[driverLocation_lat_obf, driverLocation_lon_obf]
                }
            }
        )
        '''
    '''
    This function calculates ETA for obfuscated location that a driver sees when she receives the request for the first time.
    '''

    def calculate_obf_loc_eta(self):
        location = list(self.server.database.drivers.distinct("locations",{"userID":self.id}))
        driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
        etas, distances = distance_api(self.matchedRider.obfuscatedReqeustLocation, [driverLocation])
        if self.debug_=='HIGH':
            print('Driver {} Rider {} perceived_eta is {}'.format(self.id, self.matchedRider.id, etas[0]))
        return etas[0]

    '''
    If current driver rejects ride request, this function sends requst to next driver in the list of drivers around real location.
    '''

    def real_send_request_to_next_driver(self, env):
        if self.debug_=='HIGH':
            print('real_send_request_to_next_driver time now {}'.format(env.now))
        while self.matchedRider.real_location_drivers:
            next_driver_id = self.matchedRider.real_location_drivers[0][0]
            if not self.server.driverObjects[next_driver_id].blocked and not self.server.driverObjects[next_driver_id].matchedRider:
                # send rider to a driver as a matched_rider
                # print('Real location: Rider {} sending request to next Driver {} with ETA {}'.format(self.matchedRider.id, next_driver_id, self.matchedRider.real_location_drivers[0][1]))
                self.matchedRider.matchedDriver = self.server.driverObjects[next_driver_id]
                self.matchedRider.driver_eta = self.matchedRider.real_location_drivers[0][1]
                self.server.driverObjects[next_driver_id].matchedRider = self.matchedRider
                self.matchedRider.real_location_drivers.pop(0)
                self.matchedRider = None
                break
            else:
                # print('Real Location: Rider {} - Driver {} serving already, trying next available Driver'.format(self.matchedRider.id, self.matchedRider.real_location_drivers[0][0]))
                self.matchedRider.real_location_drivers.pop(0)
        
        if self.matchedRider:
            # print('Real Location: Rider {} - No more drivers in available list, sending request to server'.format(self.matchedRider.id))
            self.matchedRider.state = LOOKING_FOR_DRIVER_WAITING
            self.matchedRider.driver_eta = None
            self.matchedRider.retry_timer = env.now + 3
            self.matchedRider.service_active = False
            self.matchedRider.real_loc_req = False
            self.matchedRider.real_num_of_trials += 1
            # If all the drivers in the list of real location refused to serve, send the request again
            self.matchedRider.real_last_match_distance = SEARCH_RAD
            if self.matchedRider.id not in self.server.pendingRiders:
                self.server.pendingRiders.append(self.matchedRider.id)
            self.matchedRider.real_location_drivers = None
            self.matchedRider.matchedDriver = None
            self.matchedRider = None

    '''
    If current driver rejects ride request, this function sends requst to next driver in the list of drivers around obfuscated location
    '''

    def obf_send_request_to_next_driver(self, env):
        if self.debug_=='HIGH':
            print('obf_send_request_to_next_driver time now {}'.format(env.now))
        while self.matchedRider.obf_loc_drivers:
            next_driver_id = self.matchedRider.obf_loc_drivers[0][0]
            if not self.server.driverObjects[next_driver_id].blocked and not self.server.driverObjects[next_driver_id].matchedRider:
                # send request to next driver in the drivers' list of the rider
                print('Obfuscated location: Rider {} sending request to next Driver {} with ETA {}'.format(self.matchedRider.id, next_driver_id, self.matchedRider.obf_loc_drivers[0][1]))
                self.matchedRider.matchedDriver = self.server.driverObjects[next_driver_id]
                self.matchedRider.driver_eta = self.matchedRider.obf_loc_drivers[0][1]
                self.server.driverObjects[next_driver_id].matchedRider = self.matchedRider
                self.matchedRider.obf_loc_drivers.pop(0)
                self.matchedRider.state = WAITING_FOR_DRIVER_ACCEPTANCE
                self.matchedRider = None
                break
            else:
                print('Obfuscated location: Next Driver {} in list of Rider {} is no more available'.format(next_driver_id, self.matchedRider.id))
                self.matchedRider.obf_loc_drivers.pop(0)

        if self.matchedRider:
            print('Obfuscated location: No more drivers in the list of Rider {}, sending request to server'.format(self.matchedRider.id))
            self.matchedRider.state = LOOKING_FOR_DRIVER_WAITING
            self.matchedRider.driver_eta = None
            self.matchedRider.retry_timer = env.now + 3
            self.matchedRider.service_active = False
            self.matchedRider.num_of_trials += 1
            # If all the drivers in the list of obf location refused to serve, send the request again
            self.matchedRider.obf_last_match_distance = SEARCH_RAD
            if self.matchedRider.id not in self.server.pendingRiders:
                self.server.pendingRiders.append(self.matchedRider.id)
            self.matchedRider.obf_loc_drivers = None
            self.matchedRider.matchedDriver = None
            self.matchedRider = None

    '''
    For obfuscared location, if a driver accepts the request, this function acts as a check on the real location of ride request by driver.
    The function checks if real location is within the tolerance of driver if yes she accepts the request.
    '''

    def obf_location_decision_hard_threshold(self, env):
        location = list(self.server.database.drivers.distinct("locations",{"userID":self.id}))
        driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
        in_spl_zone=check_driver_loc(driverLocation)
        eta_t = 15*self.tolerance if (not self.uniform_eta and in_spl_zone) else self.tolerance

        eta_tolerance = eta_t if (self.req_refusal_count <= 2) else (self.tolerance + 50*(self.req_refusal_count - 2))
        # At this point rider's real location will be disclosed to the driver if the real location ETA > 10 driver will cancel the request with some prob
        if self.debug_=='HIGH':
            print('obf_location_decision_hard_threshold time now {}'.format(env.now))
        if self.matchedRider.driver_eta > eta_tolerance:
            if self.debug_=='HIGH':
                print("Rider {} utility loss due to location obfuscation; increasing numOfExtraTrials".format(self.matchedRider.id))
            self.reject_accepted_ride += 1
            self.matchedRider.numOfExtraTrials += 1
            self.obf_send_request_to_next_driver(env)
            return False
        else:
            if self.debug_=='HIGH':
                print("Driver {} accepted request of Rider {} inspite of misleading location".format(self.id, self.matchedRider.id))
            self.matchedRider.obf_accept_eta = self.matchedRider.driver_eta
            self.matchedRider.waiting_for_driver()
            return True

    '''
    For obfuscared location, if a driver accepts the request, this function acts as a second check by driver on the real location of ride request.
    The function checks if real location is within the tolerance of driver if YES she accepts the request; if NO driver accepts requests based on
    exp(diff in eta and tolerance)
    '''

    def obf_location_decision_exp_threshold(self, env):
        location = list(self.server.database.drivers.distinct("locations",{"userID":self.id}))
        driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
        in_spl_zone=check_driver_loc(driverLocation)
        eta_t = 15*self.tolerance if (not self.uniform_eta and in_spl_zone) else self.tolerance

        eta_tolerance = eta_t if (self.req_refusal_count <= 2) else (self.tolerance + 50*(self.req_refusal_count - 2))
        # At this point rider's real location will be disclosed to the driver if the real location ETA > 10 driver will cancel the request with some prob
        diff = (eta_tolerance - self.matchedRider.driver_eta)
        if self.matchedRider.driver_eta > eta_tolerance and random.random() < math.exp(diff/500):
            if self.debug_=='HIGH':
                print("Rider {} utility loss due to location obfuscation; increasing numOfExtraTrials".format(self.matchedRider.id))
            self.reject_accepted_ride += 1
            self.matchedRider.numOfExtraTrials += 1
            self.obf_send_request_to_next_driver(env)
            return False
        else:
            if self.debug_=='HIGH':
                print("Driver {} accepted request of Rider {} inspite of misleading location".format(self.id, self.matchedRider.id))
            self.matchedRider.obf_accept_eta = self.matchedRider.driver_eta
            self.matchedRider.waiting_for_driver()
            return True

    '''
    For obfuscared location, if a driver accepts the request, this function acts as a second check by driver on the real location of ride request.
    The function checks if real location is within the tolerance of driver if YES she accepts the request; if NO driver accepts requests based on
    (diff in eta and tolerance/ tolerance)
    '''

    def obf_location_decision_lin_threshold(self, env):
        location = list(self.server.database.drivers.distinct("locations",{"userID":self.id}))
        driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
        in_spl_zone=check_driver_loc(driverLocation)
        eta_t = 15*self.tolerance if (not self.uniform_eta and in_spl_zone) else self.tolerance

        eta_tolerance = eta_t if (self.req_refusal_count <=2) else (self.tolerance + 50*(self.req_refusal_count - 2))
        # At this point rider's real location will be disclosed to the driver if the real location ETA > 10 driver will cancel the request with some prob
        diff = (eta_tolerance - self.matchedRider.driver_eta)
        if self.matchedRider.driver_eta > eta_tolerance and random.random() < (diff/eta_tolerance):
            if self.debug_=='HIGH':
                print("Rider {} utility loss due to location obfuscation; increasing numOfExtraTrials".format(self.matchedRider.id))
            self.reject_accepted_ride += 1
            self.matchedRider.numOfExtraTrials += 1
            self.obf_send_request_to_next_driver(env)
            return False
        else:
            if self.debug_=='HIGH':
                print("Driver {} accepted request of Rider {} inspite of misleading location".format(self.id, self.matchedRider.id))
            self.matchedRider.obf_accept_eta = self.matchedRider.driver_eta
            self.matchedRider.waiting_for_driver()
            return True

    '''
    For obfuscared location, if a driver accepts the request, this function acts as a second check by driver on the real location of ride request.
    The function checks if real location is within the tolerance of driver if YES she accepts the request; if NO driver accepts requests based on
    1 - log_2(2 - exp(diff in eta and tolerance/ tolerance))
    '''

    def obf_location_decision_log_threshold(self, env):
        location = list(self.server.database.drivers.distinct("locations",{"userID":self.id}))
        driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
        in_spl_zone=check_driver_loc(driverLocation)
        eta_t = 15*self.tolerance if (not self.uniform_eta and in_spl_zone) else self.tolerance

        eta_tolerance = eta_t if (self.req_refusal_count <= 2) else (self.tolerance + 50*(self.req_refusal_count - 2))
        # At this point rider's real location will be disclosed to the driver if the real location ETA > 10 driver will cancel the request with some prob
        # diff = (self.tolerance - self.matchedRider.driver_eta) if self.matchedRider.driver_eta > self.tolerance else 0
        diff = (eta_tolerance - self.matchedRider.driver_eta)
        # if self.matchedRider.driver_eta > self.tolerance and random.random() < (1 - math.log((2 - math.exp(diff)), 2)):
        if self.matchedRider.driver_eta > eta_tolerance and random.random() < math.exp(diff/10):
            if self.debug_=='HIGH':
                print("Rider {} utility loss due to location obfuscation; increasing numOfExtraTrials".format(self.matchedRider.id))
            self.reject_accepted_ride += 1
            self.matchedRider.numOfExtraTrials += 1
            self.obf_send_request_to_next_driver(env)
            return False
        else:
            if self.debug_=='HIGH':
                print("Driver {} accepted request of Rider {} inspite of misleading location".format(self.id, self.matchedRider.id))
            self.matchedRider.obf_accept_eta = self.matchedRider.driver_eta
            self.matchedRider.waiting_for_driver()
            return True

    '''
    When a driver accepts ride for obfuscated location based on two layered check as mentioned, this function will note the time to start ride and change the 
    state of rider to RIDING.
    '''

    def start_ride(self):
        # print("Obfuscated Location: Rider {} disclosing destination {} to Driver {}".format(self.matchedRider.id, self.matchedRider.rideDestination, self.id))
        self.matchedRider.disclose_destination(self)
        self.state = RIDING

    '''
    This function will end the ride for driver and rider and relocated them to new locations. The function also changes state of rider and driver as appropriate.
    '''
 
    def rate_rider(self):
        self.server.updateMongoDriver(self)
        print("Ending the ride of Rider {} & Driver {}".format(self.matchedRider.id, self.id))
        self.matchedRider = None
        self.ridePickupLocation = None
        self.rideDestination = None
        self.state = WAITING_FOR_RIDE_REQ

    def run(self, env):
        while True:
            if self.blocked:
                if self.matchedRider:
                    if self.matchedRider.real_loc_req:
                        if self.debug_=='HIGH':
                            print('Rider {} Real loc req; Driver {} is blocked send request to next driver'.format(self.matchedRider.id, self.id))
                        self.real_send_request_to_next_driver(env)
                    else:
                        if self.debug_=='HIGH':
                            print('Rider {} Obf loc req; Driver {} is blocked send request to next driver'.format(self.matchedRider.id, self.id))
                        self.obf_send_request_to_next_driver(env)

            elif self.state == WAITING_FOR_RIDE_REQ:
                if self.matchedRider:
                    rider_id = self.matchedRider.id
                    real_loc_req = self.matchedRider.real_loc_req
                    if real_loc_req:
                        rideRequestLocation = self.matchedRider.rideRequestLocation
                    else:
                        rideRequestLocation = self.matchedRider.obfuscatedReqeustLocation
                    rideDestination = self.matchedRider.rideDestination
                    driver_eta = self.matchedRider.driver_eta

                    if real_loc_req:
                        self.real_num_ride_req += 1
                    else:
                        self.obf_num_ride_req += 1

                    if decision_driver(self, env, real_loc_req):
                        self.cal_earning(real_loc_req, rideRequestLocation, rideDestination, driver_eta)
                        # the request got accepted by driver

                        if real_loc_req:
                            self.matchedRider.real_accept_eta_tolerance = self.tolerance if (self.req_refusal_count <= 2) else (self.tolerance + 50*(self.req_refusal_count - 2))
                            self.real_acc_rides += 1
                            self.real_acc_rate = self.real_acc_rides/self.real_num_ride_req
                            if self.debug_=='HIGH':
                                print('Driver {} real acc rate {}'.format(self.id, self.real_acc_rate))
                            self.real_req_accpeted(env)
                        else:
                            self.matchedRider.obf_accept_eta_tolerance = self.tolerance if (self.req_refusal_count <= 2) else (self.tolerance + 50*(self.req_refusal_count - 2))
                            self.obf_acc_rides += 1
                            self.obf_acc_rate = self.obf_acc_rides/self.obf_num_ride_req
                            if self.debug_=='HIGH':
                                print('Driver {} obf acc rate {}'.format(self.id, self.obf_acc_rate))
                            self.obf_req_accepted(env)

                        self.req_refusal_count = 0
                        print('Driver {} accepted Rider {}; resetting req_refusal_count to {}'.format(self.id, rider_id, self.req_refusal_count))
                    else:
                        # request got rejected
                        self.req_refusal_count += 1
                        print('Driver {} rejected Rider {}; increasing req_refusal_count to {}'.format(self.id, rider_id, self.req_refusal_count))
                        
                        if real_loc_req:
                            self.real_acc_rate = self.real_acc_rides/self.real_num_ride_req
                            if self.real_acc_rate < 0.8:
                                if self.debug_=='HIGH':
                                    print('real_loc: Driver {} acceptance rate {} => blocking for 5 simTime at {}'.format(self.id, self.real_acc_rate, env.now))
                                self.blocked = False
                                self.block_clock = 0
                        else:
                            self.obf_acc_rate = self.obf_acc_rides/self.obf_num_ride_req
                            if self.obf_acc_rate < 0.8:
                                if self.debug_=='HIGH':
                                    print('obf_loc: Driver {} acceptance rate {} => blocking for 5 simTime at {}'.format(self.id, self.obf_acc_rate, env.now))
                                self.blocked = False
                                self.block_clock = 0

                    yield env.timeout(1)
            
            elif self.state == RIDE_REQ_ACCEPTED:
                # print('Driver {}: Approaching pick up location to pick Rider {}'.format(self.id, self.matchedRider.id))
                # Here we should add random noise later to model driver delay
                self.start_ride()
            
            elif self.state == WAITING_FOR_RIDER_PICKUP:
                pass
                # print('Waiting for Rider {} at pick up point'.format(self.matchedRider.id))

            elif self.state == RIDING:
                self.rate_rider()

            yield env.timeout(1)