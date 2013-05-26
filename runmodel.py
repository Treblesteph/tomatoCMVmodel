#!/usr/bin/python
# run CMV model varying major assumptive parameters
# usage: runmodel.py [nthreads]
# example: runmodel.py 10

import csv  # for data output
import scipy  # for summary statistics in data output
from scipy import stats  # as above
import itertools  # to generate all parameter combinations
import numpy as np  # for generating decimal ranges of parameters
from multiprocessing import Process, JoinableQueue  # for threaded running of parameter sweep
import sys  # for taking number of threads as command line arg
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


class ModelRunThread(Process):
    """Threaded run of the model"""
    def __init__(self, queue):
        Process.__init__(self)
        self.queue = queue

    def run(self):
        while True:
            # grab parameters from queue
            params = self.queue.get()
            print "running model with params: "
            print params
            # run the model and get data back
            outputdata, manyruns = runmodel(*params)
            # send model data to file writing queues
            for line in outputdata:
                outputQueue.put(line)
            for line in manyruns:
                alldataQueue.put(line)
            # tell queue job is done
            self.queue.task_done()


class DataWritethread(Process):
    """Thread for writing from queue to a single file"""
    def __init__(self, queue, filename, headers=None):
        Process.__init__(self)
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
                outcsv.writerow([x for x in data])


if __name__ == '__main__':
    nthreads = int(sys.argv[1])  # number of threads to use
    print str(nthreads)

    # queue for threads to draw sets of parameters from
    parameterQueue = JoinableQueue()

    # queues for writing data to files
    outputQueue = JoinableQueue()
    alldataQueue = JoinableQueue()

    # generate all necessary parameter range combinations
    # define rangeshead -1
    print "generating parameter rangers"
    r_nbees = np.linspace(1, 101, 3)
    r_attr_inf = np.linspace(0.7, 0.9, 3)
    r_inf_penalty = np.linspace(0, 1, 3)
    r_nb_penalty = np.linspace(0, 1, 3)
    r_nb_inf_penalty = np.linspace(0, 0.5, 3)
    # generate combinations
    ranges = [r_nbees, r_attr_inf, r_inf_penalty, r_nb_penalty, r_nb_inf_penalty]
    params = [x for x in itertools.product(*ranges)]
    print str(len(params)) + " parameter sets will be run"

    # spawn data output threads
    print "spawning threads"
    threads = []
    mainheaders = ['nbees', 'attr_inf', 'inf_penalty', 'nb_penalty', 'nb_inf_penalty', 'season', 'population', 'mean', 'std', 'sem']
    d = DataWritethread(outputQueue, 'parameter_sweep.csv', headers=mainheaders)
    a = DataWritethread(alldataQueue, 'allmodeldata.csv')
    for t in [d, a]:
        t.daemon = True
        t.start()
        threads.append(t)

    # spawn model threads
    for i in range(nthreads):
        t = ModelRunThread(parameterQueue)
        t.daemon = True
        t.start()
        threads.append(t)

    # populate parameter queue with data
    print "running..."
    for paramset in params:
        parameterQueue.put(paramset)

    # wait until all queues have been processed
    for t in threads:
        t.join()
    parameterQueue.join()
    outputQueue.join()
    alldataQueue.join()
    print "done!"
