# DEBUG, INFO, WARNING, ERROR, CRITICAL
import datetime
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
        tri_mod = ticket.unload_time * UNLOAD_TIME_STOCHASTIC_OFFSET_FACTOR
        tri_rng = tri_mod * UNLOAD_TIME_STOCHASTIC_SD_FACTOR
        tri_min = max(min(tri_mod - tri_rng, 0), tri_mod)
        tri_max = tri_mod + tri_rng
        return random.triangular(tri_min, tri_max, tri_mod)
    else:
        return ticket.unload_time


def ticket_generator_vanilla(env, tickets):
    for ticket in tickets:
        yield env.timeout(ticket.dispatch_time)
        env.process(ticket_process(env, ticket))


def ticket_generator_qsize(env, tickets, unloading_bay):
    for ticket in tickets:
        while len(unloading_bay.queue) >= 1:
            yield env.timeout(2)
        yield env.timeout(ticket.dispatch_time)  # Dispatch time for the ticket
        env.process(ticket_process(env, ticket))


def ticket_generator_estmf(env, tickets, expected_release_times):
    for ticket in tickets:
        yield env.timeout(ticket.dispatch_time)
        # --------------------------------------------
        time_to_readiness = (
            ticket.depot_prep_time + ticket.travel_time + ticket.site_prep_time
        )
        max_unloading_end_time_k = get_expected_release_time(expected_release_times)[0]
        max_unloading_end_time_v = get_expected_release_time(expected_release_times)[1]
        logger.info(
            f"{ticket.load_number} {env.now} WAIT:{env.now < max_unloading_end_time_v - time_to_readiness} ARV?SHTNOW:{env.now}+{time_to_readiness}={env.now+time_to_readiness} {max_unloading_end_time_k}->RLS:{max_unloading_end_time_v:.2f} => SHOOT@:{max_unloading_end_time_v-time_to_readiness:.2f}"
        )
        # --------------------------------------------
        while env.now < max_unloading_end_time_v - time_to_readiness:
            yield env.timeout(5)
            # --------------------------------------------
            time_to_readiness = (
                ticket.depot_prep_time + ticket.travel_time + ticket.site_prep_time
            )
            max_unloading_end_time_k = get_expected_release_time(
                expected_release_times
            )[0]
            max_unloading_end_time_v = get_expected_release_time(
                expected_release_times
            )[1]
            logger.info(
                f"{ticket.load_number} {env.now} WAIT:{env.now < max_unloading_end_time_v - time_to_readiness} ARV?SHTNOW:{env.now}+{time_to_readiness}={env.now+time_to_readiness} {max_unloading_end_time_k}->RLS:{max_unloading_end_time_v:.2f} => SHOOT@:{max_unloading_end_time_v-time_to_readiness:.2f}"
            )
            # --------------------------------------------
            logger.info(
                f"{ticket.load_number} {env.now} << waiting before dispatching {env.now < max_unloading_end_time_v - time_to_readiness} {max_unloading_end_time_v - time_to_readiness:.2f}"
            )
        logger.info(f"{ticket.load_number} {env.now} >> dispatched")
        env.process(ticket_process(env, ticket))


