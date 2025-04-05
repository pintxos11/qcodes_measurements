#import requests
import urllib.request
import numpy as np
import requests
import sys

import qcodes as qc
from qcodes.logger.logger import start_all_logging
from qcodes.dataset.plotting import plot_dataset,plot_by_id
from qcodes.instrument.specialized_parameters import ElapsedTimeParameter
#from qcodes.loops import Loop
#from qcodes.plots.pyqtgraph import QtPlot
import numpy as np
import datetime
import time
import matplotlib.pyplot as plt
from time import sleep
import json
import os

############### Virtual drivers #################

sys.path.append('C:\\forQcodes\\Drivers')

from qcodes.instrument_drivers.stanford_research.SR830 import SR830

lockin_B = SR830('Lockin', 'GPIB0::7::INSTR')


from GS200 import GS200

yoko = GS200('yoko', 'GPIB0::2::INSTR')   # source   ADRESS GPIB    BACKGATE div 2

yoko2 = GS200('yoko2', 'GPIB0::4::INSTR')   # source   ADRESS GPIB   Vc fine DIV 10

yoko3 = GS200('yoko3', 'GPIB0::1::INSTR')   # source   ADRESS GPIB   Vc dfield DIV 10

yoko3.ramp_voltage(12.0, 0.2, 0.01)

#0.05s per point + tsl
tsl=0.03  #time sleep each point
twait=10*tsl #time sleep each loop

Vmin=-3.078
Vmax=-2.863
Vnstep=215  #51
Vg=np.linspace(Vmin,Vmax,Vnstep)   #yoko

Vdmin=0.46137
Vdmax=0.46721
Vdnstep=121  #75
Vdc=np.linspace(Vdmin,Vdmax,Vdnstep)   #yoko2

###############################################################################
#
#                      INITIALIZE QCODES EXPERIMENT
#
###############################################################################

start_all_logging()

# Create a station
station = qc.Station()
# station.add_component(lockin_C)
station.add_component(lockin_B)
# station.add_component(lockin)
# station.add_component(lockin_thermometre)

station.snapshot()
station.components

# Experiment details
user='AA'
date=datetime.datetime.today().strftime('%Y_%m_%d')
description='Resistance_vs_Vc_Vgate_SET_21_14'
database_name = date+"_"+user+"_"+description
print(database_name)

exp_name     = 'Resistance vs Vdc and Vgate'
sample_name  = 'AA1'

###############################################################################
#                           DATA FOLDER CREATION
###############################################################################

script_dir=os.path.dirname(__file__)
data_dir=os.path.join(r'C:\\forQcodes\\Data_Qcodes\\AA1\\Cooldown1\\R_vs_Vdc_gate')

try :
	os.mkdir(data_dir)
except FileExistsError:
	pass

data_dir=data_dir +'\\'+description

try :
	os.mkdir(data_dir)
except FileExistsError:
	pass

###############################################################################
#                       CREATE OR INITIALIZE DATABASE
################################################################################

qc.initialise_or_create_database_at(data_dir+'\\'+database_name+'.db')
qc.config.core.db_location


exp=qc.load_or_create_experiment(experiment_name=exp_name,
									  sample_name=sample_name)

meas = qc.Measurement(exp=exp, station=station)
#meas.register_parameter(VNA.channels.S21.power)

# meas.register_parameter(lockin_thermometre.R)

meas.register_custom_parameter('Time', unit='s')
meas.register_custom_parameter('Vdc', unit='V')
meas.register_custom_parameter('Vg', unit='V')

meas.register_parameter(lockin_B.X, setpoints=['Vdc', 'Vg'])
meas.register_parameter(lockin_B.Y, setpoints=['Vdc', 'Vg'])


############################## Measurement ##################################


time_start = time.time()

parameter_snap={}

print(f'database name : {database_name}')

yoko.ramp_voltage( Vg[0], 0.2, 0.01)
yoko2.ramp_voltage( Vdc[0], 0.2, 0.01)

with meas.run() as datasaver:

	id=datasaver.dataset.run_id

	qc.load_by_run_spec( captured_run_id=id).add_metadata('parameter_snap',
						 json.dumps(parameter_snap))

	time0 = time.time()
	current_time = time.time() - time0

	for i, valg in enumerate(Vg) :

		yoko.ramp_voltage( valg, 100, 0.01)
		yoko2.ramp_voltage( Vdc[0], 100, 0.01)

		if i==0:
			time.sleep(5.0)

		time.sleep(twait)

		for j, valdc in enumerate(Vdc) :

			yoko2.ramp_voltage( valdc, 100, 0.01)

			time.sleep(tsl)

			V_X2_B = lockin_B.X()  # voltage X
			V_Y2_B = lockin_B.Y()  # voltage Y

			current_time = time.time() - time0 # elapsed time
			datasaver.add_result((lockin_B.X, V_X2_B),
								(lockin_B.Y, V_Y2_B),
								('Vdc', valdc),
								('Vg', valg),
	                            ('Time', current_time))  

current_time = time.time() 

print ('time measurement:', current_time-time_start, 's')
#yoko.ramp_voltage( 0.0, 0.2, 0.01)
#yoko2.ramp_voltage( 0.0, 0.2, 0.01)


