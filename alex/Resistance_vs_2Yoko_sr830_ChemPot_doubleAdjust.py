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

#0.05s per point + tsl
tsl=0.1  #time sleep each point
twait=5*tsl #time sleep each loop

Vmin=-2.0
#Vmax=-9.0
#Vnstep=1452
Vstep_init=0.03  # was good with div 2 on bg
n_ite=500
#Vg=np.linspace(Vmin,Vmax,Vnstep)   #yoko

offset_start=0.0
Vdmin=0.0+offset_start
Vdmax=0.0015+offset_start
Vdnstep=31  
Vdc=np.linspace(Vdmin,Vdmax,Vdnstep)   #yoko2

minvec_vt=np.mean(Vdc)

############### Virtual drivers #################

sys.path.append('C:\\forQcodes\\Drivers')

from qcodes.instrument_drivers.stanford_research.SR830 import SR830

lockin_B = SR830('Lockin', 'GPIB0::7::INSTR')


from GS200 import GS200 

yoko = GS200('yoko', 'GPIB0::1::INSTR')   # source   ADRESS GPIB    BACKGATE div 2 

yoko2 = GS200('yoko2', 'GPIB0::4::INSTR')   # source   ADRESS GPIB   Vc DIV 10

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
description='ChemPot_doubleAdjust_vs_Vc_Vgate_SET_21and14'
database_name = date+"_"+user+"_"+description
print(database_name)

exp_name     = 'Chem Pot_doubleAdjust vs Vdc and Vgate'
sample_name  = 'AA1'

###############################################################################
#                           DATA FOLDER CREATION
###############################################################################

script_dir=os.path.dirname(__file__)
data_dir=os.path.join(r'C:\\forQcodes\\Data_Qcodes\\AA1\\Cooldown1\\ChemPot_doubleAdjust_vs_Vdc_gate')

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
meas.register_custom_parameter('Chemical_potential', setpoints=['Vg'])

meas.register_parameter(lockin_B.X, setpoints=['Vdc', 'Vg'])
meas.register_parameter(lockin_B.Y, setpoints=['Vdc', 'Vg'])


############################## Measurement ##################################


time_start = time.time()

parameter_snap={}

print(f'database name : {database_name}')

yoko.ramp_voltage( Vmin, 0.2, 0.01)
yoko2.ramp_voltage( Vdc[0], 0.2, 0.01)

#dvgin=Vg[1]-Vg[0]
dvgin=Vstep_init

with meas.run() as datasaver:

	id=datasaver.dataset.run_id

	qc.load_by_run_spec( captured_run_id=id).add_metadata('parameter_snap',
						 json.dumps(parameter_snap))

	time0 = time.time()
	current_time = time.time() - time0
	chemPot=np.array([])
	new_vec_vt=Vdc

	Vginit=Vmin
	dvg=Vstep_init

	for i in range (n_ite) :

		print (100*i/n_ite, '%')

		yoko.ramp_voltage( Vginit, 100, 0.01)
		yoko2.ramp_voltage( new_vec_vt[0], 100, 0.01)

		if i==0:
			time.sleep(5.0)

		time.sleep(twait)

		current_x=np.array([])

		for j, valdc in enumerate(new_vec_vt) :

			yoko2.ramp_voltage( valdc, 100, 0.01)

			time.sleep(tsl)

			V_X2_B = lockin_B.X()  # voltage X
			V_Y2_B = lockin_B.Y()  # voltage Y

			current_x=np.append(current_x, V_X2_B)

			current_time = time.time() - time0 # elapsed time
			datasaver.add_result((lockin_B.X, V_X2_B),
								(lockin_B.Y, V_Y2_B),
								('Vdc', valdc),
								('Vg', Vginit),
	                            ('Time', current_time),
	                            ('Chemical_potential', minvec_vt))

		#change for adjusting measurement window around minima
		pfit=np.polyfit(new_vec_vt, current_x, 4)

		'''plt.close()
		plt.plot(new_vec_vt,current_x)
		plt.plot(new_vec_vt,np.polyval(pfit,new_vec_vt))
		plt.show(block=False)
		plt.pause(0.001)'''

		#Sminpa=np.array(np.where(np.polyval(pfit,new_vec_vt)==np.amin(np.polyval(pfit,new_vec_vt))))
		vtgar=np.arange(new_vec_vt[0],new_vec_vt[-1],1e-6)  #new
		Sminpa=np.array(np.where(np.polyval(pfit,vtgar)==np.amax(np.polyval(pfit,vtgar))))   #new  change between amin or amax depending on minima or maxima
		ri=int(np.mean(Sminpa[0,:]))
		#minvec_vt=new_vec_vt[ri]
		minvec_vt=vtgar[ri]  #new
		chemPot=np.append(chemPot, minvec_vt)

		print("middle value of the top gate sweep: {} ".format(minvec_vt))
		dvt=Vdc[1]-Vdc[0]
		f_newvt=minvec_vt-len(Vdc)/2*dvt
		l_newvt=minvec_vt+len(Vdc)/2*dvt
		new_vec_vt= np.linspace(f_newvt, l_newvt, len(Vdc) )

		if i>20:
			cons=np.mean(np.abs(np.diff(chemPot[10:-1])))
			print ("consigne=",cons)
			print ("actual=",np.abs(chemPot[-1]-chemPot[-2]))
		#if i>20:
			if np.abs(chemPot[-1]-chemPot[-2])>cons:
				dvg=dvg/1.5
			else:
				dvg=dvg*1.5
			if dvg>dvgin:
				dvg=dvgin

			print("initial dvg: {} ".format(dvgin))
			print("current dvg: {} ".format(dvg))

		Vginit=Vginit+dvg

yoko.ramp_voltage( 0.0, 0.2, 0.01)
yoko2.ramp_voltage( 0.0, 0.2, 0.01)

#plt.close()
#fig, axs = plt.subplots(2, sharex=True)
#axs[0].plot(Vg,chemPot*1e3)
#axs[0].set(ylabel='Chemical potential (mV)')

#axs[1].plot(Vg[0:-1],np.diff(chemPot)/np.diff(Vg))
#axs[1].set(xlabel='Vg (V)', ylabel='Incompressibility')

#plt.show()

current_time = time.time() 

print ('time measurement:', current_time-time_start, 's')


