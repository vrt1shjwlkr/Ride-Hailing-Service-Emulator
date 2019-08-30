from rhse_util import *

def add_polar_noise(eps, pos_lat, pos_lon):
	theta = random.random() * math.pi * 2
	
	z=1-random.random()

	r = inverse_cumulative_gamma(eps, z)
	# print('obfuscation distance is %.1f'%r)
	return add_vector_to_pos(pos_lat, pos_lon, r, theta)


def add_lap_noise(location, eps):
	pos_lat = location[0]
	pos_lon = location[1]
	return add_polar_noise(eps, pos_lat, pos_lon)

def check_r(l,r):
	d=0
	for i in range(1000):
		z=random.random()
		s = inverse_cumulative_gamma((math.log(l)/r), z)
		d+=s
	print(d/1000)

# check_r(1.4,.1)