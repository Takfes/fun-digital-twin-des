from dataclasses import dataclass, field

import simpy


@dataclass
class Depot:
    name: str
    latitude: float
    longitude: float
    loading_bay_nb: int
    env: simpy.Environment
    loading_bay: simpy.Resource = None
    trucks: list = field(default_factory=list)

    def __post_init__(self):
        self.loading_bay = simpy.Resource(self.env, capacity=self.loading_bay_nb)

    def add_truck(self, truck):
        self.trucks.append(truck)

    def remove_truck(self, truck):
        if truck in self.trucks:
            self.trucks.remove(truck)

    def get_available_truck(self):
        for truck in self.trucks:
            if not truck.resource.users:  # Check if truck resource is not in use
                return truck
        return None


@dataclass
class DeliverySite:
    name: str
    latitude: float
    longitude: float
    unloading_bay_nb: int
    env: simpy.Environment
    unloading_bay: simpy.Resource = None

    def __post_init__(self):
        self.unloading_bay = simpy.Resource(self.env, capacity=self.unloading_bay_nb)


@dataclass
class Truck:
    name: str
    home_depot: str
    clock_in_time: int
    clock_out_time: int
    env: simpy.Environment
    scheduled_tickets: list = field(
        default_factory=list
    )  # List of initially planned tickets
    tasks_finished: bool = False
    resource: simpy.Resource = None

    def __post_init__(self):
        self.resource = simpy.Resource(self.env, capacity=1)


@dataclass
class Ticket:
    order_id: str
    ticket_id: str
    dispatch_depot: str
    return_depot: str
    due_datetime: float
    travel_to_time: float
    travel_back_time: float
    plan_truck_id: str = None  # Truck initially planned to handle this ticket
    actual_truck_id: str = None  # Truck actually assigned to this ticket
    is_assigned: bool = False
