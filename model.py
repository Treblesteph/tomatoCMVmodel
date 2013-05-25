import random
import itertools
import csv
import math
import scipy
from scipy import stats

# Parameters
GREENHOUSE_SIZE = 1000  # area of greenhouse in m2 (assuming all flowers on single plane)
NUMBER_OF_BEES = 10  # number of forager bees (active pollinators)
FLOWERING_WINDOW = 640  # 40 days at 16hour light cycles (artificial)
STARTING_FLOWERS = 40  # number of flowers per plant at start of season
DEFAULT_ATTRACTION_INFECTED = 0.81  # derived from experiments - will be changable in class (for sensitivity analysis)
DEFAULT_MAX_VISIT_RATE = 60  # maximum number of visits per hour assumed to be 1 per minute (estimated based on time spent in each flower and colony visits)
PLANTTYPES = ['RR', 'RS', 'SR', 'SS_i', 'SS_u']
INF_PENALTY = 0.36  # increase of seed death rate due to infected mother
NON_BUZZ_PENALTY = 0.74  # increase of seed death rate due to non-buzz pollination
NON_BUZZ_INF_PENALTY = 0.09
SEEDS_SOWN = 1000
SUSCEPTIBLE_PLANT_INFECTION_RATE = 0.5


class PollinationSeason(object):
    # "Model of pollination over a single season with hour time derivative"
    def __init__(self, plant_populations,
                 attraction=DEFAULT_ATTRACTION_INFECTED,
                 flowers_per_plant=STARTING_FLOWERS,
                 max_visit_rate=DEFAULT_MAX_VISIT_RATE,
                 pollination_season=FLOWERING_WINDOW,
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
        num_visits = self.visit_rate * NUMBER_OF_BEES
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


class Reproduction(object):
    # Model of reproduction following a single season of pollination
    def __init__(self,
                 seasonal_visitation,
                 flower_populations,
                 cross_list,
                 infected_penalty=INF_PENALTY,
                 non_buzz_penalty=NON_BUZZ_PENALTY,
                 non_buzz_infected_penalty=NON_BUZZ_INF_PENALTY):
        self.seasonal_visitation = seasonal_visitation
        self.flower_populations = flower_populations
        self.cross_list = cross_list
        self.seed_populations = dict([[x, 0] for x in ['RR', 'RS', 'SR', 'SS']])
        self.infected_penalty = infected_penalty
        self.non_buzz_penalty = non_buzz_penalty
        self.non_buzz_infected_penalty = non_buzz_infected_penalty

    def updateSeedPop(self):
        # recorded crosses
        for parents, count in self.cross_list.items():
            father, mother = parents.split(':')
            # seed counts are modified for infected mothers
            seed_count = self.seedCount(count, mother == 'SS_i')
            # alleles disregard infection information
            fallele, mallele = [x.rstrip('_iu') for x in [father, mother]]
            # perform mendelian cross
            self.mendelianCross(fallele, mallele, seed_count)
        # selfing
        for planttype, count in self.flower_populations.items():
            father, mother = planttype, planttype
            # seed counts modified for non-buzzing and infected mothers
            seed_count = self.seedCount(count, mother == 'SS_i', buzz=False)
            # alleles disregard infection information
            # alleles disregard infection information
            fallele, mallele = [x.rstrip('_iu') for x in [father, mother]]
            # perform mendelian cross
            self.mendelianCross(fallele, mallele, seed_count)

    def generatePlantPop(self):
        self.updateSeedPop()
        # generate plant population using germination
        seedsassigned = 0
        allelestoassign = self.seed_populations.keys()
        self.plant_populations = dict([[x, 0] for x in self.seed_populations])
        for allele, count in self.seed_populations.items():
            remaining_seed_pop = dict([[x, self.seed_populations[x]] for x in allelestoassign])
            seedsplanted = round((1000 - seedsassigned) * self.getSeedProp(allele, remaining_seed_pop))
            self.plant_populations[allele] += seedsplanted
            seedsassigned += seedsplanted
            allelestoassign.remove(allele)
        self.plant_populations['SS_i'] = int(round(self.plant_populations['SS'] / 2))
        self.plant_populations['SS_u'] = self.plant_populations['SS'] - self.plant_populations['SS_i']
        del(self.plant_populations['SS'])
        return self.plant_populations

    def getSeedProp(self, allele, pop):
        n = pop[allele]
        tot = float(sum(pop.values()))
        prop = n / tot if n and tot else 0
        return prop

    def seedCount(self, count, infected, buzz=True):
        # modify seed increment count if the mother was infected
        if buzz:
            if infected:
                return round(count - count * self.infected_penalty)
            else:
                return count
        else:
            selfcount = count * self.non_buzz_penalty
            if infected:
                selfcount = selfcount * self.non_buzz_infected_penalty
            return selfcount

    def mendelianCross(self, fallele, mallele, seed_count):
        offspring = set([''.join(y) for y in itertools.product(fallele, mallele)])
        counted = 0
        ncounted = 0
        for o in offspring:
            count = int(self.randomRound(seed_count - counted, len(offspring) - ncounted))
            self.seed_populations[o] += count
            counted += count
            ncounted += 1

    def randomRound(self, i, n):
        # for n offspring possibilities and i counts to share
        # return the division of i that the current offspring
        # will receive, fairly rounded
        if n == 1:
            # no need to round
            return i
        else:
            # perform fair rounding
            x = random.random()
            c = i / float(n)
            return math.floor(c) if x < 1 / float(n) else math.ceil(c)


# unvisited flowers are passed to seed model (for selfing)

plantpops = {'RR': 500, 'RS': 0, 'SR': 0, 'SS_i': 250, 'SS_u': 250}
# run over x seasons with y repeats and write otuput to file
x = 1000
y = 10
manyruns = [[]] * (x + 1)  # this holds the data from multiple runs
with open(str(x) + '_seasons.csv', 'wb') as outfile:
    outcsv = csv.writer(outfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
    outcsv.writerow(['season'] + ['S_mean', 'S_std', 'S_stderr', 'R_mean', 'R_std', 'R_stderr'])
    manyruns[0].append(plantpops)
    pollination = reproduction = None
    for i in range(y):
        print 'run: ' + str(i)
        for j in range(1, x+1):
            if j % 100 == 0:
                print 'season: ' + str(j)
            pollination = PollinationSeason(plant_populations=plantpops)
            pres = pollination.runOneSeason()
            reproduction = Reproduction(*pres)
            plantpops = reproduction.generatePlantPop()
            manyruns[j].append(plantpops)
    for season, counts in enumerate(manyruns):
        s = [z['SS_i'] + z['SS_u'] for z in counts]
        r = [z['RR'] + z['RS'] + z['SR'] for z in counts]
        s_mean = scipy.mean(s)
        s_std = scipy.std(s)
        s_stderr = stats.sem(s)
        r_mean = scipy.mean(r)
        r_std = scipy.std(r)
        r_stderr = stats.sem(r)
        outcsv.writerow([season, s_mean, s_std, s_stderr, r_mean, r_std, r_stderr])
