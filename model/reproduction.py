import random  # for stochastic element of visitation
import itertools  # for medelian crosses using Cartesian product
import math  # for floor and ceil in rounding
from model.consts import *


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
                # NOTE: infected mother penalty currently does not
                # apply when calculating non-buzzed seed numbers...
                # perhaps we need to apply the maternal penalty first?
                # or does the non-buzz-infected-penalty already account for that?
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