def update_expected_release_time(
    ticket, expected_release_times, waiting_times, stage_name
):
    average_waiting_time = np.mean(waiting_times) if waiting_times else 0
    average_unloading_time = (
        np.mean(unload_times) if unload_times else ticket.unload_time
    )

    if stage_name == "depot_prep":
        expected_release_times[f"{ticket.load_number}_{stage_name}"] = (
            env.now
            + ticket.travel_time
            + ticket.site_prep_time
            + average_unloading_time
            + average_waiting_time
        )
        expected_release_times_details[f"{ticket.load_number}_{stage_name}"] = {
            "env.now": env.now,
            "ticket.travel_time": ticket.travel_time,
            "ticket.site_prep_time": ticket.site_prep_time,
            "average_unloading_time": average_unloading_time,
            "average_waiting_time": average_waiting_time,
            "waiting_times": waiting_times,
            "unload_times": unload_times,
        }
    elif stage_name == "travel_to":
        expected_release_times[f"{ticket.load_number}_{stage_name}"] = (
            env.now
            + ticket.site_prep_time
            + average_unloading_time
            + average_waiting_time
        )
        expected_release_times_details[f"{ticket.load_number}_{stage_name}"] = {
            "env.now": env.now,
            "ticket.travel_time": None,
            "ticket.site_prep_time": ticket.site_prep_time,
            "average_unloading_time": average_unloading_time,
            "average_waiting_time": average_waiting_time,
            "waiting_times": waiting_times,
            "unload_times": unload_times,
        }
    elif stage_name == "site_prep":
        expected_release_times[f"{ticket.load_number}_{stage_name}"] = (
            env.now + average_unloading_time + average_waiting_time
        )
        expected_release_times_details[f"{ticket.load_number}_{stage_name}"] = {
            "env.now": env.now,
            "ticket.travel_time": None,
            "ticket.site_prep_time": None,
            "average_unloading_time": average_unloading_time,
            "average_waiting_time": average_waiting_time,
            "waiting_times": waiting_times,
            "unload_times": unload_times,
        }


def get_expected_release_time(expected_release_times):
    if expected_release_times.values():
        max_key = max(expected_release_times, key=expected_release_times.get)
        max_value = expected_release_times[max_key]
        return max_key, max_value
    else:
        return None, 0


def ticket_process(env, ticket):
    name = f"{ticket.load_number}"

    if name not in ticket_times:
        ticket_times[name] = {}

    start_time = env.now
    stage_numb = "1"
    stage_name = "depot_prep"
    stage_id = f"{stage_numb}_{stage_name}"
    printer.debug(f"{name}: {stage_name}: {start_time:.2f}")
    yield env.timeout(ticket.depot_prep_time)
    ticket_times[name][stage_id] = (start_time, env.now)
    update_expected_release_time(
        ticket, expected_release_times, waiting_times, stage_name
    )

    start_time = env.now
    stage_numb = "2"
    stage_name = "travel_to"
    stage_id = f"{stage_numb}_{stage_name}"
    printer.debug(f"{name}: {stage_name}: {start_time:.2f}")
    yield env.timeout(ticket.travel_time)
    ticket_times[name][stage_id] = (start_time, env.now)
    update_expected_release_time(
        ticket, expected_release_times, waiting_times, stage_name
    )

    start_time = env.now
    stage_numb = "3"
    stage_name = "site_prep"
    stage_id = f"{stage_numb}_{stage_name}"
    printer.debug(f"{name}: {stage_name}: {start_time:.2f}")
    yield env.timeout(ticket.site_prep_time)
    finish_site_prep = env.now
    ticket_times[name][stage_id] = (start_time, finish_site_prep)
    update_expected_release_time(
        ticket, expected_release_times, waiting_times, stage_name
    )

    with unloading_bay.request() as ubr:
        yield ubr

        start_time = env.now
        stage_numb = "4"
        stage_name = "waiting"
        stage_id = f"{stage_numb}_{stage_name}"
        printer.debug(f"{name}: {stage_name}: {start_time:.2f}")
        ticket_times[name][stage_id] = (start_time, finish_site_prep)
        waiting_times.append(start_time - finish_site_prep)

        start_time = env.now
        stage_numb = "5"
        stage_name = "discharging"
        stage_id = f"{stage_numb}_{stage_name}"
        printer.debug(f"{name}: >> {stage_name}: {start_time:.2f}")
        yield env.timeout(
            sample_unloading_time(ticket, stochastic=UNLOAD_TIME_STOCHASTIC)
        )
        ticket_times[name][stage_id] = (start_time, env.now)
        printer.debug(f"{name}: << leaves unloading bay at {env.now:.2f}")
        unload_times.append(env.now - start_time)

    start_time = env.now
    stage_numb = "6"
    stage_name = "cleaning"
    stage_id = f"{stage_numb}_{stage_name}"
    printer.debug(f"{name}: {stage_name}: {start_time:.2f}")
    yield env.timeout(ticket.clean_time)
    ticket_times[name][stage_id] = (start_time, env.now)
    # update_expected_release_time(ticket, expected_release_times, waiting_times)

    start_time = env.now
    stage_numb = "7"
    stage_name = "travel_back"
    stage_id = f"{stage_numb}_{stage_name}"
    printer.debug(f"{name}: {stage_name}: {start_time:.2f}")
    yield env.timeout(ticket.travel_time)
    ticket_times[name][stage_id] = (start_time, env.now)
    # update_expected_release_time(ticket, expected_release_times, waiting_times)

    printer.debug(f"{name}: @ticket finished: {env.now:.2f}")


