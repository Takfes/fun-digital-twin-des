import math
import random

import pandas as pd
from faker import Faker


def haversine(lat1, lon1, lat2, lon2):
    R = 3959.87433
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return round(distance, 2)


def generate_quantities(min_orders=5, max_orders=10):
    n_orders = random.randint(min_orders, max_orders)
    quantities = [20, 40, 60, 90, 100, 120, 150, 200, 300, 400]
    probabilities = [0.14, 0.18, 0.16, 0.14, 0.12, 0.08, 0.06, 0.04, 0.04, 0.04]
    orders_discrete = [
        random.choices(quantities, weights=probabilities, k=1)[0]
        for _ in range(n_orders)
    ]
    orders = [
        round(random.triangular(x - x / 2, x + x / 2, x) / 10) * 10
        for x in orders_discrete
    ]
    return sorted(orders, reverse=True)


def generate_depot_locations(n, bounds):
    depots = {}
    for i in range(1, n + 1):
        lat = round(random.uniform(bounds["lat_min"], bounds["lat_max"]), 8)
        lon = round(random.uniform(bounds["lon_min"], bounds["lon_max"]), 8)
        depots[f"depot_{i}"] = (lat, lon)
    return depots


def generate_delivery_sites(bounds, depots, max_distance=60):
    while True:
        lat = random.uniform(bounds["lat_min"], bounds["lat_max"])
        lon = random.uniform(bounds["lon_min"], bounds["lon_max"])
        distances = {k: haversine(lat, lon, v[0], v[1]) for k, v in depots.items()}
        sorted_distances = dict(sorted(distances.items(), key=lambda x: x[1]))
        if list(sorted_distances.values())[0] <= max_distance:
            return {
                "customer_loc": (lat, lon),
                "distance_matrix": sorted_distances,
            }


def generate_due_time(quantity):
    if quantity >= 170:
        return random.randint(3, 7)
    elif quantity >= 70:
        return random.randint(6, 11)
    elif quantity >= 40:
        return random.randint(10, 13)
    else:
        return random.randint(12, 14)


def generate_unload_minutes(quantity):
    if quantity >= 170:
        return random.randint(5, 15)
    elif quantity >= 70:
        return random.randint(15, 30)
    elif quantity >= 40:
        return random.randint(25, 45)
    else:
        return random.randint(45, 60)


def generate_load_minutes():
    return round(random.triangular(3, 11, 6))


def generate_site_prep_minutes():
    return round(random.triangular(1, 30, 10))


def generate_trucks(number_of_trucks, depots):
    trucks = []
    for t in range(1, number_of_trucks + 1):
        truck_id = f"truck_{t:02}"
        homeplant = random.choices(list(depots.keys()))[0]
        clock_in = random.randint(1, 5)
        clock_out = random.randint(13, 17)
        trucks.append(
            {
                "truck_id": truck_id,
                "homeplant": homeplant,
                "clock_in": clock_in,
                "clock_out": clock_out,
            }
        )
    return pd.DataFrame(trucks)


def generate_data(
    min_orders=5,
    max_orders=10,
    number_of_depots=4,
    number_of_trucks=None,
    minutes_per_mile=1.5,
    bounds=None,
):
    if bounds is None:
        bounds = {
            "lat_min": 25.90,
            "lat_max": 26.50,
            "lon_min": -80.00,
            "lon_max": -80.40,
        }
    fake = Faker()
    quantities = generate_quantities(min_orders, max_orders)
    print(quantities)
    print(f"Quantity : {sum(quantities)} | Orders : {len(quantities)}")
    depots = generate_depot_locations(n=number_of_depots, bounds=bounds)

    j = 1
    orders = []
    tickets = []

    for i, q in enumerate(quantities, start=1):
        # sample delivery sites
        delivery_sites = generate_delivery_sites(bounds=bounds, depots=depots)

        # make order data
        order_id = f"order_{i:02}"
        due_time = generate_due_time(q)
        due_time_mins = due_time * 60
        customer = fake.company()
        customer_loc = delivery_sites["customer_loc"]
        sched_loc = list(delivery_sites["distance_matrix"].keys())[0]
        load_minutes = generate_load_minutes()
        site_prep_minutes = generate_site_prep_minutes()
        unload_minutes = generate_unload_minutes(q)
        n_loads = int(q / 10)

        # append orders
        orders.append(
            {
                "order_id": order_id,
                "quantity": q,
                "due_time": due_time,
                "due_time_mins": due_time_mins,
                "customer": customer,
                "customer_loc": customer_loc,
                "sched_loc": sched_loc,
                "load_minutes": load_minutes,
                "site_prep_minutes": site_prep_minutes,
                "unload_mins": unload_minutes,
                "n_loads": n_loads,
            }
        )

        # make ticket data
        for i in range(1, n_loads + 1):
            ticket_id = f"ticket_{j:02}"
            j += 1
            load_number = i

            # generate ship and return locations
            if q > 100:
                ship_loc = random.choices(
                    list(depots.keys())[:2], weights=[0.8, 0.2], k=1
                )[0]
                return_loc = random.choices(
                    list(depots.keys())[:3], weights=[0.7, 0.2, 0.1], k=1
                )[0]
            else:
                ship_loc = list(depots.keys())[0]
                return_loc = random.choices(
                    list(depots.keys())[:2], weights=[0.8, 0.2], k=1
                )[0]

            # calculate travel duration based on site distance
            distance_to = delivery_sites["distance_matrix"][ship_loc]
            distance_back = delivery_sites["distance_matrix"][return_loc]
            travel_minutes_to = round(distance_to * minutes_per_mile)
            travel_minutes_back = round(distance_back * minutes_per_mile)

            # calculate ticket timestamps
            ticket_arrive_time = due_time_mins + (load_number - 1) * unload_minutes
            ticket_start_time = (
                ticket_arrive_time
                - load_minutes
                - travel_minutes_to
                - site_prep_minutes
            )

            tickets.append(
                {
                    "order_id": order_id,
                    "ticket_id": ticket_id,
                    "load_number": load_number,
                    "ticket_start_time": ticket_start_time,
                    "ticket_arrive_time": ticket_arrive_time,
                    "load_minutes": load_minutes,
                    "site_prep_minutes": site_prep_minutes,
                    "unload_mins": unload_minutes,
                    "ship_loc": ship_loc,
                    "distance_to": distance_to,
                    "travel_minutes_to": travel_minutes_to,
                    "return_loc": return_loc,
                    "distance_back": distance_back,
                    "travel_minutes_back": travel_minutes_back,
                }
            )

    data = {}
    data["orders"] = pd.DataFrame(orders)
    data["tickets"] = pd.DataFrame(tickets)
    data["depots"] = pd.DataFrame(depots).T.rename(columns={0: "lat", 1: "lon"})

    if number_of_trucks is None:
        number_of_trucks = round(data["tickets"].shape[0] / 2)
    data["trucks"] = generate_trucks(number_of_trucks, depots)

    return data
