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

yoko3.ramp_voltage(5.25, 0.2, 0.01)

rampstep=0.1

#lockin parameters
tclockin=0.03
tsl=2*tclockin   #time sleep each point
twait=10*tclockin #time sleep each loop

lockin_B.amplitude(0.1)   #V
lockin_B.time_constant(tclockin)  #s
lockin_B.sensitivity(500e-6)   #V

tophBN=60
bothBN=49
slope=1/1.134945   ##bothBN/tophBN or in situ calibration
#0.05s per point + tsl

offset_start = 0.0
Vdmin = 0.0 + offset_start
Vdmax = 0.00125 + offset_start  # was good with div 10 on Vc
Vdnstep = 41
Vdc = np.linspace(Vdmin, Vdmax, Vdnstep)  # yoko2
dvt = Vdc[1] - Vdc[0]

minvec_vt=np.mean(Vdc)

divVg3=10.967
divVg=2

Vstate=-1.89  #-3.19
Vgrange=0.1152*2.0
Vmin=Vstate-Vgrange
Vmax=Vstate+Vgrange
Vnstep=230*2 #230
Vg=np.linspace(Vmin,Vmax,Vnstep)   #yoko

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
description='ChemPot_vs_Vc_Vgate_SET_21and14'
database_name = date+"_"+user+"_"+description
print(database_name)

exp_name     = 'Chem Pot vs Vdc and Vgate'
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
meas.register_custom_parameter('Nmeas', unit='V')

meas.register_custom_parameter('Chemical_potential', setpoints=['Vg', 'Nmeas'])

meas.register_parameter(lockin_B.X, setpoints=['Vdc', 'Vg', 'Nmeas'])
meas.register_parameter(lockin_B.Y, setpoints=['Vdc', 'Vg', 'Nmeas'])

############################## Measurement ##################################

time_start = time.time()

parameter_snap={}

print(f'database name : {database_name}')

yoko.ramp_voltage( Vg[0], rampstep, 0.01)
yoko2.ramp_voltage( Vdc[0], rampstep, 0.01)

with meas.run() as datasaver:

	id=datasaver.dataset.run_id

	qc.load_by_run_spec( captured_run_id=id).add_metadata('parameter_snap',
						 json.dumps(parameter_snap))

	time0 = time.time()
	current_time = time.time() - time0
	#chemPot=np.array([])
	new_vec_vt=Vdc

	continuous = 1000000
	indin = 0
	while indin < continuous:
		time_start2 = time.time()

		if indin>0 and indin%2==0:
			Vg = Vg[::-1]

		if indin%2!=0:
			Vg=Vg[::-1]

		if indin==0:
			time.sleep(5.0)

		for i, valg in enumerate(Vg) :
			#print (new_vec_vt)

			#if i > 0 and i%2==0:
				#new_vec_vt = new_vec_vt[::-1]
			if i%10==0:
				print ('Vg sweep:', i/Vnstep*100, '%')

			if i%2!=0:
				new_vec_vt = new_vec_vt[::-1]

			yoko.ramp_voltage( valg, rampstep, 0.01)
			yoko2.ramp_voltage( new_vec_vt[0], rampstep, 0.01)

			time.sleep(twait)

			current_x=np.array([])

			#print (new_vec_vt)

			for j, valdc in enumerate(new_vec_vt) :

				yoko2.ramp_voltage( valdc, 100, 0.01)

				time.sleep(tsl)

				#V_X2_B = lockin_B.X()  # voltage X
				#V_Y2_B = lockin_B.Y()  # voltage Y

				V_X2_B,V_Y2_B = lockin_B.snap("x", "y")  # voltage X, Y

				current_x=np.append(current_x, V_X2_B)

				current_time = time.time() - time0 # elapsed time
				datasaver.add_result((lockin_B.X, V_X2_B),
									(lockin_B.Y, V_Y2_B),
									('Vdc', valdc),
									('Vg', valg),
									('Nmeas', indin),
									 ('Time', current_time),
	                          	  ('Chemical_potential', minvec_vt+indin*5e-3))

			#change for adjusting measurement window around minima
			pfit=np.polyfit(new_vec_vt, current_x, 4, full=True)

			#plt.close()
			#plt.plot(new_vec_vt,current_x, '.-')
			#plt.plot(new_vec_vt,np.polyval(pfit[0],new_vec_vt))
			#plt.show(block=False)
			#plt.pause(0.001)

			#Sminpa=np.array(np.where(np.polyval(pfit,new_vec_vt)==np.amin(np.polyval(pfit,new_vec_vt))))
			#vtgar=np.arange(new_vec_vt[0],new_vec_vt[-1],1e-6)  #new
			vtgar=np.linspace(new_vec_vt[0],new_vec_vt[-1],10000)  #new

			Sminpa=np.array(np.where(np.polyval(pfit[0],vtgar)==np.amax(np.polyval(pfit[0],vtgar))))   #new  change between amin or amax depending on minima or maxima
			ri=int(np.mean(Sminpa[0,:]))
			#minvec_vt=new_vec_vt[ri]
			minvec_vt=vtgar[ri]  #new
			#chemPot=np.append(chemPot, minvec_vt)

			#print("middle value of the top gate sweep: {:.7f} ".format(minvec_vt), "residual: {} ".format(pfit[1]))
			f_newvt=minvec_vt-len(Vdc)/2*dvt
			l_newvt=minvec_vt+len(Vdc)/2*dvt
			new_vec_vt= np.linspace(f_newvt, l_newvt, len(Vdc) )

		indin += 1

		current_time = time.time()
		print('time one measurement:', current_time - time_start2, 's')
		print('current number of measurements:', indin)

#yoko.ramp_voltage( 0.0, rampstep, 0.01)
#yoko2.ramp_voltage( 0.0, rampstep, 0.01)

#plt.close()
#fig, axs = plt.subplots(2, sharex=True)
#axs[0].plot(Vg,chemPot*1e3)
#axs[0].set(ylabel='Chemical potential (mV)')

#axs[1].plot(Vg[0:-1],np.diff(chemPot)/np.diff(Vg))
#axs[1].set(xlabel='Vg (V)', ylabel='Incompressibility')

#plt.show()

current_time = time.time() 

print ('time measurement:', current_time-time_start, 's')


