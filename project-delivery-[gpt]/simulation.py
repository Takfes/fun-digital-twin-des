import simpy

from make_data import generate_data

FIXED_DURATION = True
SIMULATION_TIME = 1440.0
CHECK_INTERVAL = 10.0
TIME_THRESHOLD = 10.0
LOADING_TIME = 6.5
TRAVEL_TIME = 20.0
SITE_PREP_TIME = 12.5
UNLOADING_TIME = 20.0


def initialize_simulation():
    env = simpy.Environment()
    return env, *generate_data(env)
    # env, depots, delivery_sites, trucks, tickets = setup_environment()


def driver_clock_in(env, truck, depot):
    yield env.timeout(truck.clock_in_time)
    depot.add_truck(truck)


def driver_clock_out(env, truck, depot):
    yield env.timeout(truck.clock_out_time - env.now)
    while not truck.tasks_finished:
        yield env.timeout(1)  # Check every 1 time unit, adjust as needed
    depot.remove_truck(truck)


def loading_process(env, truck, depot):
    pass


def unloading_process(env, truck, delivery_site):
    pass


def prep_process(env, truck, destination, travel_time):
    pass


def travel_process(env, truck, destination, travel_time):
    pass


def get_depot_by_name(depots, depot_name):
    return next((depot for depot in depots if depot.name == depot_name), None)


def get_delivery_site_by_name(delivery_sites, site_name):
    return next((site for site in delivery_sites if site.name == site_name), None)


def all_tickets_processed(tickets):
    return all(ticket.is_assigned for ticket in tickets)


def assign_trucks_to_depots(trucks, depots):
    for truck in trucks:
        home_depot = next(
            (depot for depot in depots if depot.name == truck.home_depot), None
        )
        if home_depot:
            home_depot.add_truck(truck)
        else:
            print(
                f"Warning: Home depot '{truck.home_depot}' for truck '{truck.name}' not found."
            )


def exchange_schedules(ticket, truck, trucks):
    original_truck = next((t for t in trucks if ticket in t.scheduled_tickets), None)
    if original_truck:
        truck.scheduled_tickets, original_truck.scheduled_tickets = (
            original_truck.scheduled_tickets,
            truck.scheduled_tickets,
        )


def assign_tickets(env, tickets, depots, delivery_sites, trucks):
    while True:
        for depot in depots:
            available_truck = depot.get_available_truck()
            if available_truck:
                current_time = env.now
                relevant_tickets = [
                    t
                    for t in tickets
                    if t.dispatch_depot == depot.name
                    and not t.is_assigned
                    and t.due_datetime - current_time <= TIME_THRESHOLD
                ]
                sorted_tickets = sorted(relevant_tickets, key=lambda x: x.due_datetime)
                if sorted_tickets:
                    ticket = sorted_tickets[0]
                    ticket.is_assigned = True
                    ticket.actual_truck_id = available_truck.name
                    if ticket.plan_truck_id != available_truck.name:
                        exchange_schedules(ticket, available_truck, trucks)
                    env.process(
                        truck_scheduling(
                            env, available_truck, ticket, depots, delivery_sites
                        )
                    )
                else:
                    break  # No relevant tickets for this depot at this time
            else:
                break  # No more available trucks in this depot, move to next depot
        yield env.timeout(1)


def truck_scheduling(env, truck, ticket, depots, delivery_sites):
    # Wait until the ticket's due time to start processing
    yield env.timeout(max(0, ticket.due_datetime - env.now))

    # Loading at dispatch depot
    dispatch_depot = get_depot_by_name(depots, truck.home_depot)
    if dispatch_depot:
        yield env.process(loading_process(env, truck, dispatch_depot))
    else:
        print(
            f"Dispatch depot '{truck.home_depot}' not found for truck '{truck.name}'."
        )
        return

    # Travel to delivery site
    delivery_site = get_delivery_site_by_name(delivery_sites, ticket.order_id)
    if delivery_site:
        yield env.process(
            travel_process(env, truck, delivery_site, ticket.travel_to_time)
        )
        yield env.process(unloading_process(env, truck, delivery_site))
    else:
        print(f"Delivery site '{ticket.order_id}' not found for truck '{truck.name}'.")
        return

    # Travel to return depot
    return_depot = get_depot_by_name(depots, ticket.return_depot)
    if return_depot:
        yield env.process(
            travel_process(env, truck, return_depot, ticket.travel_back_time)
        )
        truck.home_depot = ticket.return_depot  # Update truck's home depot
    else:
        print(
            f"Return depot '{ticket.return_depot}' not found for truck '{truck.name}'."
        )


def run_simulation():
    env, depots, delivery_sites, trucks, tickets = initialize_simulation()
    assign_trucks_to_depots(trucks, depots)
    for truck in trucks:
        env.process(
            driver_clock_in(env, truck, get_depot_by_name(depots, truck.home_depot))
        )
        env.process(
            driver_clock_out(env, truck, get_depot_by_name(depots, truck.home_depot))
        )
    env.process(assign_tickets(env, tickets, depots, delivery_sites))
    if FIXED_DURATION:
        env.run(until=SIMULATION_TIME)
    else:
        while not all_tickets_processed(tickets):
            env.run(until=env.now + CHECK_INTERVAL)


if __name__ == "__main__":
    run_simulation()
