from matplotlib import pyplot as plt
import numpy as np
import matplotlib as mpl

import matplotlib.font_manager as fm

fe = fm.FontEntry(
    fname='Spinnaker-Regular.ttf',
    name='Spinnaker')
fm.fontManager.ttflist.insert(0, fe)
mpl.rcParams['font.family'] = fe.name


'''def x_center_of_mass_graph(data, mode='X'):
    """
    Plots multiple centers of mass depending on the time.

    Data: array of triples [[x_center_of_mass, time], [x_center_of_mass, time], ...]
    The function graphs all the certers of mass depending on time
    Make a cool line graph
    """
    
    # Extract x_center_of_mass and time from the data
    x_center_of_mass = data[:, 0]
    time = data[:, 1]

    # Make a cool line graph in dark mode

    plt.style.use('dark_background')
    plt.figure(figsize=(10, 6))
    plt.plot(time, x_center_of_mass, marker='o', linestyle='-', color='cyan', markersize=5)
    plt.title(f'Center of Mass In {mode} Over Time', fontsize=16, color='white')
    plt.xlabel('Time', fontsize=14, color='white')
    plt.ylabel('Center of Mass', fontsize=14, color='white')
    plt.grid(color='gray', linestyle='--', linewidth=0.5)
    plt.xticks(color='white')
    plt.yticks(color='white')
    plt.gca().set_facecolor('black')
    plt.gcf().patch.set_facecolor('black')
    plt.tight_layout()

    return plt'''

"""
Same function, but to support Y and X axis as the same time (side by side)
"""
def center_of_mass_graph(data_x=None, data_y=None):
    x_center_of_mass = data_x[:, 0] if data_x is not None else None
    y_center_of_mass = data_y[:, 0] if data_y is not None else None
    time = data_x[:, 1] if data_x is not None else data_y[:, 1]

    maxValue = max(max(x_center_of_mass) if data_x is not None else 0, max(y_center_of_mass) if data_y is not None else 0)
    minValue = min(min(x_center_of_mass) if data_x is not None else 0, min(y_center_of_mass) if data_y is not None else 0)

    # Round slightly to the nearest 0.025
    limitMax = round(maxValue + 0.025, 2)
    limitMin = round(minValue - 0.025, 2)

    yLimits = [limitMin, limitMax]
    xLimits = [0, len(time)]

    # Setup steps that are divisors of the limits
    yStep = 0.005
    xStep = 100

    # make two graphs (or 1 if one of them is None)
    nbGraphs = 2 if data_x is not None and data_y is not None else 1

    if nbGraphs == 1:
        name = 'X' if data_x is not None else 'Y'
        center_mass_data = x_center_of_mass if data_x is not None else y_center_of_mass
        #plt.plot(time, center_mass_data, marker='o', linestyle='-', color='cyan', markersize=5)
        plt.title(f'Center of Mass In {name} Over Time', fontsize=16, color='white')
        plt.xlabel('Time', fontsize=14, color='white')
        plt.ylabel(f'{name} Center of Mass', fontsize=14, color='white')
        plt.grid(color='gray', linestyle='--', linewidth=0.5)
        plt.xticks(color='white')
        plt.yticks(color='white')
        plt.gca().set_facecolor('black')
        plt.gcf().patch.set_facecolor('black')
    
    else:
        fig, ax = plt.subplots(1, 2, figsize=(12, 6), sharey=True)
        for i in range(2):
            name = 'X' if i == 0 else 'Y'
            center_mass_data = x_center_of_mass if i == 0 else y_center_of_mass
            #ax[i].plot(time, center_mass_data, marker='o', linestyle='-', color='cyan', markersize=5)
            ax[i].set_title(f'Center of Mass In {name} Over Time', fontsize=16, color='white')
            ax[i].set_xlabel('Time', fontsize=14, color='white')
            ax[i].set_ylabel(f'{name} Center of Mass', fontsize=14, color='white')
            ax[i].grid(color='gray', linestyle='--', linewidth=0.5)
            ax[i].tick_params(axis='both', colors='white')
            ax[i].set_facecolor('black')
            ax[i].set_xticks(np.arange(xLimits[0], xLimits[1], xStep))
            ax[i].set_yticks(np.arange(yLimits[0], yLimits[1], yStep))
            ax[i].set_xlim(*xLimits)
            ax[i].set_ylim(*yLimits)
        
        # Set the figure background color
        fig.patch.set_facecolor('black')
        fig.patch.set_alpha(0.8)
        fig.suptitle('Center of Mass Over Time', fontsize=20, color='white')

        # link the dots with lines
        for i in range(nbGraphs):
            if nbGraphs == 1:
                center_mass_data = x_center_of_mass if data_x is not None else y_center_of_mass
            else:
                center_mass_data = x_center_of_mass if i == 0 else y_center_of_mass
            ax[i].plot(time, center_mass_data, linestyle='-', color='cyan', markersize=5, linewidth=4)
            ax[i].set_xlim(*xLimits)
            ax[i].set_ylim(*yLimits)

    plt.style.use('dark_background')
    plt.tight_layout()
    return plt


def load_data(file_path):
    """
    File path: center_of_mass_data.txt
    First line: Xcenter time Xcenter time ... (the time is the index) - spaces as separators
    Second line: Ycenter time Ycenter time ... (the time is the index)
    Output wanted: 2 lists
    [[Xcenter, time], [Xcenter, time], ...] and [[Ycenter, time], [Ycenter, time], ...]
    """
    x_data = []
    y_data = []
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            data = line.split()
            if len(data) == 0:
                continue
            modified_data = [float(i) for i in data]
            data = [modified_data[i:i+2] for i in range(0, len(modified_data), 2)]
            if len(x_data) == 0:
                x_data = data
            else:
                y_data = data
                break
    
    return np.array(x_data), np.array(y_data)


if __name__ == "__main__":
    data_x, data_y = load_data('center_of_mass_data.txt')

    plt = center_of_mass_graph(data_x, data_y)
    plt.show()
