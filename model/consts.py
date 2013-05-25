# Parameters - those marked with *** should be included in sensitivity analysis from (x:y)
GREENHOUSE_SIZE = 1000  # area of greenhouse in m2 (assuming all flowers on single plane)
NUMBER_OF_BEES = 10  # *** (1:101, step 50, n=3) number of forager bees (active pollinators)
FLOWERING_WINDOW = 640  # 40 days at 16hour light cycles (artificial)
STARTING_FLOWERS = 40  # number of flowers per plant at start of season
DEFAULT_ATTRACTION_INFECTED = 0.81  # *** (0.5:1.0, step 0.25, n=3) derived from experiments - will be changable in class (for sensitivity analysis)
DEFAULT_MAX_VISIT_RATE = 60  # maximum number of visits per hour assumed to be 1 per minute (estimated based on time spent in each flower and colony visits)
PLANTTYPES = ['RR', 'RS', 'SR', 'SS_i', 'SS_u']
INF_PENALTY = 0.36  # *** (0:1, step 0.5, n=3) increase of seed death rate due to infected mother
NON_BUZZ_PENALTY = 0.74  # *** (0:1, step 0.5, n=3) increase of seed death rate due to non-buzz pollination
NON_BUZZ_INF_PENALTY = 0.09  # *** (0:0.5, step 0.25, n=3)
SEEDS_SOWN = 1000  # number of seeds the farmer sows each year
SUSCEPTIBLE_PLANT_INFECTION_RATE = 0.5
