#!/usr/bin/python
# run CMV model varying major assumptive parameters
# usage: runmodel.py [nthreads]
# example: runmodel.py 10

import csv  # for data output
import scipy  # for summary statistics in data output
from scipy import stats  # as above
from model.pollination import PollinationSeason
from model.reproduction import Reproduction


def runmodel(nbees, attr_inf, inf_penalty, nb_penalty, nb_inf_penalty):
    # define starting population
    plantpops = {'RR': 500, 'RS': 0, 'SR': 0, 'SS_i': 250, 'SS_u': 250}
    # run over x seasons with y repeats and write otuput to file
    x = 500  # 500 seasons
    y = 3  # 3 repeats
    manyruns = [[] for i in range(x + 1)]  # this holds the data from multiple runs
    manyruns[0].append(plantpops)
    p = r = None
    for i in range(y):
        # do repeats
        for j in range(1, x+1):
            # create pollination season model
            p = PollinationSeason(plant_populations=plantpops,
                                  number_of_bees=int(nbees),
                                  attraction=float(attr_inf))
            # run pollination season
            pres = p.runOneSeason()
            # create reproduction model
            r = Reproduction(*pres,
                             infected_penalty=float(inf_penalty),
                             non_buzz_penalty=float(nb_penalty),
                             non_buzz_infected_penalty=float(nb_inf_penalty))
            # run reproduction
            plantpops = r.generatePlantPop()
            # save the data
            manyruns[j].append(plantpops)
    outputdata = []
    for season, counts in enumerate(manyruns):
        # aggregate susceptible and resistant
        s = [z['SS_i'] + z['SS_u'] for z in counts]
        r = [z['RR'] + z['RS'] + z['SR'] for z in counts]
        # calculate summary stats for plotting later
        s_mean = scipy.mean(s)
        s_std = scipy.std(s)
        s_stderr = 0 if season == 0 else stats.sem(s)
        r_mean = scipy.mean(r)
        r_std = scipy.std(r)
        r_stderr = 0 if season == 0 else stats.sem(r)
        # write to CSV in 'long' table format
        outputdata.append([nbees, attr_inf, inf_penalty, nb_penalty, nb_inf_penalty, season, 'susceptible', s_mean, s_std, s_stderr])
        outputdata.append([nbees, attr_inf, inf_penalty, nb_penalty, nb_inf_penalty, season, 'resistant', r_mean, r_std, r_stderr])
    return outputdata, manyruns


if __name__ == '__main__':
    defaults = {'nbees': 10, 'attr_inf': 0.81, 'inf_penalty': 0.36,
                'nb_penalty': 0.74, 'nb_inf_penalty': 0.09}
    keyorder = ['nbees', 'attr_inf', 'inf_penalty', 'nb_penalty', 'nb_inf_penalty']
    params = [defaults[x] for x in keyorder]
    outputdata, manyruns = runmodel(*params)
    with open('default_500_seasons.csv', 'wb') as outfile:
        outcsv = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for x in outputdata:
            outcsv.writerow(x)
