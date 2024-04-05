# Importing the required libraries
import random

import numpy as np
import simpy
from tqdm import tqdm

RANDOM_SEED = 1990
NO_SIMULATIONS = 50
SIM_TIME = 24 * 60 * 60
WARMUP_TIME = 1 * 60 * 60
CUST_INTER_ARR_MIN = 1
CUST_INTER_ARR_MAX = 2
PRINTING = False

thruput_simulation = []  # Throughput
ct_replication = []  # Cycle time
wt_replication = []  # Wait time
ct_simulation = []
wt_simulation = []


# Defining the 'customer' process
def customer(env, name, atm):
    # Customer arrives and requests the ATM
    customer_enter_time = env.now
    if PRINTING:
        print(f"{name}: Arrives at time: {env.now:.2f}")
    with atm.request() as atm_req:
        yield atm_req
        customer_got_atm = env.now
        # Customer gets the ATM
        if PRINTING:
            print(f"{name}: gets ATM machine at time: {env.now:.2f}")
        # Customer enters details
        yield env.timeout(30)
        if PRINTING:
            print(f"{name}: Details entered at time: {env.now:.2f}")
        # Customer retrieves cash
        yield env.timeout(60)
        if PRINTING:
            print(f"{name}: Cash retrieved at time: {env.now:.2f}")

    if env.now > WARMUP_TIME:
        wt_replication.append(customer_got_atm - customer_enter_time)
        ct_replication.append(env.now - customer_enter_time)


# Defining the 'customer_generator' process
def customer_generator(env, atm):
    cust_number = 1
    while True:
        # Generate a random inter-arrival time
        random_inter_arrival_time = (
            random.uniform(CUST_INTER_ARR_MIN, CUST_INTER_ARR_MAX) * 60
        )
        yield env.timeout(random_inter_arrival_time)
        # Process the customer
        env.process(customer(env, f"customer {cust_number}", atm))
        cust_number += 1


for r in tqdm(range(NO_SIMULATIONS)):
    # Seed for random number generator for reproducibility
    random.seed(r)

    # Create an environment and start the setup process
    env = simpy.Environment()
    atm = simpy.Resource(env, capacity=1)
    env.process(customer_generator(env, atm))

    # Execute the simulation
    env.run(until=SIM_TIME)  # 10 minutes
    # break

    num_customers = len(ct_replication)
    wt_simulation.append(np.mean(wt_replication))
    ct_simulation.append(np.mean(ct_replication))
    thruput_simulation.append(num_customers / (SIM_TIME - WARMUP_TIME))

    ct_replication = []
    wt_replication = []

print(
    f"Average Cycle Time: {np.mean(ct_simulation)/60 :.2f} minutes +/- {np.std(ct_simulation)/60 :.2f} minutes"
)
print(
    f"Average Waiting Time: {np.mean(wt_simulation)/60 :.2f} minutes +/- {np.std(wt_simulation)/60 :.2f} minutes"
)
print(
    f"Average Throughput: {np.mean(thruput_simulation)*60*60 :.2f} customers/hour +/- {np.std(thruput_simulation)*60*60 :.2f} customers/hour"
)
