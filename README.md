# Ride-Hailing-Service-Emulator

Ride hailing service emulator (RHSE) is built to collect the data of commonly occuring scenarios in ride hailing services (RHS) such as Uber and Lyft. RHSE is a simple tool in Python which can be tuned to different scenarios of RHSes. Below, we detail the requirements and setup instructions to use the tool.


## Requirements:

- We tested our code on Ubuntu 16.04 LTS with Python 2.7.12
- Python packages required (along with their versions we used while testing) are listed in requirements.txt and can be installed using *pip install -r requirements.txt*
- 'python-tk' is required to work along with the matplotlib package, which can be installed using 'apt-get install python-tk'
- Please follow the following commands to set up mongodb: (Alternately, you can try more detailed set up instructions here: https://tecadmin.net/install-mongodb-on-ubuntu/):<br />

sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4<br />
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/4.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb.list <br />
sudo apt update<br />
sudo apt install mongodb-org<br />
sudo systemctl enable mongod<br />
sudo systemctl start mongod 

To check if the mongodb is correctly set up, please check the version using *mongod --version* command. The second command will change based on the version of Ubuntu you are using.

## High level flow of the code:

- RHSE first generates a database of riders and drivers using mongodbGenerator.py. The database is then managed using a mongoDB client, PyMongo. For GUI of the database created, use any GUI client of MongoDB.
- Then riders start sending ride requests and based on availability, drivers accept them. A flow -- ride request to completion -- of a typical scenario in RHSes is given in Figure 1.
- Various attributes of each of the completed rides are logged in a csv file in appropriate folder.

## Creating a database of riders and drivers:
Using mongodbGenerator.py, one can generate a database of riders and drivers. We have given the discription of various variables used to generate the initial database in the mongodbGenerator.py file. Below, we give an example command to geenrate a database with : 200 riders, 120 drivers, in an area bounded by lat1 and lat2 from below and above, and lon1 and lon2 from sideways.

Set of variable and example values:

num_riders = 200 <br />
num_drivers = 120 <br />
regions = 15 <br />
db_name = 'example_Database' <br />
mech_name= 'planar_lap' <br />
g_res = 100 <br />
genric_util = 1.0 <br />
privacy_leve = 1.4 <br />
z_qlg = -1 # unused <br />
g_res = 100 <br />
uniform = 1 <br />
r_uniform = 1 <br />
g_remap = 0 <br />

Following variable are used only for exponential and geometric mechanisms, hence set to arbitrary values:<br />
alpha=10 <br />
geo_lat=10<br />
geo_lon=10

The command is as follows:

python mongodbGenerator.py number_riders, number_drivers, regions, db_name, mech_name, genric_util, privacy_level, z_qlg, g_res, uniform, alpha, geo_lat, geo_lon, r_uniform, g_remap
 
## Configuring scenarios:

- RHSE is built to configure different scenarios of RHSes, as described in Section 5.2. RHSes are complex systems with multiple tunable parameters, including the ones given in Table 4. We have detailed the description and variable name of each in run_pl_diff_driver_eta.py.

## Reproducing the results:

In order to reproduce the results in the paper, we provide sample scripts which can be modified to obtain the rest of the results in the paper. With the default configurations provided in the respective run_* files below, the time it takes to complete their run and re-produce the desired results varies from 6-10 hours. To check if code is making progress or not, please check the contents of .csv files: Specfically, one should check if the more ride details are being updated in the rider_results_* csv files that are placed inside the folder with name given by exp_folder in the corresponding script. 

The details of how to reproduce the results are as follows:

### Reproducing Figure 3
This figure demonstrates the effect of different parameters of RHSes on the evaluation of LPPMs. For demonstration, we use planar Laplace mechanism. More specifically, the figure demonstrates the effect of -- drivers' acceptance model, drivers' ETA tolerance and the number of drivers in each run; the details of these parameters are in Sec. 5.1.2.


- run_pl_diff_driver_models.py reproduces the results of Figure 3 (left)
- run_pl_diff_driver_etat.py reproduces the results of Figure 3 (middle)
- To reproduce the results of Figure 3 (right), please vary the number of drivers using variable called number_drivers as required.


### Reproducing Figure 4

This figure compares generic and tailored QLes due to different mechanisms under uniform and nonuniform distributions of RHS players, i.e., riders and drivers. 

- run_pl_uni_vs_nonuni.py reproduces the results in Figure 4 (right). Based on number of runs, the results may look different. We recommend collecting data with run_time=400.
- To reproduce the results in Figure 4 (left), collect data for planar Laplace and exponential mechanisms while setting uniform=1. This can be done by simply modifying run_pl_uni_vs_nonuni.py.
- To reproduce the results in Figure 4 (middle), collect data for planar Laplace and exponential mechanisms while setting uniform=0. This can be done by simply modifying run_pl_uni_vs_nonuni.py.


### Reproducing Figure 5

This figure compares planar Laplace and two variants of planar geometric with different grid resolution (g_res). The comparison is in terms of tailored and generic QLes of riders. The results can be reproduced by running run_epss_pl_pg.py.

### Reproducing Figure 6

This figure compares tailored and generic utility losses of riders when planar laplace mechanism is used with and without greedy remapping described in Sec. 6.4. The results can be reproduced by running run_pl_greedy_remap.py.
