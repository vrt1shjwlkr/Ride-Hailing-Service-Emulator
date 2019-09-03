from __future__ import division
import numpy, simpy, sys, os, datetime, random, simplejson, urllib, logging
from globalvars import *
from pymongo import MongoClient
from lppmConstantNoise import *
from distance_apis import *
from lppm import *
from geopy.distance import vincenty
from globalvars import *

'''
Below, enter the geo-coordinates of the region in which you would like to generate RHS data
For example, following are the geo-coordinates of downtown area of Paris.
'''

lat1 = (48.810519)
lat2 = (48.901606)
lon1 = (2.275873)
lon2 = (2.421079)

'''
This class imitates rider behaviours by implementing relevant functions
'''
class Rider:
    def __init__(self, riderID, server, debug_, gen_utility, obf_level, req_delay, mech_name, privacy_level, z_qlg, g_res,alpha,geo_lat,geo_lon,r_uniform,g_remap=False):
        # common
        self.server=server
        self.debug_=debug_
        self.id = riderID
        self.state = SATISFIED
        self.obf_level = obf_level 
        self.first_req_time = None
        self.matchedDriver = None
        self.real_loc_req = False
        self.service_active = False
        self.genericUtility = None
        self.gen_utility = gen_utility
        self.rideDetails = []
        self.req_delay = req_delay
        self.retry_timer = None
        self.privacy_level = privacy_level
        self.mech_name = mech_name
        self.euclidean_dist = None
        self.max_search_distance=MAX_SEARCH_RAD
        self.z_qlg=z_qlg
        self.g_res=g_res
        self.alpha=alpha
        self.geo_lat=geo_lat
        self.geo_lon=geo_lon

        # real location
        self.rideRequestLocation = None
        self.real_num_of_trials = 0
        self.rideDestination = None
        self.driver_eta = None
        self.uniform=r_uniform # used for greedy remapping and nonuniform distribution cases
        self.greedy_remap=g_remap
        self.real_last_match_distance = SEARCH_RAD
        self.real_location_drivers = None
        self.real_loc_req_accept_time = None
        self.real_ride_start_time = None
        self.est_real_ride_start_time = None
        self.real_loc_accepted_driver = None
        self.num_real_loc_drivers = 0
        self.min_eta_real_loc_drivers = 0
        self.avg_etas_real_loc_drivers = 0
        self.real_accept_eta = None
        self.avg_real_acc_rate = 0
        self.avg_real_surge = None
        self.real_accept_eta_tolerance = None

        # obfuscated location
        self.obfuscatedReqeustLocation = None
        self.obf_rideDestination = None
        self.num_of_trials = 0
        self.numOfExtraTrials = 0
        self.obf_ride_start_time = None
        self.est_obf_ride_start_time = None
        self.obf_loc_processing_start = None
        self.obf_last_match_distance = SEARCH_RAD
        self.obf_loc_drivers = None
        self.obf_loc_req_accept_time = None
        self.obf_loc_accepted_driver = None
        self.obf_no_drivers_time = 0
        self.num_obf_loc_drivers = 0
        self.min_eta_obf_loc_drivers = 0
        self.avg_etas_obf_loc_drivers = 0
        self.obf_accept_eta = None
        self.avg_obf_acc_rate = 0
        self.avg_obf_surge = None
        self.obf_accept_eta_tolerance = None

    def rider_reset_parameters(self):
        # common
        self.state = SATISFIED
        self.first_req_time = None
        self.matchedDriver = None
        self.real_loc_req = False
        self.service_active = False
        self.retry_timer = None
        self.obf_real_eta = None
        self.euclidean_dist = None

        # real location
        self.rideRequestLocation = None
        self.real_num_of_trials = 0
        self.rideDestination = None
        self.driver_eta = None
        self.real_last_match_distance = SEARCH_RAD
        self.real_location_drivers = None
        self.real_loc_req_accept_time = None
        self.real_ride_start_time = None
        self.real_loc_accepted_driver = None
        self.num_real_loc_drivers = 0
        self.min_eta_real_loc_drivers = 0
        self.avg_etas_real_loc_drivers = 0
        self.real_accept_eta = None
        self.avg_real_acc_rate = 0
        self.avg_real_surge = None
        self.real_accept_eta_tolerance = None

        # obfuscated location
        self.obfuscatedReqeustLocation = None
        self.obf_rideDestination = None
        self.num_of_trials = 0
        self.numOfExtraTrials = 0
        self.obf_ride_start_time = None
        self.obf_loc_processing_start = None
        self.obf_last_match_distance = SEARCH_RAD
        self.obf_loc_drivers = None
        self.obf_loc_req_accept_time = None
        self.obf_loc_accepted_driver = None
        self.obf_no_drivers_time = 0
        self.num_obf_loc_drivers = 0
        self.min_eta_obf_loc_drivers = 0
        self.avg_etas_obf_loc_drivers = 0
        self.obf_accept_eta = None
        self.avg_obf_acc_rate = 0
        self.avg_obf_surge = None
        self.obf_accept_eta_tolerance = None

    def calculate_generic_util(self):
        if self.obfuscatedReqeustLocation:
            etas, distances = distance_api(self.rideRequestLocation, [self.obfuscatedReqeustLocation])
            self.genericUtility = distances[0]
        else:
            return False

    # Extract real location from mongodb database, generate obfuscated request location and real destination
    def initiateRideRequest(self, env):
        if self.num_of_trials == 1:
            self.first_req_time = env.now

        location = list(self.server.database.riders.distinct('locations',{'userID':self.id}))
        self.rideRequestLocation = location[0].get('coordinates')
        
        obf_location = list(self.server.database.riders.distinct('location_obf',{'userID':self.id}))
        self.obfuscatedReqeustLocation = obf_location[0].get('coordinates')
        
        self.euclidean_dist = float(vincenty(self.rideRequestLocation, self.obfuscatedReqeustLocation).meters)
        print('Rider {} initiating a ride with Euclidean QL {}'.format(self.id, round(self.euclidean_dist)))

        if self.rideRequestLocation == None or self.obfuscatedReqeustLocation == None:
            print('Rider {} has no location data R {} O {}'.format(self.id, self.rideRequestLocation, self.obfuscatedReqeustLocation))
            sys.exit()

        etas, distances = distance_api(self.rideRequestLocation, [self.obfuscatedReqeustLocation])

        self.obf_real_eta = etas[0]
        
        self.rideDestination = []
        
        self.rideDestination.append(numpy.random.uniform(self.server.regionLat1, self.server.regionLat2))
        self.rideDestination.append(numpy.random.uniform(self.server.regionLon1, self.server.regionLon2))

        if self.uniform==0:
            z=random.random()
            if z<0.05:
                self.rideDestination[0]=np.random.uniform(self.server.regionLat1,self.server.regionLat1+((self.server.regionLat2-self.server.regionLat1)/2),1)[0]
            else:
                self.rideDestination[0]=np.random.uniform(self.server.regionLat1+((self.server.regionLat2-self.server.regionLat1)/2),self.server.regionLat2,1)[0]
        



    def calculate_eta(self):
        location = list(self.server.database.drivers.distinct("locations",{"userID":self.matcqdDriver.id}))
        driverLocation = [location[0].get("coordinates")[0], location[0].get("coordinates")[1]]
        etas, distances = distance_api(self.rideRequestLocation, [driverLocation])
        return(etas[0])
        
    def calculate_destination_eta(self):
        etas, distances = distance_api(self.rideRequestLocation, [self.rideDestination])
        return(etas[0])

    def waiting_for_driver(self):
        self.state = WAITING_FOR_DRIVER_PICKUP

    def disclose_destination(self, driver):
        self.state = RIDING
        driver.rideDestination = self.rideDestination
        # driver.rideDestination = self.rideDestination if self.real_loc_req else self.obf_rideDestination

    def rateDriver(self):
        self.server.update_mongo_rider(self)
        # ride request was successful
        self.rider_reset_parameters()

    def run(self, env):
        while True:
            t = env.now
            if self.state == LOOKING_FOR_DRIVER:
                if not self.rideRequestLocation:
                    self.initiateRideRequest(env)

                self.matchedDriver = self.server.findDrivers(self, env)
                
                if self.matchedDriver != None:
                    if self.real_loc_req:
                        self.state = WAITING_FOR_DRIVER_ACCEPTANCE
                        self.real_location_drivers.pop(0)
                    else:
                        print("Obfuscated Location Rider {} - I found a Driver {}".format(self.id, self.matchedDriver.id))
                        self.state = WAITING_FOR_DRIVER_ACCEPTANCE
                else:
                    if self.real_loc_req == False:
                        # print('Obfuscated location No drivers in 2000m of Rider {}, sending request to server'.format(self.id))
                        self.num_of_trials += 1
                        self.service_active = False
                        self.server.serviceActive = False
                        self.obf_last_match_distance = SEARCH_RAD
                        if self.id not in self.server.pendingRiders:
                            self.server.pendingRiders.append(self.id)
                        '''
                        # Fill the ride details
                        if self.real_ride_start_time:
                            self.rideDetails.append([self.num_of_trials, self.numOfExtraTrials, self.real_num_of_trials, 0, 1, self.first_req_time, self.obf_ride_start_time, self.real_ride_start_time, self.genericUtility])
                            print('Rider {} Real location: Time to start ride {}; Obfuscated location: Ride incomplete'.format(self.id, self.real_ride_start_time))
                        else:
                            self.rideDetails.append([self.num_of_trials, self.numOfExtraTrials, self.real_num_of_trials, 0, 0, self.first_req_time, self.obf_ride_start_time, self.real_ride_start_time, self.genericUtility])
                            print('Rider {} Real location: Ride incomplete; Obfuscated location: Ride incomplete'.format(self.id))
                        # Reset the rider parameters as driver has given up
                        self.riderResetParameters()
                        '''

                    else:
                        # print('Real Location No drivers in 2000m of Rider {}, sending request to server'.format(self.id))
                        self.real_num_of_trials += 1
                        self.service_active = False
                        self.server.serviceActive = False
                        self.real_loc_req = False
                        # If all the drivers in the list of real location refused to serve, send the request again
                        self.real_last_match_distance = SEARCH_RAD
                        if self.id not in self.server.pendingRiders:
                            self.server.pendingRiders.append(self.id)
                        '''
                        if self.real_loc_req_accept_time == None:
                            if self.real_last_match_distance != 5000:
                                print('Real location Rider {} couldnt get cab at {} trying again'.format(self.id, self.real_last_match_distance))
                                self.matchedRider.service_active = False
                                self.matchedRider.real_loc_req = False
                                self.real_last_match_distance = 500
                                if self.id not in self.server.pendingRiders:
                                    self.server.pendingRiders.append(self.id)
                                self.real_location_drivers = None
                            else:
                                self.real_loc_req = False
                                print('Rider {} Real location couldnt get a cab'.format(self.id))
                                if self.obf_ride_start_time:
                                    self.rideDetails.append([self.num_of_trials, self.numOfExtraTrials, self.real_num_of_trials, 0, 1, self.first_req_time, self.obf_ride_start_time, self.real_ride_start_time, self.genericUtility])
                                    print('Rider {} Real location: Ride incomplete; Obfuscated location: Time to start ride - {}'.format(self.id, self.obf_ride_start_time))
                                else:
                                    print('Rider {} Real location: Ride incomplete; Obfuscated location: Yet to process'.format(self.id))
                        '''
                yield env.timeout(1)

            elif self.state == LOOKING_FOR_DRIVER_WAITING:
                self.server.pendingRiders.append(self.id)
                if self.debug_=='HIGH':
                    print('Rider {} waiting to request ride again'.format(self.id))

            elif self.state == WAITING_FOR_DRIVER_ACCEPTANCE:
                print("Rider {}: Waiting for driver acceptance; ETA is {}".format(self.id, self.driver_eta))

            elif self.state == WAITING_FOR_DRIVER_PICKUP:
                if self.debug_=='HIGH':
                    print("Rider {}: Waiting for Driver {} to pickup".format(self.id, self.matchedDriver.id))
                yield env.timeout(1)

            elif self.state == RIDING:
                if self.debug_=='HIGH':
                    print("Rider {}: I'm riding to location {}".format(self.id, self.rideDestination))
                self.rateDriver()
                yield env.timeout(1)

            elif self.state == SATISFIED:
                yield env.timeout(1)
                continue
            yield env.timeout(1)