def plot_gantt(ticket_times):
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
        "1_depot_prep": "cyan",
        "2_travel_to": "blue",
        "3_site_prep": "purple",
        "4_waiting": "magenta",
        "5_discharging": "red",
        "6_cleaning": "orange",
        "7_travel_back": "green",
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
LOG_TO_FILE = True

# LOGGING CONFIGURATION
logger = logging.getLogger(__name__)
# formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# formatter = logging.Formatter("%(levelname)s - %(message)s")
formatter = logging.Formatter("$ %(message)s")
printer = configure_logger(
    log_to_console=True,
    log_to_file=LOG_TO_FILE,
    filename=f'logs/{datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S")}.log',
    level=logging.WARNING,
)

# INITIATE STATISTICS
ticket_times = {}
waiting_times = []
unload_times = []
expected_release_times = {}
expected_release_times_details = {}

# SIMULATION CONFIGURATIONS
DISPATCHING_MODE = 2
GANTT_PLOT = True
# RANDOM_SEED = 1990
# random.seed(RANDOM_SEED)

N_LOADS = 10
UNLOAD_TIME = 15
DEPOT_PREP_TIME = 30
TRAVEL_TIME = 25
SITE_PREP_TIME = 15
SITE_CLEAN_TIME = 15

UNLOAD_TIME_STOCHASTIC = True
UNLOAD_TIME_STOCHASTIC_OFFSET_FACTOR = 1.8
UNLOAD_TIME_STOCHASTIC_SD_FACTOR = 0.5

# MAKE DATA
orderbook = generate_data(
    n_loads=N_LOADS,
    unload_time=UNLOAD_TIME,
    depot_prep_time=DEPOT_PREP_TIME,
    travel_time=TRAVEL_TIME,
    site_prep_time=SITE_PREP_TIME,
    site_clean_time=SITE_CLEAN_TIME,
)
tickets = create_tickets(orderbook)

# ENVIRONMENT SETUP
env = simpy.Environment()
unloading_bay = simpy.Resource(env, capacity=1)
# ticket = tickets[0]
# env.process(ticket_process(env, ticket))
if DISPATCHING_MODE == 0:
    env.process(ticket_generator_vanilla(env, tickets))
elif DISPATCHING_MODE == 1:
    env.process(ticket_generator_qsize(env, tickets, unloading_bay))
elif DISPATCHING_MODE == 2:
    env.process(ticket_generator_estmf(env, tickets, expected_release_times))


# RUN SIMULATION
env.run()

# REVIEW STATISTICS
if GANTT_PLOT:
    plot_gantt(ticket_times)

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

logger.warning("")
logger.warning(f"Dispatching mode: {DISPATCHING_MODE}")
logger.warning(f"Number of loads: {N_LOADS}")
logger.warning(f"Unload times deterministic: {unload_times_theoretical} +/- 0")
if UNLOAD_TIME_STOCHASTIC:
    logger.warning(
        f"Unload times stochastic: [{unload_times_theoretical}] {unload_times_mu:.2f} +/- {unload_times_sd:.2f}"
    )
logger.warning(f"Unload times: {unload_times_rounded}")
logger.warning(f"Waiting times: {waiting_times_rounded}")
logger.warning(
    f"Avg waiting time: {np.mean(waiting_times):.2f} +/- {np.std(waiting_times):.2f}"
)
logger.warning(f"Total waiting time: {total_waiting_time:.2f}")
logger.warning(
    f"Waiting % total theoretical: {total_waiting_time/total_theoretical_time:.2%}"
)

logger.info("")
logger.info(expected_release_times)
logger.info("")
logger.info(expected_release_times_details)
