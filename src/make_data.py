from assets.assets import *


def generate_data(env):
    depots = [
        Depot(name="Depot1", latitude=10.0, longitude=20.0, env=env),
        Depot(name="Depot2", latitude=15.0, longitude=25.0, env=env),
    ]

    delivery_sites = [
        DeliverySite(name="Site1", latitude=35.0, longitude=45.0, env=env)
    ]

    trucks = [
        Truck(name="Truck1", home_depot="Depot1"),
        Truck(name="Truck2", home_depot="Depot1"),
        Truck(name="Truck3", home_depot="Depot2"),
        Truck(name="Truck4", home_depot="Depot2"),
    ]

    tickets = [
        Ticket(
            order_id="Order1",
            ticket_id="Ticket1",
            truck_id="Truck1",
            dispatch_depot="Depot1",
            return_depot="Depot1",
            due_datetime=10.0,
            travel_to_time=5.0,
            travel_back_time=5.0,
        ),
        Ticket(
            order_id="Order1",
            ticket_id="Ticket2",
            truck_id="Truck2",
            dispatch_depot="Depot1",
            return_depot="Depot1",
            due_datetime=10.0,
            travel_to_time=5.0,
            travel_back_time=5.0,
        ),
        Ticket(
            order_id="Order1",
            ticket_id="Ticket3",
            truck_id="Truck3",
            dispatch_depot="Depot2",
            return_depot="Depot2",
            due_datetime=10.0,
            travel_to_time=5.0,
            travel_back_time=5.0,
        ),
        Ticket(
            order_id="Order1",
            ticket_id="Ticket4",
            truck_id="Truck4",
            dispatch_depot="Depot2",
            return_depot="Depot2",
            due_datetime=10.0,
            travel_to_time=5.0,
            travel_back_time=5.0,
        ),
    ]

    return (
        depots,
        delivery_sites,
        trucks,
        tickets,
    )
