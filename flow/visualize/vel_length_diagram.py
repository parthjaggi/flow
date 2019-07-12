from flow.utils.rllib import get_flow_params
import csv
from matplotlib import pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.colors as colors
import numpy as np
import os 
import argparse
import glob 
import statistics
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import matplotlib.colors as colors
import matplotlib.patches as patches
import pickle
from scipy.interpolate import griddata

ACCEPTABLE_SCENARIOS = [
    'LoopScenario',
    'Figure8Scenario',
    'MergeScenario',
]

# I only care about the average speed so .. 


def get_average_speed(fp):              #takes file path as input 


 with open(fp) as csvfile: 
     readCSV = csv.reader(csvfile)
     v = [] 
     for row in readCSV:
         v.append(row[3])
     v.remove('speed')  
    
     v = [int(float(i)) for i in v]
     vavg = statistics.mean(v)

 return vavg 



if __name__ == '__main__':
    # create the parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='[Flow] Generates time space diagrams for flow networks.',
        epilog='python time_space_diagram.py </path/to/emission>.csv '
               '</path/to/flow_params>.json')
    """
    # required arguments
    parser.add_argument('dir_path', type=str,
                        help='path to the csv file.')
    """
    # optional arguments
    parser.add_argument('--steps', type=int, default=1,
                        help='rate at which steps are plotted.')
    parser.add_argument('--title', type=str, default='Time Space Diagram',
                        help='rate at which steps are plotted.')
    parser.add_argument('--max_speed', type=int, default=8,
                        help='The maximum speed in the color range.')
    parser.add_argument('--start', type=float, default=0,
                        help='initial time (in sec) in the plot.')
    parser.add_argument('--stop', type=float, default=float('inf'),
                        help='final time (in sec) in the plot.')

    args = parser.parse_args()


    # get the names of all the directories starting with \
    path = "./flow/examples/sumo/IDM,with_noise"
    dirs = os.listdir( path )
    files=[] 
    for file in dirs:
        if file[0]=="l":
          files.append(file)
    x=[]
    y=[]
    z=[]

    for dir_i in files:
        # from the name, extract the length
        total_len = int(dir_i[2]+dir_i[3]+dir_i[4]) 
       
        # from the name, extract v0 
        if len(dir_i)<11:
            v0 = int(dir_i[9])
        else: 
            v0 = int(dir_i[9]+dir_i[10])

        # check for the elements in the dir_i folder and choose the file that ends with .csv
        m = glob.glob("flow/examples/sumo/IDM,with_noise/l={}-v0={}/*.csv".format(total_len,v0))
        file_path = m[0]


        # compute the desired Vel,length,and average speed of vehicles in each simulation 
        x.append(total_len)
        y.append(v0)
        z.append(get_average_speed(file_path))

    #print(len(x))
    #print(len(y))
    #print(len(z)) 


    points = np.stack((y,x)).T
    grid_x, grid_y = np.mgrid[220:5:290, 5:1:31]

    a = griddata(points, z, (grid_x, grid_y))

    plt.figure(figsize=(16,9))
    norm = plt.Normalize(0, 15)
    # plt.title("Velocity Distribution for Vehicles in the Highway", fontsize=25)
    plt.xlabel("length", fontsize=20)
    plt.ylabel("Desired Velocity", fontsize=20)
    plt.imshow(a, extent=(0,3600,0,708), origin='lower', aspect='auto', cmap=my_cmap, norm=norm)
    cbar = plt.colorbar()
    cbar.set_label('Average Velocity (m/s)', fontsize=20)
    cbar.ax.tick_params(labelsize=18)
    plt.xticks(fontsize=18)
    plt.yticks(fontsize=18)
    plt.show()
   


