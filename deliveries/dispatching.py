# DEBUG, INFO, WARNING, ERROR, CRITICAL
import logging
import random
from dataclasses import dataclass

import numpy as np
import pandas as pd
import simpy
from tqdm import tqdm


def configure_logger(
    log_to_console=True,
    log_to_file=False,
    filename=None,
    level=logging.INFO,
):
    # Remove all existing handlers
    logger.handlers = []

    # Set the log level
    logger.setLevel(level)

    if log_to_console:
        # Create a console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    if log_to_file and filename:
        # Create a file handler
        file_handler = logging.FileHandler(filename)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    return logger


def generate_data(
    n_loads: int,
    unload_time: int,
    depot_prep_time: int = 30,
    travel_time: int = 20,
    site_prep_time: int = 10,
    site_clean_time: int = 10,
) -> pd.DataFrame:
    """
    Generates a dataframe with the required data.
    """

    my_range = range(1, n_loads + 1)
    series_loads = list(my_range)
    series_unload_minutes = [unload_time for _ in my_range]
    series_depot_prep_time = [depot_prep_time for _ in my_range]
    series_travel_minutes = [travel_time for _ in my_range]
    series_site_prep_time = [site_prep_time for _ in my_range]
    series_site_clean_time = [site_clean_time for _ in my_range]
    series_dispatch_time = [unload_time for _ in my_range]
    series_dispatch_time.insert(0, 0)
    series_dispatch_time.pop()

    temp = pd.DataFrame(
        {
            "load_number": series_loads,
            "dispatch_time": series_dispatch_time,
            "depot_prep_time": series_depot_prep_time,
            "travel_time": series_travel_minutes,
            "site_prep_time": series_site_prep_time,
            "unload_time": series_unload_minutes,
            "site_clean_time": series_site_clean_time,
        }
    )
    return temp


@dataclass
class Ticket:
    load_number: int
    depot_prep_time: int
    travel_time: int
    site_prep_time: int
    unload_time: int
    clean_time: int
    dispatch_time: int


def create_tickets(orderbook):
    tickets = []
    for _, row in orderbook.iterrows():
        ticket = Ticket(
            load_number=row["load_number"],
            depot_prep_time=row["depot_prep_time"],
            travel_time=row["travel_time"],
            site_prep_time=row["site_prep_time"],
            unload_time=row["unload_time"],
            clean_time=row["site_clean_time"],
            dispatch_time=row["dispatch_time"],
        )
        tickets.append(ticket)
    return tickets


def sample_unloading_time(ticket, stochastic=True):
    if stochastic:
        mu = ticket.unload_time * UNLOAD_TIME_STOCHASTIC_OFFSET_FACTOR
        sd = mu * UNLOAD_TIME_STOCHASTIC_SD_FACTOR
        return random.gauss(mu, sd)
    else:
        return ticket.unload_time


def ticket_generator(env, tickets):
    for ticket in tickets:
        yield env.timeout(ticket.dispatch_time)
        # yield env.timeout(0)
        env.process(ticket_process(env, ticket))


