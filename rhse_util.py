from __future__ import division
import random, math, logging, os
from scipy.special import lambertw
from geopy.distance import vincenty
from globalvars import *

earth_radius = 6378137

def add_polar_noise_cartesian(eps, pos_lat, pos_lon):
	if pos_lat:
		pos_lat, pos_lon = get_cartesian(pos_lat, pos_lon)

	theta = random.random() * math.pi * 2
	z = random.random()
	r = inverse_cumulative_gamma(eps, z)

	x = pos_lat + r * math.cos(theta)
	y = pos_lon + r * math.sin(theta)

	return x, y

def get_lat_lon(cart_x, cart_y):
	rLon = cart_x / earth_radius;
	rLat = 2 * (math.atan(math.exp(cart_y / earth_radius))) - math.pi/2;
	# convert to degrees
	return(deg_of_rad(rLat), deg_of_rad(rLon))

def get_cartesian(ll_lon, ll_lat):
	# latitude and longitude are converted in radiants
	x = earth_radius * rad_of_deg(ll_lon)
	y = earth_radius * math.log(math.tan((math.pi/4) + rad_of_deg(ll_lat)/2))
	return x, y

# returns alpha such that the noisy pos is within alpha from the real pos with
# probability at least delta
# (comes directly from the inverse cumulative of the gamma distribution)

def alpha_delta_accuracy(eps, delta):
	return inverse_cumulative_gamma(eps, delta)

def expected_err(eps):
	return 2/eps

# convert an angle in radians to degrees and viceversa
def rad_of_deg(ang):
	return ang * math.pi/180

def deg_of_rad(ang):
	return ang * 180/math.pi

# LamberW function on branch -1 (http://en.wikipedia.org/wiki/Lambert_W_function)
def lambert_w(x):
	# min_diff decides when the while loop should stop
	min_diff = 1e-10
	if (x == -1/math.e):
		return -1
	elif x < 0 and x > -1/math.e:
		q = math.log(-x)
		p = 1
		while (abs(p-q) > min_diff):
			p=(q*q+x/math.exp(q))/(q+1)
			q=(p*p+x/math.exp(p))/(p+1)
		# This line decides the precision of the float number that would be returned
		return (round(100000*q)/100000)
	else:
		return 0

# This is the inverse cumulative polar laplacian distribution function. 
def inverse_cumulative_gamma(eps, z):
	x = (z-1)/math.e
	return -(lambertw(x, k=-1).real + 1)/eps
	# print(-1/math.e, x, -(lambertw(x, k=-1).real + 1)/eps, -(lambert_w(x) + 1)/eps)

def add_vector_to_pos(pos_lat, pos_lon, distance, angle):
	ang_distance = distance/earth_radius

	lat1 = rad_of_deg(pos_lat)
	lon1 = rad_of_deg(pos_lon)
	
	lat2 = math.asin(math.sin(lat1) * math.cos(ang_distance) + math.cos(lat1) * math.sin(ang_distance) * math.cos(angle))
	lon2 = lon1 + math.atan2(math.sin(angle) * math.sin(ang_distance) * math.cos(lat1), 
							 math.cos(ang_distance) - math.sin(lat1) * math.sin(lat2) 
							)

	lon2 = (lon2 + 3 * math.pi) % (2 * math.pi) - math.pi

	lat = deg_of_rad(lat2)
	lon = deg_of_rad(lon2)

	# print('distance - ',float(vincenty([pos_lat,pos_lon], [lat,lon]).meters))
	return [lat, lon]

#Paris
paris_lat1 = (48.810519)
paris_lat2 = (48.901606)
paris_lon1 = (2.275873)
paris_lon2 = (2.421079)

'''
Following function returns ETA tolerance of driver given her location.
Used when ETA tolerances are non-uniform namely depend on area of drivers.
'''
def check_driver_loc(driverLocation):
    if driverLocation[0]>paris_lat1 and driverLocation[0]<(paris_lat1+(paris_lat2-paris_lat1)/2) and driverLocation[1]>paris_lon1 and driverLocation[1]<(paris_lon1+(paris_lon2-paris_lon1)/2):
    # if driverLocation[0]>paris_lat1 and driverLocation[0]<(paris_lat1+(paris_lat2-paris_lat1)/2) and driverLocation[1]>paris_lon1 and driverLocation[1]<paris_lon2:
        return True
    else:
        return False 