
##Visualisation= group
##input_layer=vector
##azimuth_field=string azimuth
##bin_count=number 32
##hollow_radius=number 0

import numpy as np
import matplotlib.pyplot as plt
from PyQt4.QtGui import *

N = int(bin_count)

input = processing.getObject(input_layer)
provider = input.dataProvider()

fieldIdx = provider.fields().indexFromName(azimuth_field)
if fieldIdx < 0:
    QMessageBox.information(None, "Error","Field does not exist!")
    Exit 
    
features = input.getFeatures()

out=[]
for f in features: 
    v=f[fieldIdx]
    if 0.00001 <= v <= 360 and f['tip']=="En circ":  out.append(v)

#theta = np.linspace(0.0, 2 * np.pi, N, endpoint=False)
#radii = max_height*np.random.rand(N)
theta = np.linspace(0,  2 * np.pi, N, endpoint=False)

radii, labels = np.histogram (np.array(out), bins=N)
width = 2*np.pi  / N


ax = plt.subplot(111, polar=True)
#put north to top , arrange clockwise, give geographic labels (instead of angles)
ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])

bars = ax.bar(theta, radii, width=width,bottom=hollow_radius)# 

# Use custom colors and opacity
for r, bar in zip(radii, bars):
    bar.set_facecolor(plt.cm.jet(r / 10.))
    bar.set_alpha(0.8)

plt.show()