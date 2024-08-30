
from qgis.PyQt.QtCore import QCoreApplication, QVariant

from qgis.core import ( QgsProcessing, QgsProcessingAlgorithm, 
    QgsProcessingParameterFeatureSource,
    QgsProcessingParameterVectorLayer,
	QgsProcessingParameterNumber,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterEnum,
    QgsProcessingParameterFile, 
    QgsProcessingParameterFileDestination)


import networkx as nx
import community
import csv


class ExAlgo(QgsProcessingAlgorithm):

    INPUT = 'INPUT'
    OPTIMAL='OPTIMAL'
    ANALYSIS_TYPE = 'ANALYSIS_TYPE'
    OUTPUT = 'OUTPUT'

    def __init__(self):

        super().__init__()

    def name(self):

        return "network_indices"
   

    def tr(self, text):

        return QCoreApplication.translate("modularity", text)


    def displayName(self):

        return self.tr("Network indices")

    def group(self):

        return self.tr("Landscape Archaeology")

    def groupId(self):

        return "LandscapeArchaeology"

    def shortHelpString(self):

        return self.tr("""Network indices for visibilityu networks. 
                    ATTENTION: only field names 'Source' and 'Target' are accepted. 
        """)

    def helpUrl(self):

        return None
        

    def createInstance(self):

        return type(self)()

    def initAlgorithm(self, config=None):

        self.addParameter(
		QgsProcessingParameterFeatureSource(
            self.INPUT,
            self.tr("Input line layer"), 
            types=[QgsProcessing.TypeVectorLine]))
            
               
        self.addParameter(QgsProcessingParameterEnum(
            self.ANALYSIS_TYPE,
            self.tr('Analysis type'),
            ['Closeness', 'Betweenness', 'Modularity'],
            defaultValue=0))
        
             
        self.addParameter(
        QgsProcessingParameterFileDestination(
            self.OUTPUT,
            self.tr("Output"),
            fileFilter = ".csv" ))
        # The name in fileFilter has been deduced from list of filters from execution of 
        # QgsVectorFileWriter.fileFilterString(QgsVectorFileWriter.VectorFormatOptions())
            
    def processAlgorithm(self, parameters, context, feedback):
        
        layer = self.parameterAsSource(parameters, self.INPUT, context)
        
        optimal = self.parameterAsBool(parameters, self.OPTIMAL, context)
        analysis_type = self.parameterAsInt(parameters, self.ANALYSIS_TYPE, context)
        
        output = self.parameterAsString(parameters, self.OUTPUT, context)
        
        G = nx.Graph()
        for f in layer.getFeatures():  
            G.add_edge( f['Source'], f['Target']) 
        
        if analysis_type == 0 :
            out = nx.closeness_centrality(G)
            field = 'closenness'
        elif analysis_type == 1:
            out = nx.betweenness_centrality(G)
            field = 'betweenness'
        elif analysis_type == 2 :
            out = community.best_partition(G)
            field = 'group'
            
     
        with open(output, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file, delimiter = ';')
            writer.writerow (['node',field])
            # writer.writeheader()
            for i in out : writer.writerow ([i, out[i] ])#     (str(i), str(p[i])) 
            csv_file = None
            
        return {self.OUTPUT: None}
