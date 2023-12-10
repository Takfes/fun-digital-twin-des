import simpy
from dotenv import dotenv_values, load_dotenv

from make_data import generate_data

# load_dotenv()
config = dotenv_values(".env")
LOADING_TIME = config["LOADING_TIME"] = float(config["LOADING_TIME"])
TRAVEL_TIME = config["TRAVEL_TIME"] = float(config["TRAVEL_TIME"])
SITE_PREP_TIME = config["SITE_PREP_TIME"] = float(config["SITE_PREP_TIME"])
UNLOADING_TIME = config["UNLOADING_TIME"] = float(config["UNLOADING_TIME"])


def initialize_simulation():
    env = simpy.Environment()
    return env, *generate_data(env)
    # env, depots, delivery_sites, trucks, tickets = setup_environment()


# def loading_process(env, truck, depot):
#     with depot.loading_bay.request() as request:
#         yield request  # Wait for access to the loading bay
#         # Assume loading time is a constant, can be replaced with a distribution
#         yield env.timeout(
#             LOADING_TIME
#         )  # Replace LOADING_TIME with actual time or a distribution
#         print(f"{env.now}: {truck.name} finished loading at {depot.name}")

# def unloading_process(env, truck, delivery_site):
#     with delivery_site.unloading_bay.request() as request:
#         yield request  # Wait for access to the unloading bay
#         # unloading_time = np.random.normal(
#         #     MEAN_UNLOADING_TIME, UNLOADING_TIME_STD_DEV
#         # )  # Replace with your distribution parameters
#         yield env.timeout(UNLOADING_TIME)
#         print(f"{env.now}: {truck.name} finished unloading at {delivery_site.name}")

# def travel_process(env, truck, destination, travel_time):
#     yield env.timeout(TRAVEL_TIME)  # Simulate the travel time
#     print(f"{env.now}: {truck.name} arrived at {destination}")


# Functions for Loading and Unloading Processes
def loading_process(env, truck, depot):
    # Simulate truck loading at the depot
    pass


def unloading_process(env, truck, delivery_site):
    # Simulate truck unloading at the delivery site
    pass


# Function for Simulating the Prep Process at the Delivery Site
def prep_process(env, truck, destination, travel_time):
    # Simulate the travel time of trucks between locations
    pass


# Function for Simulating Traveling Process
def travel_process(env, truck, destination, travel_time):
    # Simulate the travel time of trucks between locations
    pass


# Function to Assign Trucks to Depots
def assign_trucks_to_depots(trucks, depots):
    # Logic to assign each truck to its starting depot
    # Iterate through each truck
    for truck in trucks:
        # Find the depot that matches the truck's home depot
        home_depot = next(
            (depot for depot in depots if depot.name == truck.home_depot), None
        )

        # If the matching depot is found, add the truck to the depot's list
        if home_depot:
            home_depot.add_truck(truck)
        else:
            print(
                f"Warning: Home depot '{truck.home_depot}' for truck '{truck.name}' not found."
            )


# Function for Ticket Processing and Truck Dispatch
def assign_tickets(env, tickets, depots, delivery_sites):
    # Continuously go through tickets and assign them to available trucks
    # Sorting tickets based on some criteria, e.g., due date/time
    sorted_tickets = sorted(tickets, key=lambda x: x.due_datetime)

    # Loop to continuously try to assign tickets
    while True:
        for ticket in sorted_tickets:
            # Check if the ticket is already assigned
            if not ticket.is_assigned:
                # Find the dispatch depot for the ticket
                dispatch_depot = next(
                    (depot for depot in depots if depot.name == ticket.dispatch_depot),
                    None,
                )

                # If the dispatch depot is found
                if dispatch_depot:
                    # Attempt to get an available truck from the depot
                    available_truck = dispatch_depot.get_available_truck()

                    # If a truck is available, schedule it for the ticket and mark the ticket as assigned
                    if available_truck:
                        ticket.is_assigned = True
                        env.process(
                            truck_scheduling(
                                env, available_truck, ticket, depots, delivery_sites
                            )
                        )
                else:
                    print(
                        f"Warning: Dispatch depot '{ticket.dispatch_depot}' for ticket '{ticket.ticket_id}' not found."
                    )

        # Wait for a bit before trying to assign tickets again
        yield env.timeout(1)  # This can be adjusted based on simulation needs


# Function for Truck Scheduling for Each Ticket
def truck_scheduling(env, truck, ticket, depots, delivery_sites):
    # Process for handling the sequence of loading, traveling, unloading, and returning
    # Start by loading the truck at its dispatch depot
    dispatch_depot = next(
        (depot for depot in depots if depot.name == ticket.dispatch_depot), None
    )
    if dispatch_depot:
        yield env.process(loading_process(env, truck, dispatch_depot))
    else:
        print(
            f"Dispatch depot '{ticket.dispatch_depot}' not found for truck '{truck.name}'."
        )
        return  # Exit the process if depot is not found

    # Travel to the delivery site
    delivery_site = next(
        (site for site in delivery_sites if site.name == ticket.order_id), None
    )
    if delivery_site:
        yield env.process(
            travel_process(env, truck, delivery_site, ticket.travel_to_time)
        )
        # Unload the truck at the delivery site
        yield env.process(unloading_process(env, truck, delivery_site))
    else:
        print(f"Delivery site '{ticket.order_id}' not found for truck '{truck.name}'.")
        return  # Exit the process if delivery site is not found

    # Travel to the return depot
    return_depot = next(
        (depot for depot in depots if depot.name == ticket.return_depot), None
    )
    if return_depot:
        yield env.process(
            travel_process(env, truck, return_depot, ticket.travel_back_time)
        )
        # Update the truck's home depot to the return depot
        truck.home_depot = return_depot.name
        return_depot.add_truck(truck)
    else:
        print(
            f"Return depot '{ticket.return_depot}' not found for truck '{truck.name}'."
        )


# Main Simulation Execution Function
def run_simulation():
    # Initialize the simulation environment and entities
    env, depots, delivery_sites, trucks, tickets = initialize_simulation()
    # Assign trucks to their starting depots
    assign_trucks_to_depots(trucks, depots)
    # Start the continuous process of assigning tickets to available trucks
    env.process(assign_tickets(env, tickets, depots, delivery_sites))
    # Define the simulation run duration
    SIMULATION_TIME = 100  # Adjust as needed for your simulation
    # Run the simulation
    env.run(until=SIMULATION_TIME)


if __name__ == "__main__":
    run_simulation()
