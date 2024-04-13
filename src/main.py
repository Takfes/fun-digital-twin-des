import simpy

from src.datagen import generate_data
from src.simobj import SimEngine

data = generate_data()
# data.keys()

orders = data["orders"]
tickets = data["tickets"]
depots = data["depots"]
trucks = data["trucks"]

tickets.ship_loc.value_counts()

# data["tickets"].columns
# round(data["tickets"].shape[0] / 2)

env = simpy.Environment()

se = SimEngine(
    env=env,
    orderlist=data["orders"],
    ticketlist=data["tickets"],
    depotlist=data["depots"],
    trucklist=data["trucks"],
)

# GENERATE TICKETS
len(se.tickets)
env.process(se.ticket_generator())
env.run()

# TICKETS
# myticket = se.tickets[0]
myticket = se.get_ticket("ticket_01")
myticket.is_started
myticket.ship_loc
# myticket.sim_ticket_start_time = 12
# myticket.is_started

# ORDERS
# myorder = [o for o in se.orders if o.order_id == myticket.order_id][0]
myorder = se.get_parent_order("ticket_01")
myorder.is_started

# DEPOTS
# se.depots
# mydepot.ticket_queue.capacity
mydepot = se.get_depot(myticket.ship_loc)
mydepot
mydepot.ticket_queue.items
# mydepot.ticket_queue.put(myticket)
mydepot.add_ticket(myticket)
mydepot.ticket_queue.items
len(mydepot.ticket_queue.items)
mydepot.queue_size
