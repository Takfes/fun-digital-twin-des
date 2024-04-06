import random
from dataclasses import dataclass

import numpy as np
import pandas as pd
import simpy
from tqdm import tqdm

# GENERIC CONFIGURATION
# DISPATCHING CONFIGURATION


def generate_data(
    n_loads: int,
    unload_minutes: int,
    depot_prep_time: int = 30,
    travel_minutes: int = 20,
    site_prep_time: int = 15,
    site_clean_time: int = 15,
    warmup_time: int = 0,
    # whether to dispatch to arrival or discharge
    dispatch_rate_incl_site_prep: bool = False,
) -> pd.DataFrame:
    """
    Generates a dataframe with the required data.
    """
    dispatch_logic = (
        depot_prep_time
        + travel_minutes
        + site_prep_time * int(dispatch_rate_incl_site_prep)
    )

    my_range = range(1, n_loads + 1)
    series_loads = list(my_range)
    series_unload_minutes = [unload_minutes for _ in my_range]
    series_depot_prep_time = [depot_prep_time for _ in my_range]
    series_travel_minutes = [travel_minutes for _ in my_range]
    series_site_prep_time = [site_prep_time for _ in my_range]
    series_site_clean_time = [site_clean_time for _ in my_range]
    series_dispatch_time = [
        dispatch_logic + warmup_time + (unload_minutes * (i - 1)) for i in my_range
    ]

    temp = pd.DataFrame(
        {
            "load_number": series_loads,
            "dispatch_time": series_dispatch_time,
            "depot_prep_time": series_depot_prep_time,
            "travel_minutes": series_travel_minutes,
            "site_prep_time": series_site_prep_time,
            "unload_minutes": series_unload_minutes,
            "site_clean_time": series_site_clean_time,
        }
    )
    temp.insert(
        2,
        "interdispatch_rate",
        temp.dispatch_time.diff().fillna(temp.dispatch_time.min()).astype(int),
    )
    return temp


@dataclass
class Ticket:
    load_number: int
    depot_prep_time: int
    travel_minutes: int
    site_prep_time: int
    unload_minutes: int
    clean_time: int
    dispatch_time: int
    interdispatch_rate: int


def create_tickets(orderbook):
    tickets = []
    for _, row in orderbook.iterrows():
        ticket = Ticket(
            load_number=row["load_number"],
            depot_prep_time=row["depot_prep_time"],
            travel_minutes=row["travel_minutes"],
            site_prep_time=row["site_prep_time"],
            unload_minutes=row["unload_minutes"],
            clean_time=row["site_clean_time"],
            dispatch_time=row["dispatch_time"],
            interdispatch_rate=row["interdispatch_rate"],
        )
        tickets.append(ticket)
    return tickets


def ticket_process(env, ticket):
    # reference events by their start time
    name = f"{ticket.load_number}"
    print(f"{name}: ticket: {env.now:.2f}")
    yield env.timeout(ticket.depot_prep_time)
    print(f"{name}: to job: {env.now:.2f}")
    yield env.timeout(ticket.travel_minutes)
    print(f"{name}: on job: {env.now:.2f}")
    yield env.timeout(ticket.site_prep_time)
    print(f"{name}: pour: {env.now:.2f}")
    yield env.timeout(ticket.unload_minutes)
    print(f"{name}: clean: {env.now:.2f}")
    yield env.timeout(ticket.clean_time)
    print(f"{name}: to plant: {env.now:.2f}")
    yield env.timeout(ticket.travel_minutes)
    print(f"{name}: at plant: {env.now:.2f}")


def ticket_generator(env, tickets):
    for ticket in tickets:
        yield env.timeout(ticket.interdispatch_rate)
        env.process(ticket_process(env, ticket))


orderbook = generate_data(
    n_loads=5, unload_minutes=10, dispatch_rate_incl_site_prep=True
)

tickets = create_tickets(orderbook)

env = simpy.Environment()
# unloading_bay = simpy.Resource(env, capacity=1)

# ticket = tickets[0]
# env.process(ticket_process(env, ticket))

env.process(ticket_generator(env, tickets))

env.run()
