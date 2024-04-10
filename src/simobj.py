from dataclasses import dataclass

import simpy


def create_order_obj():
    pass


def create_ticket_obj():
    pass


def create_depot_obj():
    pass


def create_truck_obj():
    pass


@dataclass
class Order:
    is_started: bool
    priority: int


@dataclass
class Ticket:
    load_number: int
    depot_prep_time: int
    travel_time: int
    site_prep_time: int
    unload_time: int
    clean_time: int
    dispatch_time: int


@dataclass
class Depot:
    env: simpy.Environment
    depot_id: str
    depot_lon: float
    depot_lat: float
    loader_capacity: int = 1

    def __post_init__(self):
        self.queue = simpy.PriorityStore(self.env)
        self.loader = simpy.Resource(self.env, capacity=self.loader_capacity)


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

    def clock_in(self):
        yield self.env.timeout(self.clock_in_time)
        self.current_location = self.home_depot
