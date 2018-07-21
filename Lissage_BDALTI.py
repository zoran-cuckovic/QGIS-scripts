##Raster=group
##Input=raster
##Ligne_epaisse=boolean
##Output=output raster

"""
Author: Zoran Cuckovic
This script is used for somoothing integer based DEMs 
(or other types of raster data with flat, continouous surfaces)

more detail on: LandscapeArchaeology.org/2018/lissage-bdalti/
"""

from osgeo import gdal, osr
import sys
import numpy as np


# load raster
gdalData = gdal.Open(str(Input))
raster = gdalData.ReadAsArray()

# get width and heights of the raster
xsize = gdalData.RasterXSize
ysize = gdalData.RasterYSize

mask=np.zeros((ysize,xsize)).astype(bool)    
        
views = [ [np.s_[1:, :], np.s_[:-1, :]],
             [ np.s_[: , 1:] , np.s_[:, :-1]]]
 
if Ligne_epaisse:
    views +=  [ [np.s_[:-1, 1:], np.s_[1:, :-1]], 
                              [np.s_[:-1, :-1], np.s_[1:, 1:]] ]

for v in views :
        a,b = v
        
        for reverse in [0,1]: 
            # test the opposite side 
            if reverse:   a, b = b, a 
        
            mask[a] += raster[a]>raster[b]
            
raster*=mask

DriverGTiff = gdal.GetDriverByName('GTiff')
OutputDataset =DriverGTiff.Create(Output, xsize, ysize, 1, gdal.GDT_Float32) 

#write to file -- force float format
OutputDataset.GetRasterBand(1).SetNoDataValue(0.0)
OutputDataset.GetRasterBand(1).WriteArray(raster)

#set all metadata...
OutputDataset.SetGeoTransform(gdalData.GetGeoTransform())
outRasterSRS = osr.SpatialReference()
outRasterSRS.ImportFromWkt(gdalData.GetProjectionRef())
OutputDataset.SetProjection(outRasterSRS.ExportToWkt())

