# Ride-Hailing-Service-Emulator

Ride hailing service emulator (RHSE) is built to collect the data of commonly occuring scenarios in ride hailing services (RHS) such as Uber and Lyft. RHSE is a simple tool in Python which can be tuned to different scenarios of RHSes. Below, we detail the requirements and setup instructions to use the tool.


## Requirements:

- MongoBooster 3.6
- Python; the tool is tested with Python 3.6. Python packages required are listed in requirements.txt and can be installed using pip install -r requirements.txt

## High level flow of the code:

- RHSE first generates a database of riders and drivers using mongodbGenerator.py. The database is then managed using a mongoDB client, PyMongo. For GUI of the database created, use any GUI client of MongoDB.
- Then riders start sending ride requests and based on availability, drivers accept them. A flow -- ride request to completion -- of a typical scenario in RHSes is given in Figure 1.
- Various attributes of each of the completed rides are logged in a csv file in appropriate folder.

## Configuring scenarios:

- RHSE is built to configure different scenarios of RHSes, as described in Section 5.2. RHSes are complex systems with multiple tunable parameters, including the ones given in Table 4. We have detailed the description and variable name of each in run_pl_diff_driver_eta.py.

## Reproducing the results:

In order to reproduce the results in the paper, we provide sample scripts which can be modified to obtain the rest of the results in the paper. The details are as follows:

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
