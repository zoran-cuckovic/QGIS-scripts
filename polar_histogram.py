# -*- coding: utf-8 -*-

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

from qgis.PyQt.QtCore import QCoreApplication
from qgis.core import (QgsProcessing,
                       QgsFeatureSink,
                       QgsProcessingException,
                       QgsProcessingAlgorithm,
                       QgsProcessingParameterFeatureSource,
                       QgsProcessingParameterString, 
                       QgsProcessingParameterNumber, 
                       QgsProcessingParameterBoolean,
                       QgsProcessingParameterFileDestination
                       )
from qgis import processing

import numpy as np
import matplotlib.pyplot as plt

# NOT USED
from PyQt5 import QtWidgets


class PolarHistogram(QgsProcessingAlgorithm):
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
    TABLE_FIELD= 'TABLE_FIELD'
    BIN_COUNT = 'BIN_COUNT'
    HOLLOW_RADIUS = 'HOLLOW_RADIUS'
    COLOUR_RATIO = 'COLOUR_RATIO'
    CENTRED = 'CENTRED'
    PERCENTAGE = 'PERCENTAGE'
    STACK = 'STACK'
    OUTPUT = 'OUTPUT'
    SVG = 'SVG'

    def tr(self, string):
        """
        Returns a translatable string with the self.tr() function.
        """
        return QCoreApplication.translate('Processing', string)

    def createInstance(self):
        return PolarHistogram()

    def name(self):
        """
        Returns the algorithm name, used for identifying the algorithm. This
        string should be fixed for the algorithm, and must not be localised.
        The name should be unique within each provider. Names should contain
        lowercase alphanumeric characters only and no spaces or other
        formatting characters.
        """
        return 'myscript'

    def displayName(self):
        """
        Returns the translated algorithm name, which should be used for any
        user-visible display of the algorithm name.
        """
        return self.tr('Polar histogram')

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
        return self.tr("Example algorithm short description")

    def initAlgorithm(self, config=None):
        """
        Here we define the inputs and output of the algorithm, along
        with some other properties.
        """

        self.addParameter(
            QgsProcessingParameterFeatureSource(
                self.INPUT,
                self.tr('Vector layer')
            )
        )
        
        self.addParameter(
            QgsProcessingParameterString(
                self.TABLE_FIELD,
                self.tr('Field containing values'),
                'azimuth')
            
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.BIN_COUNT,
                self.tr('Number of bins'),
                QgsProcessingParameterNumber.Integer,
                16)
            
        )
        
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.HOLLOW_RADIUS,
                self.tr('Hollow radius'),
                QgsProcessingParameterNumber.Integer,
                0)
            
        )
        
        self.addParameter(
            QgsProcessingParameterNumber(
                self.COLOUR_RATIO,
                self.tr('Colour ratio'),
                QgsProcessingParameterNumber.Integer,
                1)
            
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.CENTRED,
                self.tr('Center on axis')
                ) 
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.PERCENTAGE,
                self.tr('Express as percentage')
                ) 
        )
        

        self.addParameter(
            QgsProcessingParameterBoolean(
                self.STACK,
                self.tr('Stack (leave open for the next graph)')
                )
            
        )
        
        self.addParameter(
            QgsProcessingParameterFileDestination(
                self.OUTPUT,
                self.tr('Output image'),
                '*.png' 
                )
            
        )
        
        self.addParameter(
            QgsProcessingParameterBoolean(
                self.SVG,
                self.tr('Vector (.svg) output')
                ) 
        )
    # https://stackoverflow.com/questions/29357442/example-of-embedding-matplotlib-in-pyqt5/29791498#29791498
    # NOT USED !
    def addmpl(self, fig):
        self.canvas = FigureCanvas(fig)
        self.mplvl.addWidget(self.canvas)
        self.canvas.draw()
        
    def processAlgorithm(self, parameters, context, feedback):
        """
        Here is where the processing itself takes place.
        """
               
        data = [] # using a list, slow but it works fine...

        # Retrieve the feature source and sink. The 'dest_id' variable is used
        # to uniquely identify the feature sink, and must be included in the
        # dictionary returned by the processAlgorithm function.
        source = self.parameterAsSource(parameters, self.INPUT, context)
        
        output = self.parameterAsFileOutput(parameters,self.OUTPUT, context)
        
        azimuth_field =  self.parameterAsString( parameters,self.TABLE_FIELD, context)
        bin_count = self.parameterAsInt( parameters,self.BIN_COUNT, context)
        hollow_radius = self.parameterAsInt( parameters,self.HOLLOW_RADIUS, context)
        colour_ratio = self.parameterAsInt( parameters,self.COLOUR_RATIO, context)
        centred = self.parameterAsBool(parameters,self.CENTRED, context)
        percentage = self.parameterAsBool(parameters,self.PERCENTAGE, context)
        stack = self.parameterAsBool(parameters,self.STACK, context)
        
        svg = self.parameterAsBool(parameters,self.SVG, context)
        if svg : output = output[:-3:] + 'svg'

        # If source was not found, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSourceError method to return a standard
        # helper text for when a source cannot be evaluated
        if source is None:
            raise QgsProcessingException(self.invalidSourceError(parameters, self.INPUT))

        if azimuth_field not in source.fields().names(): 
            raise QgsProcessingException(azimuth_field + " field doesn't exist !")
            
        # Send some information to the user
        # feedback.pushInfo('CRS is {}'.format(source.sourceCrs().authid()))

        # If sink was not created, throw an exception to indicate that the algorithm
        # encountered a fatal error. The exception text can be any string, but in this
        # case we use the pre-built invalidSinkError method to return a standard
        # helper text for when a sink cannot be evaluated
        
        #if sink is None:
         #   raise QgsProcessingException(self.invalidSinkError(parameters, self.OUTPUT))

        # Compute the number of steps to display within the progress bar and
        # get features from source
        total = 100.0 / source.featureCount() if source.featureCount() else 0
        
        out = [] #lists are slow, but they work...

        features = source.getFeatures()

        for current, feature in enumerate(features):
            # Add a feature
            v = feature[azimuth_field]
            # Attention : only the 0 - 360 range is accepted !!
            if 0<=v<=360:  out += [v]
                

        # the following code is mostly adapted from : 
        # http://stackoverflow.com/questions/22562364/circular-histogram-for-python
        N = bin_count
        theta = np.linspace(0,  2 * np.pi, N, endpoint=False)
        radii, labels = np.histogram (np.array(out), 
                                      bins = np.linspace(
                                                0, 360, N+1, endpoint=True))
                                                
        if percentage : radii = radii / len(out) * 100
        
        width = 2*np.pi  / N
        
        if not centred : theta += width/2

        ax = plt.subplot(111, polar=True)
        #put north to top , arrange clockwise, give geographic labels (instead of angles)
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_xticklabels(['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'])
        
        
        bars = ax.bar(theta, radii, width=width,bottom=hollow_radius)# 
     
        # Use custom colors and opacity
        
        """
        for r, bar in zip(radii, bars):
            bar.set_facecolor(plt.cm.jet(r / 10.))
            bar.set_alpha(0.8)
        """
        # plt.show()
               
  #     savefig(fname, dpi=None, facecolor='w', edgecolor='w',
   #     orientation='portrait', papertype=None, format=None,
      #  transparent=False, bbox_inches=None, pad_inches=0.1,
       # frameon=None, metadata=None)
        plt.savefig(output) #, dpi = 72, format ='png
        
        
        
        if not stack : # This is a very poor hack - do not clear to stack graphs
        # Matplotlib handels poorly class instances, they stay alive after execution
            plt.clf()
            plt.cla()
            plt.close()

        return {self.OUTPUT: output}
