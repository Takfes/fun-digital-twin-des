import random

import simpy

# GENERIC CONFIGURATION
PRINTING = True
RANDOM_SEED = 1990
NO_CASHIERS = 2

# TIMINGS CONFIGURATION
CUST_INTER_ARR_RATE = 0.5
CUST_PATIENCE_TIME = 10
MILK_REQUEST_MIN = 1
MILK_REQUEST_MAX = 5

# FRIDGE CONFIGURATION
NO_FRIDGES = 1
FRIDGE_CAPACITY = 50
FRIDGE_LEVEL = 15
FRIDGE_REPLENISH_TIME_MIN = 10
FRIDGE_REPLENISH_TIME_MAX = 20
FRIDGE_REPLENISH_MIN_LEVEL = 5
FRIDGE_REPLENISH_DURATION = 2

# SIMULATION CONFIGURATION
SIM_TIME = 1 * 24 * 60  # MINUTES
# NO_SIMULATIONS = 10
# WARMUP_TIME = 5  # MINUTES

# stats = {
#     "customer_lost": 0,
#     "customer_lost_iter": [],
#     "customer_lost_experiment": [],
# }


def customer(env, name, cashiers, fridge):
    milk_required = random.randint(MILK_REQUEST_MIN, MILK_REQUEST_MAX)
    if PRINTING:
        print(
            f"{name}: Arrives at time: {env.now:.2f}, and requires {milk_required}L milk."
        )

    with fridge["resource"].request() as fridge_req:
        res = yield fridge_req | env.timeout(CUST_PATIENCE_TIME)
        if fridge_req in res:
            yield env.timeout(milk_required)
            yield fridge["milk_container"].get(milk_required)
        else:
            if PRINTING:
                print(
                    f"{name}: @@@ walked out without buying any milk at time: {env.now:.2f}"
                )
            return

    if PRINTING:
        print(
            f'{name}: finishes retrieving the milk at time: {env.now:.2f}. Fridge has {fridge["milk_container"].level}L of milk left.'
        )

    with cashiers.request() as cashier_req:
        yield cashier_req
        if PRINTING:
            print(f"{name}: gets a cashier at time: {env.now:.2f}.")
        yield env.timeout(FRIDGE_REPLENISH_DURATION)
        if PRINTING:
            print(f"{name}: leaves at time: {env.now:.2f}")


def customer_generator(env, cashiers, fridge):
    cust_number = 1
    while True:
        random_inter_arrival_time = random.expovariate(lambd=CUST_INTER_ARR_RATE)
        yield env.timeout(random_inter_arrival_time)
        env.process(
            customer(
                env=env,
                name=f"customer {cust_number}",
                cashiers=cashiers,
                fridge=fridge,
            )
        )
        cust_number += 1


def fridge_control_process(env, fridge):
    while True:
        if fridge["milk_container"].level < FRIDGE_REPLENISH_MIN_LEVEL:
            # ! USE PROCESS AS EVENT (YIELD) TO ENSURE WAITING
            yield env.process(fridge_refill_process(env, fridge))
        yield env.timeout(
            random.uniform(FRIDGE_REPLENISH_TIME_MIN, FRIDGE_REPLENISH_TIME_MAX)
        )


def fridge_refill_process(env, fridge):
    if PRINTING:
        print(f">>> FRIDGE REFILL process called at time {env.now:.2f}.")
    yield env.timeout(FRIDGE_REPLENISH_DURATION)  # 2 minutes
    to_refill = FRIDGE_LEVEL - fridge["milk_container"].level
    if PRINTING:
        print(
            f"Fridge has {fridge['milk_container'].level}L milk. Fridge filled with {to_refill}L milk."
        )
    yield fridge["milk_container"].put(to_refill)


random.seed(RANDOM_SEED)
env = simpy.Environment()
cashiers = simpy.Resource(env=env, capacity=NO_CASHIERS)
fridge = {
    "resource": simpy.Resource(env=env, capacity=NO_FRIDGES),
    "milk_container": simpy.Container(
        env=env, capacity=FRIDGE_CAPACITY, init=FRIDGE_LEVEL
    ),
}
env.process(customer_generator(env=env, cashiers=cashiers, fridge=fridge))
env.process(fridge_control_process(env=env, fridge=fridge))
env.run(until=SIM_TIME)  # 10 minutes
