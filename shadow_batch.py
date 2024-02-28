import csv
import processing

# ATTENTION  : cahnge \ to / for Windows folder structure

# .csv table with three values : output name, azimuth, sun height angle
# first line is skipped (header)
my_table= 'C:/_______/parameters_table.csv' 

# choose your .csv delimiter
table_delimiter = ';' 

my_dem = 'C:/______/myfile.tif'
output_folder = 'C:/____/shadows/' # must be existent 

with open(my_table, newline='') as csvfile:
    spamreader = csv.reader(csvfile, delimiter=';')
    
    next(spamreader, None)  # skipping the header
   
    for row in spamreader:
        
        name,azim, height = row # supposing you only have two values per row
       
        processing.run("terrain_shading:Shadow depth", {'INPUT':my_dem,
                'DIRECTION': int(azim),
                'ANGLE':float(height),
                'SMOOTH':True,
                'OUTPUT':output_folder + str(name) + '.tif'})
