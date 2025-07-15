"""
***************************************************************************
*                                                                         *
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""
import numpy as np
import csv

from qgis.PyQt.QtCore import (QCoreApplication, QVariant) 
from qgis.core import (QgsProcessing,
                        QgsProcessingException,
                        QgsProcessingAlgorithm,
                        QgsProcessingParameterFeatureSource,
                        QgsProcessingParameterFileDestination ,
                        QgsProcessingParameterField, 
                        QgsProcessingParameterBoolean, 
                        QgsProcessingParameterNumber,
                        QgsSpatialIndexKDBush,
                        QgsFields, QgsField,
                        QgsVectorFileWriter, 
                        QgsWkbTypes,
                        QgsCoordinateReferenceSystem
                        )
from qgis import processing

class CovarianceEllipse(QgsProcessingAlgorithm):
    """
    This is an example algorithm that takes a vector layer and
    creates a new identical one.

    It is meant to be used as an example of how to create your own
    algorithms and explain methods and variables used to do it. An
    algorithm like this will be available in all elements, and there
    is not need for additional work.

    All Processing algorithms should extend the QgsProcessingAlgorithm
    class.
    """

    # Constants used to refer to parameters and outputs. They will be
    # used when calling the algorithm from another algorithm, or when
    # calling from the QGIS console.

    INPUT = 'INPUT'
    DISTANCE = 'DISTANCE'
    # KEY_FIELD= 'KEY_FIELD'
    # NEIGHBOURS = 'NEIGHBOURS'
    # COSINE_SIMILARITY= 'COSINE_SIMILARITY'
    OUTPUT = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return CovarianceEllipse()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'covariance_ellipse'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Covariance ellipse')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('Landscape Archaeology')

    def groupId(self):
        """
        Returns the unique ID of the group this algorithm belongs to. This
        string should be fixed for the algorithm, and must not be localised.
        The group id should be unique within each provider. Group id should
        contain lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'LandscapeArchaeology'

    def shortHelpString(self):
        """
        Returns a localised short helper string for the algorithm. This string
        should provide a basic description about what the algorithm does and the
        parameters and outputs associated with it..
        """
        return self.tr("Calculates the parameters for covar. ellipse within a set of points.")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        # We add the input vector features source. It can have any kind of
        # geometry.
        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Input layer'),
                [QgsProcessing.TypeVectorPoint]
            )
        )
    
       
        self.addParameter(QgsProcessingParameterNumber (
                                self.DISTANCE,
                                self.tr('Search radius (map units)'),
                                QgsProcessingParameterNumber.Double,
                                1000
                                ))

        self.addParameter(
             QgsProcessingParameterFileDestination (
                 self.OUTPUT,
                self.tr('Output layer'), 
                '.csv'
             )
         )

    def processAlgorithm(self, parameters, context, feedback):
        
        source = self.parameterAsSource(parameters, self.INPUT, context)
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        distance = self.parameterAsDouble( parameters, self.DISTANCE, context)
        output = self.parameterAsFileOutput(parameters, self.OUTPUT, context)
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        
        # create a dictionary (I don't handle the obtruse PyQgis ...)
        # dictionary : fast retrieval 
        features = {f.id(): f.geometry().asPoint()  
                        for f in source.getFeatures() }
        
        index = QgsSpatialIndexKDBush(source.getFeatures())
       
        # open the file in the write mode
        w = open(output, 'w', newline='')

        # create the csv writer
        writer = csv.writer(w)
        
        header = ['internal_id', 'count', 'ellipse_minor', 'ellipse_major', 
                        'center_x', 'center_y', 'azimuth_geo', 'eccentricity', 'offset']
       # if cosines : header += ['cosine_similarity']

        # write a row to the csv file
        writer.writerow(header)
        
        counter = 0
        for f, xy in features.items():
            
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled(): break
            
            coords = [] 
            
            # returns array of feature IDs of x nearest features
            # including the point under the origin 
            # QgsPointXY(x,y) : hard coded values
            for n in index.within(xy, distance) :
                coords.append(features[n.id]) 
                           
            x,y = np.array(coords).T #reshape for numpy covariance
         
            count=len(x)
            
            if count > 2:
                     
                cov = np.cov(x, y) # calcul basé sur (n-1)
                # Compute eigenvectors (principal directions)
                eigenval,eigenvecs = np.linalg.eigh(cov)  # sorted low → high
                minor_axis = eigenvecs[:, 0]              # direction of minor axis
                major_axis = eigenvecs[:, 1]              # direction of major axis
                
                # eccentricity : eigenvals are sorted and squared already (!)
                exc = np.sqrt(1 - eigenval[0]/eigenval[1])
                
                # point to line distance = vector A * vector B = (x−x0)⋅* sin(θ) − (y−y0)⋅* cos(θ)
                # offset = (xy[0]- x.mean()) * np.sin(theta1) - (xy[1]- y.mean()) * np.cos(theta1) 
                # ...or use dot product - here
                offset = [xy[0]- x.mean(), xy[1] - y.mean()]
                # Project the offset onto the minor axis (i.e., perpendicular to main axis)
                offset = np.dot(offset, minor_axis)  # signed perpendicular distance
                
                 # geographic north conversion
                 # Vector from eigen decomposition (unit vector)
                dx, dy = major_axis

                # Angle in radians from North (y-axis), clockwise
                theta_rad = np.arctan2(dx, dy)  # not dy, dx

                # Convert to degrees from North, ensuring [0, 360)
                # attention : 360 degrees, while only 180 makes sense (if az > 180: az -= 18)
                azimuth = (np.degrees(theta_rad) + 360) % 360
                
                output = [f, count,  *np.sqrt(eigenval),
                            x.mean(), y.mean(), azimuth , exc, abs(offset)]
                
            else: output = [f, count, 0,0,  x.mean(), y.mean(),0,0,0]
            
            writer.writerow(output)
            
                  # Update the progress bar
            feedback.setProgress(int(counter * total))
            counter +=1
 
        w.close()
        return {self.OUTPUT: None}
