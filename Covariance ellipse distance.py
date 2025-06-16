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
        return 'covariance2'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Covariance ellipse 2')

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
        return self.tr("Example algorithm short description")

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

        """
        self.addParameter(QgsProcessingParameterField(
                                self.KEY_FIELD,
                                self.tr('Category name field NOT USED'), 
                                parentLayerParameterName=self.INPUT, 
                           optional=True     ))
       
        self.addParameter(QgsProcessingParameterNumber (
                                self.NEIGHBOURS,
                                self.tr('Minimum number of neighbours NOT USED'),
                                QgsProcessingParameterNumber.Integer,
                                3
                                ))
        
        self.addParameter(QgsProcessingParameterBoolean (
                                self.COSINE_SIMILARITY,
                                self.tr('Cosine similarity USELESS')
                                ))
                                
        """
        # TODO : WRITE Geometry QgsProcessingParameterVectorDestination
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

        namefieldname = self.parameterAsString(parameters, self.KEY_FIELD, context)
        distance = self.parameterAsDouble( parameters, self.DISTANCE, context)
        # TODO
        # min_neighbours = self.parameterAsInt( parameters, self.NEIGHBOURS, context)
        # cosines = self.parameterAsInt( parameters, self.COSINE_SIMILARITY, context)
        # valuefieldname = self.parameterAsString(parameters, self.VALUE_FIELD, context)

        output = self.parameterAsFileOutput(parameters, self.OUTPUT, context)

        total = 100.0 / source.featureCount() if source.featureCount() else 0
        
        # create a dictionary (I don't handle the obtruse PyQgis ...)
        # dictoinary : fast retrieval 
        features = {f.id(): f.geometry().asPoint()  
                        for f in source.getFeatures() }
        
        index = QgsSpatialIndexKDBush(source.getFeatures())
       
        # open the file in the write mode
        w = open(output, 'w', newline='')

        # create the csv writer
        writer = csv.writer(w)
        
        header = ['internal_id', 'count', 'ellipse_y', 'ellipse_x', 
                        'center_x', 'center_y', 'angle_rad', 'azimuth_geo', 'eccentricity', 'offset']
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
            
             # calcul de la matrice de covariance
                cov = np.cov(x, y) # calcul basé sur (n-1)
                #print cov
                eigenval,eigenvec = np.linalg.eig(cov)
                
                # rayons de l'ellipse (racine carré des valeurs propres)
                sigmay,sigmax = np.sqrt(eigenval)
           
                # angle de l'ellipse à partir de la matrice de covariance
                theta1 = np.arctan((2*cov[:,0][1])/(cov[:,0][0] - cov[:,1][1]))/2
                
                # changement d'axe pour le N géographique 
                theta = 90 - np.rad2deg(theta1) #MARCHE PAS
                """ 
                #POUR MEMOIRE
                # angle de l'ellipse à partir des vecteurs propres 
                theta = 90 - np.rad2deg(np.arccos(eigenvec[0, 0]))#ERREUR ??
                
                # aire de l'ellipse
                aire = np.pi * sigmax * sigmay
                """
                # excentricité de l'ellipse
                exc = np.sqrt(1 - ((min(sigmax,sigmay)**2)/(max(sigmax,sigmay)**2)))
                
                # point to line distance = vector A * vector B = (x−x0)⋅* sin(θ) − (y−y0)⋅* cos(θ)
                
                offset = (xy[0]- x.mean()) * np.sin(theta1) - (xy[1]- y.mean()) * np.cos(theta1) 
                
                output = [f, count, sigmay, sigmax, x.mean(), y.mean(), theta1, theta, exc, abs(offset)]
                
                """
                if cosines  :
                    # do not use raw coordinates : the origin is distant and arbitrary
                    # crop the space to the point cloud
                    x-= np.min(x); y-= np.min(y)
                    # https://stackoverflow.com/questions/18424228/cosine-similarity-between-2-number-lists
                    cos_sim = np.dot(x, y)/(np.linalg.norm(x)*np.linalg.norm(y))
                    output.append(cos_sim)
                """
                
            else: output = [f, count, 0,0,  x.mean(), y.mean(), 0,0,0,0]
            
            writer.writerow(output)
            
                  # Update the progress bar
            feedback.setProgress(int(counter * total))
            counter +=1
 
          
        w.close()
        return {self.OUTPUT: None}