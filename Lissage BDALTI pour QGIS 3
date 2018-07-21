
"""
Author: Zoran Cuckovic
This script is used for somoothing integer based DEMs 
(or other types of raster data with flat, continouous surfaces)

more detail on: LandscapeArchaeology.org/2018/lissage-bdalti/
"""

from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import ( QgsProcessing, QgsProcessingAlgorithm, 
QgsProcessingParameterRasterLayer, QgsProcessingParameterBoolean, 
QgsProcessingParameterRasterDestination)

       
from osgeo import gdal, osr
#import sys
import numpy as np               

class Lissage(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    THICK= 'THICK'
    OUTPUT = 'OUTPUT'

    def __init__(self):
        super().__init__()

    def name(self):
        return "lissage_ign"

    def tr(self, text):
        return QCoreApplication.translate("lissage", text)

    def displayName(self):
        return self.tr("Lissage BDALTI")

    def group(self):
        return self.tr("Raster")

    def groupId(self):
        return "raster"

    def shortHelpString(self):
        return self.tr("Lissage de MNT")


  #  def helpUrl(self):
    #    return "https://qgis.org"

    def createInstance(self):
        return type(self)()  

    def initAlgorithm(self, config=None):

      
        self.addParameter(QgsProcessingParameterRasterLayer
                          (self.INPUT,
            self.tr('MNT (raster)')))
                        
        self.addParameter(QgsProcessingParameterBoolean(
            self.THICK,
            self.tr('Lignes épaisses'), False))
            
        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
            self.tr("Résultat")))
            
    def processAlgorithm(self, parameters, context, feedback):
        
        input = self.parameterAsRasterLayer(parameters,self.INPUT, context)
        thick = self.parameterAsBool(parameters,self.THICK,context)
        output_path = self.parameterAsOutputLayer(parameters,self.OUTPUT,context)
		
        print (output_path)
        
        #load raster
        gdalData = gdal.Open(input.source())
        raster = gdalData.ReadAsArray()

        # get width and heights of the raster
        xsize = gdalData.RasterXSize
        ysize = gdalData.RasterYSize

        mask=np.zeros((ysize,xsize)).astype(bool)    
                
        views = [ [np.s_[1:, :], np.s_[:-1, :]],
                     [ np.s_[: , 1:] , np.s_[:, :-1]]]
         
        if thick:
            views +=  [ [np.s_[:-1, 1:], np.s_[1:, :-1]], 
                                      [np.s_[:-1, :-1], np.s_[1:, 1:]] ]

        for v in views :
            a,b = v
            mask[a] += raster[a]>raster[b]
            # test the opposite side 
            mask[b] += raster[b]>raster[a]
             
                    
        raster*=mask

        DriverGTiff = gdal.GetDriverByName('GTiff')
        OutputDataset =DriverGTiff.Create(output_path, xsize, ysize, 1, gdal.GDT_Float32) 

        #write to file -- force float format
        OutputDataset.GetRasterBand(1).SetNoDataValue(0.0)
        OutputDataset.GetRasterBand(1).WriteArray(raster)

        #set all metadata...
        OutputDataset.SetGeoTransform(gdalData.GetGeoTransform())
        outRasterSRS = osr.SpatialReference()
        outRasterSRS.ImportFromWkt(gdalData.GetProjectionRef())
        OutputDataset.SetProjection(outRasterSRS.ExportToWkt())

        return {self.OUTPUT: output_path}



