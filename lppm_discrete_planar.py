from rhse_util import *
import numpy as np

# TODO: Try s = 100m as well
s = 200 # Length and width of each cell of the grid; in meters

def add_polar_noise(eps, pos_lat, pos_lon,z_qlg=None):
	theta = random.random() * math.pi * 2
	z = random.random()
	if z_qlg:
		z=z_qlg
	r = inverse_cumulative_gamma(eps, z)
	
	# TODO: Check if s = 50m is a good approximation or not. May be 1m is too small for such a large distances
	r_cos = r * math.cos(theta)
	r_cos_f = r_cos - (r_cos%s)
	r_cos_c = r_cos + (s - r_cos%s)
	
	r_sin = r * math.sin(theta)
	r_sin_f = r_sin - (r_sin%s)
	r_sin_c = r_sin + (s - r_sin%s)
	
	# print('theta - {}; r - {}; r_cos - {}; r_sin - {}'.format(theta, r, r_cos, r_sin))

	r_cos = r_cos_c if r_cos_c < r_cos_f else r_cos_f
	r_sin = r_sin_c if r_sin_c < r_sin_f else r_sin_f
	
	# print('theta - {}; r - {}; r_cos - {}; r_cos_c - {}; r_cos_f - {}; r_sin - {}; r_cos_c - {}; r_cos_f - {}'.format(theta, r, r_cos, r_cos_c, r_cos_f, r_sin, r_sin_c, r_sin_f))
	
	r = math.sqrt(r_cos**2 + r_sin**2)
	theta = math.atan2(r_sin, r_cos)

	return add_vector_to_pos(pos_lat, pos_lon, r, theta)



def add_discrete_lap_noise(location, eps,z_qlg=None):
	pos_lat = location[0]
	pos_lon = location[1]
	return add_polar_noise(eps, pos_lat, pos_lon,z_qlg=z_qlg)




