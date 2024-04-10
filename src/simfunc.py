def ticket_generator():
    """
    spawn tickets in the simulation
    can accommodate different logics :
    vanilla, track site queue, track site progress
    # ! push tickets to Depot queues
    """
    pass


def ticket_process():
    """
    simulates the steps required to complete the ticket
    depot_prep > travel > site_prep > unload > site_clean > travel_back
    # ! release truck resource at the end of the process
    """
    pass


def truck_assignment():
    """
    assign trucks to tickets
    monitors ticket queues and truck availability, assigning tickets to trucks based on predefined rules or priorities.
    """
    pass


def siminit():
    """
    initialize the simulation
    """
    pass
