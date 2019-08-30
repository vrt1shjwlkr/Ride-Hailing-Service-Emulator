from rhse_util import *
from lppm_planar_lap import *
from lppm_exp import *
from lppm_planar_geo import *
from lppm_discrete_planar import *

'''
Following function generates obfuscated location based on given real location
mech_name - name of the mechanism viz. planar_lap, normal/Gaussian, random/uniform, circular/constant
gen_util - distance within which user expects the mechanism to preserve privacy according to Geo-indistingushability criteria; km units
'''

def obfuscate_loc(mech_name, location, gen_util, privacy_level,region,g_res,alpha,geo_lat,geo_lon):
	eps=math.log(privacy_level)/(1000 * gen_util)
	if mech_name == 'planar_lap':
		return add_lap_noise(location,eps)
	elif mech_name == 'planar_geo':
		return add_geo_noise(location,region,eps,g_res,alpha,geo_lat,geo_lon)
	elif mech_name == 'exp':
		return add_exp_noise(location, eps, region, g_res)
	else:
		print('Unsupported mechanism')
		os._exit(0)


'''
This function checks if the obfuscated location is in considered region
'''

def check_validity(lat1, lon1, lat2, lon2, location):
	lat = location[0]
	lon = location[1]
	
	if lat < lat1 or lat > lat2 or lon < lon1 or lon > lon2:
		return False

'''
This function truncates the obfuscated location i.e. remaps it to closest location in the considered area.
'''

def truncate_loc_(lat1, lon1, lat2, lon2, location):
	lat = location[0]
	lon = location[1]

	if lat < lat1 and lon < lon1:
		# region-1
		remap_lat=lat1
		remap_lon=lon1
	elif lat < lat1 and lon > lon1 and lon < lon2:
		# region-2
		remap_lat=lat1
		remap_lon=lon
	elif lat < lat1 and lon > lon2:
		# region-3
		remap_lat=lat1
		remap_lon=lon2
	elif lat > lat1 and lat < lat2 and lon > lon2:
		# region-4
		remap_lat=lat
		remap_lon=lon2
	elif lat > lat2 and lon > lon2:
		# region-5
		remap_lat=lat2
		remap_lon=lon2
	elif lat > lat2 and lon < lon2 and lon > lon1:
		# region-6
		remap_lat=lat2
		remap_lon=lon
	elif lat > lat2 and lon < lon1:
		# region-7
		remap_lat=lat2
		remap_lon=lon1
	elif lat < lat2 and lat > lat1 and lon < lon1:
		# region-8
		remap_lat=lat
		remap_lon=lon1
	elif lat < lat2 and lat > lat1 and lon < lon2 and lon > lon1:
		remap_lat=lat
		remap_lon=lon
	else:
		assert False, 'Invalid location {} Exiting..'.format(location)

	return [remap_lat, remap_lon]


def truncate_loc(lat1, lon1, lat2, lon2, location):
	lat = location[0]
	lon = location[1]

	if lat <= lat1 and lon <= lon1:
		# region-1
		remap_lat=lat1
		remap_lon=lon1
	elif lat <= lat1 and lon >= lon1 and lon <= lon2:
		# region-2
		remap_lat=lat1
		remap_lon=lon
	elif lat <= lat1 and lon >= lon2:
		# region-3
		remap_lat=lat1
		remap_lon=lon2
	elif lat >= lat1 and lat <= lat2 and lon >= lon2:
		# region-4
		remap_lat=lat
		remap_lon=lon2
	elif lat >= lat2 and lon >= lon2:
		# region-5
		remap_lat=lat2
		remap_lon=lon2
	elif lat >= lat2 and lon <= lon2 and lon >= lon1:
		# region-6
		remap_lat=lat2
		remap_lon=lon
	elif lat >= lat2 and lon <= lon1:
		# region-7
		remap_lat=lat2
		remap_lon=lon1
	elif lat <= lat2 and lat >= lat1 and lon <= lon1:
		# region-8
		remap_lat=lat
		remap_lon=lon1
	elif lat <= lat2 and lat >= lat1 and lon <= lon2 and lon >= lon1:
		remap_lat=lat
		remap_lon=lon
		# print('check')
	else:
		assert False, 'Invalid location {} Exiting..'.format(location)

	return [remap_lat, remap_lon]
