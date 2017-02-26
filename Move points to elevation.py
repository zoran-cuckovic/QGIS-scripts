##Move points to higher location=name
##Vector=group
##Points=vector
##Elevation=raster
##Radius=number 50
# nromally, create a new file which is a copy of the input
#but with new coords. Or modify directly input file..
##Modify_input_file_NOT_IMPLEMENTED=boolean
##Output NOT USED=output vector

from qgis.core import *
from PyQt4.QtCore import *
#from processing.tools.vector import VectorWriter
import processing 
import gdal
import numpy as np


r= gdal.Open(Elevation)

gt= r.GetGeoTransform()

#pixels must be square !!
# will not give useful results if pixels are rectangular
pix = gt[1] 

radius_pix = int(Radius/pix)

raster_x_min = gt[0]
raster_y_max = gt[3] # it's top left y, so maximum!

raster_y_size = r.RasterYSize
raster_x_size = r.RasterXSize

#raster_y_min = raster_y_max - raster_y_size * pix
#raster_x_max = raster_x_min + raster_x_size * pix

 

inputLayer = processing.getObject(Points)
feats = inputLayer.getFeatures()
for feat in  feats:

    pt = feat.geometry().asPoint()
    pt_id = feat.id()
     
    x_g, y_g = pt

    x =  int((x_g - raster_x_min) / pix) # not float !
    y = int((raster_y_max - y_g) / pix) #reversed !

    if not 0 <= x < raster_x_size or not 0 <= y < raster_y_size : continue
       
       #cropping from the front
    if x <= radius_pix:   x_offset =0
       #cropping from the back
    else:      x_offset = x - radius_pix         
      
    if y <= radius_pix:  y_offset =0
    else:   y_offset = y - radius_pix

    x_offset2 = min(x + radius_pix +1, raster_x_size) #could be enormus radius, so check both ends always
    y_offset2 = min(y + radius_pix + 1, raster_y_size )
    
    window_size_y = y_offset2 - y_offset
    window_size_x = x_offset2 - x_offset

    mx = r.ReadAsArray(x_offset, y_offset, window_size_x, window_size_y).astype(float)
    m = np.argmax(mx)

    iy, ix=np.unravel_index(m, mx.shape)
    
    #0.5 is to move to the center of corresp. pixel
    x2_g = ( ix +0.5 + x_offset) * pix  + raster_x_min 
    
    y2_g = raster_y_max - (y_offset + iy + 0.5) * pix  

    g= QgsGeometry.fromPoint(QgsPoint( x2_g, y2_g))
    
    inputLayer.dataProvider().changeGeometryValues({ pt_id : g })
    #feat.geometry().setX = x2_g
    #feat.geometry().setY= y2_g


