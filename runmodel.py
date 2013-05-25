#!/usr/bin/env python
# run CMV model varying major assumptive parameters
# usage: runmodel.py [nthreads]
# example: runmodel.py 10

import csv  # for data output
import scipy  # for summary statistics in data output
from scipy import stats  # as above
import itertools  # to generate all parameter combinations
import numpy as np  # for generating decimal ranges of parameters
import threading  # for threaded running of parameter sweep
import sys  # for taking number of threads as command line arg
from multiprocessing import Queue  # as previous
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
        print 'run: ' + str(i + 1)
        for j in range(1, x+1):
            # create pollination season model
            p = PollinationSeason(plant_populations=plantpops,
                                  number_of_bees=nbees,
                                  attraction=attr_inf)
            # run pollination season
            pres = p.runOneSeason()
            # create reproduction model
            r = Reproduction(*pres,
                             infected_penalty=inf_penalty,
                             non_buzz_penalty=nb_penalty,
                             non_buzz_infected_penalty=nb_inf_penalty)
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


class ModelRunThread(threading.Thread):
    """Threaded run of the model"""
    def __init__(self, queue):
        threading.Thread.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # grab parameters from queue
            params = self.queue.get()
            # run the model and get data back
            outputdata, manyruns = runmodel(*params)
            # send model data to file writing queues
            outputQueue.put(manyruns)
            alldataQueue.put(outputdata)
            # tell queue job is done
            self.queue.task_done()


class DataWritethread(threading.Thread):
    """Thread for writing from queue to a single file"""
    def __init__(self, queue, filename, headers=None):
        threading.Thead.__init__(self)
        self.queue = queue
        self.filename = filename
        self.headers = headers

    def run(self):
        with open(self.filename, 'wb') as outfile:
            outcsv = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            if self.headers is not None:
                outcsv.writerow(self.headers)
            while True:
                # grab data from queue
                data = self.queue.get()
                # write to file
                outcsv.writerow(data)


# queue for threads to draw sets of parameters from
parameterQueue = Queue.Queue()

# queues for writing data to files
outputQueue = Queue.Queue()
alldataQueue = Queue.Queue()


def main():
    nthreads = sys.argv[1]  # number of threads to use
    # generate all necessary parameter range combinations
    # define ranges
    r_nbees = np.arange(1, 101, 50)
    r_attr_inf = np.arange(0.5, 1.0, 0.25)
    r_inf_penalty = np.arange(0, 1, 0.5)
    r_nb_penalty = np.arange(0, 1, 0.5)
    r_nb_inf_penalty = np.arange(0, 0.5, 0.25)
    # generate combinations
    ranges = [r_nbees, r_attr_inf, r_inf_penalty, r_nb_penalty, r_nb_inf_penalty]
    params = [x for x in itertools.product(*ranges)]

    # spawn data output threads
    mainheaders = ['nbees', 'attr_inf', 'inf_penalty', 'nb_penalty', 'nb_inf_penalty', 'season', 'population', 'mean', 'std', 'sem']
    d = DataWritethread(outputQueue, 'parameter_sweep.csv', mainheaders)
    a = DataWritethread(alldataQueue, 'allmodeldata.csv')
    for t in [d, a]:
        t.setDaemon(True)
        t.start()

    # spawn model threads
    for i in range(nthreads):
        t = ModelRunThread(parameterQueue)
        t.setDaemon(True)
        t.start()

    # populate parameter queue with data
    for paramset in params:
        parameterQueue.put(paramset)

    # wait until all queues have been processed
    parameterQueue.join()
    outputQueue.join()
    alldataQueue.join()
