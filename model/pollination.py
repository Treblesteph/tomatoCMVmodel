import random  # for stochastic element of visitation
import itertools  # for medelian crosses using Cartesian product
import csv  # for data output prior to visualisation
from model.consts import *


class PollinationSeason(object):
    # "Model of pollination over a single season with hour time derivative"
    def __init__(self, plant_populations,
                 attraction=DEFAULT_ATTRACTION_INFECTED,
                 flowers_per_plant=STARTING_FLOWERS,
                 max_visit_rate=DEFAULT_MAX_VISIT_RATE,
                 pollination_season=FLOWERING_WINDOW,
                 number_of_bees=NUMBER_OF_BEES,
                 writeresults=False):
        # STATE VARIABLES
        # convert plant population dictionary to flower population dictionary:
        self.flower_populations = dict([[pair, plant_populations[pair] * flowers_per_plant] for pair in plant_populations])
        # initial values
        self.attraction = attraction
        self.max_visit_rate = max_visit_rate
        self.cross_list = dict([[':'.join(x), 0] for x in itertools.product(plant_populations, repeat=2)])
        self.seasonal_visitation = dict([pair, 0] for pair in plant_populations)
        self.pollination_season = pollination_season
        self.number_of_bees = number_of_bees
        # write results to file(s)
        if writeresults:
            # visitation tracking
            self.visitsfile = open('season_visits.csv', 'wb')
            self.visitscsv = csv.writer(self.visitsfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            self.visitscsv.writerow(['hour'] + ['SR', 'SS_u', 'SS_i', 'RR', 'RS'])
        else:
            self.visitscsv = self.visitsfile = None

    def updateDensity(self):
        # update plant density
        self.density = float(self.totalPop() / GREENHOUSE_SIZE)

    def updateVisitRate(self):
        # update bee visit rate
        # self.updateDensity must be called first
        v = (self.max_visit_rate * self.density ** 2) / (100 ** 2 + self.density ** 2)
        self.visit_rate = int(round(v))

    def updateInfectedProb(self):
        infected_prop = self.infectedPop() / float(self.totalPop()) if self.infectedPop() else 0
        uninfected_prop = 1 - infected_prop  # includes resistant and susceptible uninfected
        adjust_infected = infected_prop * self.attraction
        adjust_uninfected = uninfected_prop * (1 - self.attraction)
        self.infected_prob = adjust_infected / (adjust_infected + adjust_uninfected)
        self.uninfected_prob = 1 - self.infected_prob
        self.updateLandingProbs()

    def updateLandingProbs(self):
        self.ssi_prob = self.infected_prob  # SS_i
        noninfected_pop = self.totalPop() - self.infectedPop()
        rr_prop = self.flower_populations['RR'] / float(noninfected_pop) if self.flower_populations['RR'] else 0
        rs_prop = self.flower_populations['RS'] / float(noninfected_pop) if self.flower_populations['RS'] else 0
        sr_prop = self.flower_populations['SR'] / float(noninfected_pop) if self.flower_populations['SR'] else 0
        self.rr_prob = self.infected_prob + (self.uninfected_prob * rr_prop)  # RR
        self.rs_prob = self.rr_prob + (self.uninfected_prob * rs_prop)  # RS
        self.sr_prob = self.rs_prob + (self.uninfected_prob * sr_prop)  # SR
        self.ssu_prob = 1

    def updateAll(self):
        self.updateDensity()
        self.updateVisitRate()
        self.updateInfectedProb()

    def resistantPop(self):
        return sum([self.flower_populations[x] for x in ['RR', 'RS', 'SR']])

    def susceptiblePop(self):
        return sum([self.flower_populations[x] for x in ['SS_i', 'SS_u']])

    def infectedPop(self):
        return self.flower_populations['SS_i']

    def uninfectedPop(self):
        return self.flower_populations['SS_u']

    def totalPop(self):
        return sum(self.flower_populations.values())

    def runOneHour(self):
        # run one iteration of the model
        self.updateAll()
        visitation = dict([[pair, 0] for pair in self.flower_populations])
        # release the bees!
        num_visits = self.visit_rate * self.number_of_bees
        if not num_visits:
            # no flowers left to visit this season
            return
        lastchoice = None
        for x in range(num_visits):
            choice = self.foragingChoice()
            if choice is not None:
                visitation[choice] += 1
                if x and lastchoice is not None:
                    self.storeCross(lastchoice, choice)
                lastchoice = choice
        self.killFlowers(visitation)
        self.updateSeasonalVisitation(visitation)

    def runOneSeason(self):
        # run the model for a season
        self.hour = 1
        while self.hour <= self.pollination_season:
            self.runOneHour()
            self.hour += 1
        if self.visitsfile:
            self.visitsfile.close()
        return [self.seasonal_visitation,
                self.flower_populations,
                self.cross_list]

    def foragingChoice(self):
        # make probabilistic foraging choice
        x = random.random()
        choice = None
        if x < self.ssi_prob:
            choice = 'SS_i'
        elif x < self.rr_prob:
            choice = 'RR'
        elif x < self.rs_prob:
            choice = 'RS'
        elif x < self.sr_prob:
            choice = 'SR'
        elif x < self.ssu_prob:
            choice = 'SS_u'
        return choice if self.flower_populations[choice] > 0 else None

    def storeCross(self, male, female):
        # update cross count for seed model
        self.cross_list[':'.join([male, female])] += 1

    def updateSeasonalVisitation(self, visitation):
        # add hourly visitation to total for selfings in seed model
        if self.visitscsv:
            self.visitscsv.writerow([self.hour] + [visitation[x] for x in visitation])
        for pair in visitation:
            self.seasonal_visitation[pair] += visitation[pair]

    def killFlowers(self, visitation):
        # remove visited flowers from population
        for pair in visitation:
            self.flower_populations[pair] -= visitation[pair]
