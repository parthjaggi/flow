import csv
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.colors as colors
import numpy as np
import os 
import argparse
import glob
import statistics

# to get the data needed .. 
def import_data_from_emission(fp):

    NOx, CO, CO2, fuel = [], [], [], [] 

    # import relevant data from emission file
    for record in csv.DictReader(open(fp)):
        PMx.append(record['PMx'])
        CO.append(record['CO'])
        CO2.append(record['CO2'])      
        fuel.append(record['fuel']) 
    fuel = [int(float(i)) for i in fuel] 
    CO =  [int(float(i)) for i in CO] 
    CO2 =  [int(float(i)) for i in CO2] 
    NOx =  [int(float(i)) for i in NOx] 

    return veh_id, NOx, CO, CO2, HC, fuel


if __name__ == "__main__":

path = "./flow/examples/sumo/BCM/"                                      # Change every time .. 
dirs = os.listdir( path )
av_NOx, av_CO, av_CO2, av_fuel = [], [], [], [], []
files=[] 
for file in dirs:
    files.append(file)
    x = str(file)
    fp = "./flow/examples/sumo/BCM/{}".format(x)                        #Also change this 
    NOx, CO, CO2, fuel = import_data_from_emission(fp)
    #av_PMx.append(statistics.mean(PMx))
    av_NOx.append(round(statistics.mean(NOx),3))
    av_CO.append(round(statistics.mean(CO),2) )    
    av_CO2.append( round(statistics.mean(CO2),2)) 
    av_fuel.append(round(statistics.mean(fuel),3) )

head = ["x","NOx","CO","CO2","fuel"]
with open('guestList.csv', 'a') as csvFile:                             #Also this . . 
    writer = csv.writer(csvFile)
    writer.writerow(head)
    writer.writerow(av_NOx)
    writer.writerow(av_CO)
    writer.writerow(av_CO2)
    writer.writerow(av_fuel)