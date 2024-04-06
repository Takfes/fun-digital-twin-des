import random
from dataclasses import dataclass

import numpy as np
import pandas as pd
import simpy


def generate_data(
    n_loads: int,
    unload_minutes: int,
    depot_prep_time: int = 30,
    travel_minutes: int = 20,
    site_prep_time: int = 10,
    site_clean_time: int = 10,
) -> pd.DataFrame:
    """
    Generates a dataframe with the required data.
    """

    my_range = range(1, n_loads + 1)
    series_loads = list(my_range)
    series_unload_minutes = [unload_minutes for _ in my_range]
    series_depot_prep_time = [depot_prep_time for _ in my_range]
    series_travel_minutes = [travel_minutes for _ in my_range]
    series_site_prep_time = [site_prep_time for _ in my_range]
    series_site_clean_time = [site_clean_time for _ in my_range]
    series_dispatch_time = [unload_minutes for _ in my_range]
    series_dispatch_time.insert(0, 0)
    series_dispatch_time.pop()

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
        )
        tickets.append(ticket)
    return tickets


def ticket_process(env, ticket):
    name = f"{ticket.load_number}"

    if name not in ticket_times:
        ticket_times[name] = {}

    start_time = env.now
    print(f"{name}: depot_prep: {start_time:.2f}")
    yield env.timeout(ticket.depot_prep_time)
    ticket_times[name]["1.depot_prep"] = (start_time, env.now)

    start_time = env.now
    print(f"{name}: travel_to: {env.now:.2f}")
    yield env.timeout(ticket.travel_minutes)
    ticket_times[name]["2.travel_to"] = (start_time, env.now)

    start_time = env.now
    print(f"{name}: waiting: {env.now:.2f}")
    yield env.timeout(ticket.site_prep_time)
    ticket_times[name]["3.waiting"] = (start_time, env.now)

    start_time = env.now
    print(f"{name}: discharging: {env.now:.2f}")
    yield env.timeout(ticket.unload_minutes)
    ticket_times[name]["4.discharging"] = (start_time, env.now)

    start_time = env.now
    print(f"{name}: cleaning: {env.now:.2f}")
    yield env.timeout(ticket.clean_time)
    ticket_times[name]["5.cleaning"] = (start_time, env.now)

    start_time = env.now
    print(f"{name}: travel_back: {env.now:.2f}")
    yield env.timeout(ticket.travel_minutes)
    ticket_times[name]["6.travel_back"] = (start_time, env.now)

    print(f"{name}: @ticket finished: {env.now:.2f}")


def ticket_generator(env, tickets):
    for ticket in tickets:
        yield env.timeout(ticket.dispatch_time)
        env.process(ticket_process(env, ticket))


def plot_gannt(ticket_times):
    import matplotlib.dates as mdates
    from matplotlib import pyplot as plt

    gdf = (
        pd.DataFrame()
        .from_dict(ticket_times, orient="index")
        .stack()
        .to_frame()
        .reset_index()
    )
    gdf.columns = ["ticket", "stage", "times"]
    gdf["start"] = gdf.times.apply(lambda x: x[0])
    gdf["end"] = gdf.times.apply(lambda x: x[1])
    gdf.drop(columns=["times"], inplace=True)
    max_x_value = gdf.end.max()

    # Convert 'start' and 'end' to datetime if they aren't already
    gdf["start"] = pd.to_datetime(
        gdf["start"], unit="D"
    )  # Adjust the unit as per your data
    gdf["end"] = pd.to_datetime(
        gdf["end"], unit="D"
    )  # Adjust the unit as per your data

    # Define colors for each stage
    colors = {
        "1.depot_prep": "cyan",
        "2.travel_to": "blue",
        "3.waiting": "purple",
        "4.discharging": "red",
        "5.cleaning": "orange",
        "6.travel_back": "green",
    }

    fig, ax = plt.subplots(figsize=(10, 5))  # Adjust size as needed

    # Plot each ticket's stages
    for key, grp in gdf.groupby(["ticket"]):
        for _, row in grp.iterrows():
            start_date = mdates.date2num(row["start"])
            end_date = mdates.date2num(row["end"])
            ax.barh(
                y=row["ticket"],
                width=end_date - start_date,
                left=start_date,
                color=colors[row["stage"]],
                edgecolor="black",
            )
    ax.set_xticks(np.arange(0, max_x_value, 10))

    ax.grid(
        axis="x",
        which="both",
        linestyle="dotted",
        alpha=1,
        color="black",
        linewidth=1,
    )
    fig.autofmt_xdate()
    plt.xlabel("Time")
    plt.ylabel("ticket")
    plt.tight_layout()
    plt.show()


orderbook = generate_data(n_loads=3, unload_minutes=10)

tickets = create_tickets(orderbook)

ticket_times = {}
env = simpy.Environment()
# unloading_bay = simpy.Resource(env, capacity=1)

# ticket = tickets[0]
# env.process(ticket_process(env, ticket))

env.process(ticket_generator(env, tickets))

env.run()

plot_gannt(ticket_times)
