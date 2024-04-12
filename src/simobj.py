from dataclasses import dataclass
from typing import List

import pandas as pd
import simpy


@dataclass
class Ticket:
    dispatch_time: int
    load_number: int
    pln_loading_time: float
    pln_travel_time: float
    pln_prep_time: float
    pln_unload_time: float
    pln_clean_time: float
    pln_total_time: float
    act_loading_time: float = None
    act_travel_time: float = None
    act_prep_time: float = None
    act_unload_time: float = None
    act_clean_time: float = None
    act_total_time: float = None
    waiting_time: float = 0.0


@dataclass
class Order:
    pln_start_time: float
    pln_end_time: float
    act_start_time: float
    act_end_time: float
    tickets: List[Ticket]

    @staticmethod
    def is_started() -> bool:
        pass

    @staticmethod
    def is_finished() -> bool:
        pass

    def progress() -> float:
        pass


@dataclass
class Hub:
    env: simpy.Environment
    orderbook: pd.DataFrame
    ticketbook: pd.DataFrame

    def create_order_obj(self):
        pass

    def create_ticket_obj(self):
        pass

    def ticket_generator(self):
        """
        spawn tickets in the simulation
        can accommodate different logics :
        vanilla, track site queue, track site progress
        # ! push tickets to Depot queues
        """
        pass


@dataclass
class Truck:
    env: simpy.Environment
    truck_id: str
    home_depot: str
    clock_in_time: int
    current_location: str
    return_location: str

    def __post_init__(self):
        self.resource = simpy.Resource(self.env, capacity=1)

    def process_ticket(self):
        """
        simulates the steps required to complete the ticket
        loading > travel > prep > unload > site_clean > travel_back
        # ! release truck resource at the end of the process
        """
        pass


@dataclass
class Fleet:
    env: simpy.Environment
    clockins: pd.DataFrame

    def __post_init__(self):
        self.store = simpy.FilterStore(self.env)

    def create_truck_obj():
        pass

    def truck_clock_in(self):
        yield self.env.timeout(self.clock_in_time)
        self.current_location = self.home_depot


@dataclass
class Depot:
    env: simpy.Environment
    depot_id: str
    depot_lon: float
    depot_lat: float
    loader_capacity: int = 1

    def __post_init__(self):
        self.ticket_queue = simpy.PriorityStore(self.env)
        self.loading_bay = simpy.Resource(self.env, capacity=self.loader_capacity)

    def add_ticket(self):
        pass

    def truck_assignment(self):
        """
        assign trucks to tickets
        monitors ticket queues and truck availability, assigning tickets to trucks based on predefined rules or priorities.
        """
        pass
