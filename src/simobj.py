from dataclasses import dataclass
from typing import List, Union

import pandas as pd
import simpy


@dataclass
class Ticket:
    order_id: str
    ticket_id: str
    load_number: int
    ticket_start_time: int
    ticket_arrive_time: int
    load_mins: int
    site_prep_mins: int
    unload_mins: int
    site_clean_mins: int
    ship_loc: str
    distance_to: float
    travel_to_mins: int
    return_loc: str
    distance_back: float
    travel_back_mins: int
    # simulation quantities tracking
    sim_ticket_start_time: int = None
    sim_ticket_arrive_time: int = None
    sim_load_mins: int = None
    sim_site_prep_mins: int = None
    sim_unload_mins: int = None
    sim_site_clean_mins: int = None
    sim_travel_to_mins: int = None
    sim_travel_back_mins: int = None

    @property
    def is_started(self) -> bool:
        return self.sim_ticket_start_time is not None


@dataclass
class Order:
    order_id: str
    quantity: int
    due_time: int
    due_time_mins: int
    customer: str
    customer_loc: str
    sched_loc: str
    load_mins: int
    site_prep_mins: int
    unload_mins: int
    site_clean_mins: int
    n_loads: int
    tickets: List[Ticket]

    @property
    def is_started(self) -> bool:
        return any(ticket.sim_ticket_start_time is not None for ticket in self.tickets)

    @property
    def is_finished() -> bool:
        pass

    @property
    def progress() -> float:
        pass


@dataclass
class Hub:
    env: simpy.Environment
    tickets: List[Ticket]

    def ticket_generator(self, tickets):
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
    clock_out_time: int
    status: str = None
    current_location: str = None
    return_location: str = None

    def __post_init__(self):
        self.resource = simpy.Resource(self.env, capacity=1)

    def process_ticket(self):
        """
        simulates the steps required to complete the ticket
        loading > travel > site_prep > unload > site_clean > travel_back
        # ! release truck resource at the end of the process
        """
        pass


# @dataclass
# class Fleet:
#     env: simpy.Environment
#     clockins: pd.DataFrame
#     trucks: List[Truck]

#     def __post_init__(self):
#         self.in_yard = simpy.FilterStore(self.env)

#     def request_truck(self, depot: str) -> Truck:
#         pass

#     def truck_clock_in(self):
#         yield self.env.timeout(self.clock_in_time)
#         self.current_location = self.home_depot


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


@dataclass
class SimEngine:
    env: simpy.Environment
    orderlist: pd.DataFrame
    ticketlist: pd.DataFrame
    depotlist: pd.DataFrame
    trucklist: pd.DataFrame

    orders: List[Order] = None
    tickets: List[Ticket] = None
    depots: List[Depot] = None
    trucks: List[Truck] = None

    def __post_init__(self):
        self.tickets = self.create_ticket_obj(self.ticketlist)
        self.orders = self.create_order_obj(self.orderlist, self.tickets)
        self.depots = self.create_depot_obj(self.depotlist)
        self.trucks = self.create_truck_obj(self.trucklist)

    def create_ticket_obj(self, ticketlist):
        tickets = []
        for _, row in ticketlist.iterrows():
            ticket = Ticket(
                order_id=row["order_id"],
                ticket_id=row["ticket_id"],
                load_number=row["load_number"],
                ticket_start_time=row["ticket_start_time"],
                ticket_arrive_time=row["ticket_arrive_time"],
                load_mins=row["load_mins"],
                site_prep_mins=row["site_prep_mins"],
                unload_mins=row["unload_mins"],
                site_clean_mins=row["site_clean_mins"],
                ship_loc=row["ship_loc"],
                distance_to=row["distance_to"],
                travel_to_mins=row["travel_to_mins"],
                return_loc=row["return_loc"],
                distance_back=row["distance_back"],
                travel_back_mins=row["travel_back_mins"],
            )
            tickets.append(ticket)
        return tickets

    def create_order_obj(self, orderlist, tickets):
        orders = []
        for _, row in orderlist.iterrows():
            order = Order(
                order_id=row["order_id"],
                quantity=row["quantity"],
                due_time=row["due_time"],
                due_time_mins=row["due_time_mins"],
                customer=row["customer"],
                customer_loc=row["customer_loc"],
                sched_loc=row["sched_loc"],
                load_mins=row["load_mins"],
                site_prep_mins=row["site_prep_mins"],
                unload_mins=row["unload_mins"],
                site_clean_mins=row["site_clean_mins"],
                n_loads=row["n_loads"],
                tickets=[t for t in tickets if t.order_id == row["order_id"]],
            )
            orders.append(order)
        return orders

    def create_depot_obj(self, depotlist):
        depots = []
        for _, row in depotlist.iterrows():
            depot = Depot(
                env=self.env,
                depot_id=row["depot_id"],
                depot_lon=row["depot_lon"],
                depot_lat=row["depot_lat"],
            )
            depots.append(depot)
        return depots

    def create_truck_obj(self, trucklist):
        trucks = []
        for _, row in trucklist.iterrows():
            truck = Truck(
                env=self.env,
                truck_id=row["truck_id"],
                home_depot=row["home_depot"],
                clock_in_time=row["clock_in_time"],
                clock_out_time=row["clock_out_time"],
            )
            trucks.append(truck)
        return trucks

    def get_order(self, order_id: str) -> Order:
        return [order for order in self.orders if order.order_id == order_id][0]

    def get_ticket(self, ticket_id: str) -> Ticket:
        return [ticket for ticket in self.tickets if ticket.ticket_id == ticket_id][0]

    def get_parent_order(self, ticket_id: str) -> Order:
        return self.get_order(self.get_ticket(ticket_id).order_id)

    def get_depot(self, depot_id: str) -> Depot:
        return [depot for depot in self.depots if depot.depot_id == depot_id][0]

    def get_truck(self, truck_id: str) -> Truck:
        return [truck for truck in self.trucks if truck.truck_id == truck_id][0]
