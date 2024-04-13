import simpy

from src.datagen import generate_data
from src.simobj import SimEngine

data = generate_data()
# data.keys()

orders = data["orders"]
tickets = data["tickets"]
depots = data["depots"]
trucks = data["trucks"]

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

se.depots[0].ticket_queue
se.depots[0].loading_bay
se.trucks

# myticket = se.tickets[0]
myticket = se.get_ticket("ticket_01")
myticket.is_started
myticket.sim_ticket_start_time = 12
myticket.is_started

# myorder = [o for o in se.orders if o.order_id == myticket.order_id][0]
myorder = se.get_parent_order("ticket_01")
myorder.is_started
