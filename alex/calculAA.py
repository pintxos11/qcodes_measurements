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

e=1.6e-19
h=6.6e-34
eps0=8.85e-12

B=8.0
np0=B/h*e
d=50e-9
nu=1

ne=nu*np0

C=3.2*eps0/d
V=ne/C

print (V*e)
