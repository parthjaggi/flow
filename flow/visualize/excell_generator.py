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

    NOx, CO, CO2, fuel, speed = [], [], [], [], [] 

    # import relevant data from emission file
    for record in csv.DictReader(open(fp)):
        NOx.append(record['NOx'])
        CO.append(record['CO'])
        CO2.append(record['CO2'])      
        fuel.append(record['fuel']) 
        speed.append(record['speed']) 
    fuel = [int(float(i)) for i in fuel] 
    CO =  [int(float(i)) for i in CO] 
    CO2 =  [int(float(i)) for i in CO2] 
    NOx =  [int(float(i)) for i in NOx] 
    speed = [int(float(i)) for i in speed ]

    return  NOx, CO, CO2, fuel, speed


if __name__ == "__main__":


    path = "./flow/examples/sumo/IDM_BCM"                                      # Change every time .. 
    dirs = os.listdir( path )
    av_NOx, av_CO, av_CO2, av_fuel, av_vel, std_vel = [], [], [], [], [], []
    files=[] 
    x = []
    for file in dirs:
        y = file.split('I')
        x.append(int(y[0]))                                                       #change sometimes 
        z = int(y[0])

        files.append(file)
        m = glob.glob("flow/examples/sumo/IDM_BCM/{}IDM_{}BCM/*.csv".format(z,22-z)) #also this 
        file_path = m[0]                      #Also change this 
        NOx, CO, CO2, fuel, speed = import_data_from_emission(file_path)
        av_NOx.append(round(statistics.mean(NOx),3))
        av_CO.append(round(statistics.mean(CO),2) )    
        av_CO2.append( round(statistics.mean(CO2),2)) 
        av_fuel.append(round(statistics.mean(fuel),3) )
        av_vel.append(round(statistics.mean(speed),3) ) 
        std_vel.append(round(statistics.stdev(speed),3) )

    head = ["x","NOx","CO","CO2","fuel","Velocity","std velocity"]
    with open('IDM_BCM', 'a') as csvFile:                             #Also this . . 
        writer = csv.writer(csvFile)
        writer.writerow(x)
        writer.writerow(av_NOx)
        writer.writerow(av_CO)
        writer.writerow(av_CO2)
        writer.writerow(av_fuel)
        writer.writerow(av_vel)
        writer.writerow(std_vel)
        writer.writerow(head)