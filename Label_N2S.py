##Vector=group
##Input_layer=vector
##Label_field=string 


from PyQt4.QtGui import *
from operator import itemgetter

input = processing.getObject(Input_layer)
provider = input.dataProvider()

# SEE: http://gis.stackexchange.com/questions/97344/how-to-change-attributes-with-qgis-python
updateMap = {}
fieldIdx = provider.fields().indexFromName( Label_field )
if fieldIdx < 0:
    QMessageBox.information(None, "Error","Field does not exist!")
    Exit #This is not correct....
    
features = input.getFeatures()

out=[]
for f in features:
    geom = f.geometry()
    t = geom.asPoint()
    id1 = f.id()
    x, y = t[0], t[1]
    out.append([x,y,id1])
        
# sorting two times : because N-S is reverse, and W-E is not 
# CHANGE SORTING  reverse =True/False FOR OTHER REGIONS / PROJECTION SYSTEMS !!! 
# key 0 = west - east
# key 1 = north-south

out.sort(key=itemgetter(0), reverse=False) #begin sorting with the least important attribute
out.sort(key=itemgetter(1), reverse=True)

i=0
for o in out: 
    i+=1
    id_f=o[2]
    updateMap[id_f] = { fieldIdx: i }

provider.changeAttributeValues( updateMap )