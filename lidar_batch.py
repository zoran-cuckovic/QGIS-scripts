"""
***************************************************************************
*                    LIDAR BATCH PROCESSING FOR QGIS
*   By Zoran Zoran Čučković @ LandscapeArchaeology.org
GNU licence:
*   This program is free software; you can redistribute it and/or modify  *
*   it under the terms of the GNU General Public License as published by  *
*   the Free Software Foundation; either version 2 of the License, or     *
*   (at your option) any later version.                                   *
*                                                                         *
***************************************************************************
"""

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFile,
                       QgsProcessingParameterString, 
                       QgsProcessingParameterNumber)
from qgis import processing
import os


class ExampleProcessingAlgorithm(QgsProcessingAlgorithm):
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

    INPUT_FOLDER = 'INPUT'
    RESOLUTION = 'RESOLUTION'
    CLASSIFICATION = 'CLASSIFICATION'
    OUTPUT_FOLDER = 'OUTPUT'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return ExampleProcessingAlgorithm()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'lidar_batch'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Lidar batch conversion')

    def group(self):
        """
        Returns the name of the group this algorithm belongs to. This string
        should be localised.
        """
        return self.tr('LandscapeArchaeology')

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
        return self.tr("Batch conversion of lidar files (.las to raster)")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(QgsProcessingParameterFile(
            self.INPUT_FOLDER,
            self.tr("Input folder"),
            behavior=QgsProcessingParameterFile.Folder))
            
        self.addParameter(
            QgsProcessingParameterNumber(
                self.RESOLUTION,
                self.tr('Resolution'),
                QgsProcessingParameterNumber.Double,
                1.0))
        
        self.addParameter(
            QgsProcessingParameterString(
                self.CLASSIFICATION,
                self.tr('Classes'),
                '2,3,4,5,6,7'))
  
        self.addParameter(QgsProcessingParameterFile(
            self.OUTPUT_FOLDER,
            self.tr("Output folder"),
            behavior=QgsProcessingParameterFile.Folder))
        
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsFile(parameters, self.INPUT_FOLDER, context)
        resolution = self.parameterAsDouble(parameters, self.RESOLUTION, context)
        destination =  self.parameterAsFile(parameters, self.OUTPUT_FOLDER, context)
        classification = 'Classification in ( {} )'.format(
            self.parameterAsString(parameters, self.CLASSIFICATION, context))
  
        if source == destination : 
            err= (" \n ****** \n ERROR! \n Destination folder is the same as the raw data folder!")
            feedback.reportError(err, fatalError = True)
            raise QgsProcessingException(err)
            
        input_files = os.listdir(source)
        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / len(input_files)
        count = 1
     

        for f in input_files:
            # Stop the algorithm if cancel button has been clicked
            if feedback.isCanceled():
                break

            full_path = os.path.join(source, f)
            output_file = os.path.join(destination, 
                                    os.path.basename(f) + ".tif")

            if f[-4:] in (".las" ,".laz"): 

                processing.run("pdal:exportraster", {
                    'INPUT': full_path,
                    'ATTRIBUTE' : 'Z',
                    'FILTER_EXPRESSION' : classification, 
                    'RESOLUTION' : resolution,
                    'OUTPUT': output_file 
                })
                print ("Converted file: " +f)
                
            else : print ("Skipped file: " + f) 
            
            # Update the progress bar
            feedback.setProgress(int(count * total))
            count +=1
            
            

        # Return the results of the algorithm. In this case our only result is
        # the feature sink which contains the processed features, but some
        # algorithms may return multiple feature sinks, calculated numeric
        # statistics, etc. These should all be included in the returned
        # dictionary, with keys matching the feature corresponding parameter
        # or output names.
        return {self.OUTPUT_FOLDER: None}
