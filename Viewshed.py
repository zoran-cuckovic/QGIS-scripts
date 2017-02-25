##Viewshed =name
##Raster=group
##Point_Layer=vector
##Elevation=raster
##radius=number 10000
##observer_height=number 1.6
##Output=output raster

# ERROR  = LINE 61 !!

from qgis.core import *
from PyQt4.QtCore import *
import gdal

import numpy as np

from ViewshedAnalysis import doViewshed as ws
from ViewshedAnalysis import Points as pts

# 1 open raster and read basic parameters
r= gdal.Open(Elevation)

projection= r.GetProjection() 

gt= r.GetGeoTransform()

#pixels must be square !!
# will not give useful results if pixels are rectangular
pix = gt[1] 

raster_x_min = gt[0]
raster_y_max = gt[3] # it's top left y, so maximum!

raster_y_size = r.RasterYSize
raster_x_size = r.RasterXSize

raster_y_min = raster_y_max - raster_y_size * pix
raster_x_max = raster_x_min + raster_x_size * pix

#extent, to filter points
ext = QgsRectangle(raster_x_min, raster_y_min,  raster_x_max, raster_y_max)

#output matrix = entire raster
matrix_final = np.zeros ( (raster_y_size, raster_x_size) )

# 2  convert points shapefile into a dictionary
# supplementary keyword arguments can be used :
# z_targ : target height, 
 # field_ID : name of table filed that holds IDs of points,
 # field_zobs : name of table filed that holds  observer height - for each point
 # field_ztarg : same for target height 
 # field_radius : same for analysis radius
 
p = pts.Points()
p.point_dict(Point_Layer, ext, pix, observer_height, radius)

# --------- ERROR ------------------
# this should move the point to a higher loaction
#it opens the Eleevation raster to check heights

#  >>   p.search_top_z (1, Elevation)

# -------------------------------------
points = p.pt

# 3 create distance and error matrix
#  >>  an additional matrix needs to be made for  Earth curvature (not implemented here!)

radius_float = radius/pix
radius_pix = int(radius_float)

full_window_size = radius_pix *2 + 1
 
#  pixel distances for the entire viewshed area
temp_x= ((np.arange(full_window_size) - radius_pix) ) **2
temp_y= ((np.arange(full_window_size) - radius_pix) ) **2
mx_dist = np.sqrt(temp_x[:,None] + temp_y[None,:])

# mask corners for circular result (othervise the calculation is on a square slice
mask_circ = mx_dist [:] > radius_float 

# we draw all lines beforehand (indices), and save their offsets from pixel centres (errors)
# mask is used to filter the least error instances for each pixel
indices, error_indices, errors, mask = ws.error_matrix(radius_pix)

for p_id in points:
    x,y= points[p_id]["x_pix"],  points[p_id]["y_pix"]

    
    #gives full window size by default
    data, cropping = ws.dem_chunk ( x, y, radius_pix, r) 

    #parameters to place correctly the extracted data window
    (x_offset, y_offset,
         x_offset_dist_mx, y_offset_dist_mx,
         window_size_x, window_size_y) = cropping
         
      # take absolute height immediately
     #observer is in the center of the matrix (positoin = radius in pixels)
    z_abs =points[p_id]["z"] + data [radius_pix,radius_pix] 

    # caulculate angular height
    data = (data - z_abs) / mx_dist
    
    v = ws.viewshed_raster("Binary", data, errors, mask, indices, error_indices)
    # additional keyword arguments : target_matrix = None (all same as elevation matrix, 
    # but with target height added to the entire raster), algorithm =1 (0 for non interpolated
   # calculation, 1 for normal) 
   
    v [mask_circ] = 0 #make it circular
    
    #clumsy... place correctly the analysed window inside the raster
    matrix_final [ y_offset : y_offset + window_size_y,
                               x_offset : x_offset + window_size_x ] += v [
                                   y_offset_dist_mx : y_offset_dist_mx +  window_size_y,
                                    x_offset_dist_mx : x_offset_dist_mx + window_size_x] 


# write output
driver = gdal.GetDriverByName( 'GTiff' )
  
c = driver.CreateCopy(Output, r , 0) #WHAT IS 0 ? : "strict or not" default =1

c.GetRasterBand(1).WriteArray(matrix_final)

c = None