def ticket_process(env, ticket):
    name = f"{ticket.load_number}"

    if name not in ticket_times:
        ticket_times[name] = {}

    start_time = env.now
    printer.debug(f"{name}: depot_prep: {start_time:.2f}")
    yield env.timeout(ticket.depot_prep_time)
    ticket_times[name]["1.depot_prep"] = (start_time, env.now)

    start_time = env.now
    printer.debug(f"{name}: travel_to: {start_time:.2f}")
    yield env.timeout(ticket.travel_time)
    ticket_times[name]["2.travel_to"] = (start_time, env.now)

    start_time = env.now
    printer.debug(f"{name}: site_prepring: {start_time:.2f}")
    yield env.timeout(ticket.site_prep_time)
    finish_site_prep = env.now
    ticket_times[name]["3.site_prep"] = (start_time, finish_site_prep)

    with unloading_bay.request() as ubr:
        yield ubr
        start_time = env.now
        waiting_times.append(start_time - finish_site_prep)
        ticket_times[name]["4.waiting"] = (start_time, finish_site_prep)
        printer.debug(f"{name}: >> discharging: {start_time:.2f}")
        yield env.timeout(
            sample_unloading_time(ticket, stochastic=UNLOAD_TIME_STOCHASTIC)
        )
        ticket_times[name]["5.discharging"] = (start_time, env.now)
        printer.debug(f"{name}: << leaves unloading bay at {env.now:.2f}")
        unload_times.append(env.now - start_time)

    # start_time = env.now
    # printer.debug(f"{name}: discharging: {env.now:.2f}")
    # yield env.timeout(ticket.unload_time)
    # ticket_times[name]["4.discharging"] = (start_time, env.now)

    start_time = env.now
    printer.debug(f"{name}: cleaning: {start_time:.2f}")
    yield env.timeout(ticket.clean_time)
    ticket_times[name]["6.cleaning"] = (start_time, env.now)

    start_time = env.now
    printer.debug(f"{name}: travel_back: {start_time:.2f}")
    yield env.timeout(ticket.travel_time)
    ticket_times[name]["7.travel_back"] = (start_time, env.now)

    printer.debug(f"{name}: @ticket finished: {env.now:.2f}")


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
    gdf.ticket = gdf.ticket.astype(int)
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
        "3.site_prep": "purple",
        "4.waiting": "magenta",
        "5.discharging": "red",
        "6.cleaning": "orange",
        "7.travel_back": "green",
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


# GENERIC CONFIGURATION
logger = logging.getLogger(__name__)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
printer = configure_logger(
    log_to_console=True, log_to_file=False, filename=None, level=logging.INFO
)

# INITIATE STATISTICS
ticket_times = {}
waiting_times = []
unload_times = []

# SIMULATION CONFIGURATIONS
N_LOADS = 10
UNLOAD_TIME = 15
UNLOAD_TIME_STOCHASTIC = True
UNLOAD_TIME_STOCHASTIC_OFFSET_FACTOR = 1.25
UNLOAD_TIME_STOCHASTIC_SD_FACTOR = 0.25
GANTT_PLOT = True

# MAKE DATA
orderbook = generate_data(n_loads=N_LOADS, unload_time=UNLOAD_TIME)
tickets = create_tickets(orderbook)

# ENVIRONMENT SETUP
env = simpy.Environment()
unloading_bay = simpy.Resource(env, capacity=1)
# ticket = tickets[0]
# env.process(ticket_process(env, ticket))
env.process(ticket_generator(env, tickets))

# RUN SIMULATION
env.run()

# REVIEW STATISTICS
if GANTT_PLOT:
    plot_gannt(ticket_times)

total_waiting_time = sum(waiting_times)
unload_times_rounded = [round(x, 1) for x in unload_times]
waiting_times_rounded = [round(x, 1) for x in waiting_times]

total_theoretical_time = sum(
    orderbook["depot_prep_time"]
    + 2 * orderbook["travel_time"]
    + orderbook["site_prep_time"]
    + orderbook["unload_time"]
    + orderbook["site_clean_time"]
)

unload_times_theoretical = UNLOAD_TIME
unload_times_mu = UNLOAD_TIME * UNLOAD_TIME_STOCHASTIC_OFFSET_FACTOR
unload_times_sd = unload_times_mu * UNLOAD_TIME_STOCHASTIC_SD_FACTOR

print(f"Number of loads: {N_LOADS}")
print(f"Unload times deterministic: {unload_times_theoretical} +/- 0")
if UNLOAD_TIME_STOCHASTIC:
    print(
        f"Unload times stochastic: [{unload_times_theoretical}] {unload_times_mu:.2f} +/- {unload_times_sd:.2f}"
    )
print(f"Unload times: {unload_times_rounded}")
print(f"Waiting times: {waiting_times_rounded}")
print(f"Avg waiting time: {np.mean(waiting_times):.2f} +/- {np.std(waiting_times):.2f}")
print(f"Total waiting time: {total_waiting_time:.2f}")
print(f"Waiting % total theoretical: {total_waiting_time/total_theoretical_time:.2%}")
logger.info(
    f"Waiting % total theoretical: {total_waiting_time/total_theoretical_time:.2%}"
)
