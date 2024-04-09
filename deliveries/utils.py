import math
import random

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()

DEPOTS = 4
AREA_BOUNDS = {
    "lat_min": 25.90,
    "lat_max": 26.50,
    "lon_min": -80.00,
    "lon_max": -80.40,
}

# 26.453936, -80.293473
# 26.442077, -80.063882
# 25.909135, -80.132318
# 25.919063, -80.399438


def haversine(lat1, lon1, lat2, lon2):
    R = 3959.87433
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)
    a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(
        math.radians(lat1)
    ) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


def generate_quantities():
    n_orders = random.randint(5, 10)
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
        return random.randint(0, 7)
    elif quantity >= 70:
        return random.randint(4, 13)
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


def generate_order(
    n_loads: int,
    unload_time: int,
    depot_prep_time: int = 30,
    site_prep_time: int = 10,
    site_clean_time: int = 10,
) -> pd.DataFrame:
    """
    Generates a dataframe with the required data.
    """

    my_range = range(1, n_loads + 1)
    series_loads = list(my_range)
    series_unload_minutes = [unload_time for _ in my_range]
    series_depot_prep_time = [depot_prep_time for _ in my_range]
    series_site_prep_time = [site_prep_time for _ in my_range]
    series_site_clean_time = [site_clean_time for _ in my_range]
    series_dispatch_time = [unload_time for _ in my_range]
    series_dispatch_time.insert(0, 0)
    series_dispatch_time.pop()

    temp = pd.DataFrame(
        {
            "load_number": series_loads,
            "dispatch_time": series_dispatch_time,
            "depot_prep_time": series_depot_prep_time,
            "site_prep_time": series_site_prep_time,
            "unload_time": series_unload_minutes,
            "site_clean_time": series_site_clean_time,
        }
    )
    return temp


"""
orders :
order_id
due_time
quantity
customer
customer_loc
sched_loc
unload_mins

tickets :
ticket_id
load_number
ship_loc
return_loc
distance
"""

quantities = generate_quantities()
n_orders = len(quantities)
print(quantities)
print(f"Total Quantity : {sum(quantities)} across {len(quantities)} orders")
depots = generate_depot_locations(n=DEPOTS, bounds=AREA_BOUNDS)
generate_delivery_sites(bounds=AREA_BOUNDS, depots=depots)

for i, q in enumerate(quantities, start=1):
    delivery_sites = generate_delivery_sites(bounds=AREA_BOUNDS, depots=depots)

    order_id = f"order_{i:02}"
    due_time = generate_due_time(q)
    customer = fake.company()
    customer_loc = delivery_sites["customer_loc"]
    sched_loc = list(delivery_sites["distance_matrix"].keys())[0]
    unload_minutes = generate_unload_minutes(q)
    n_loads = int(q / 10)

    generate_order(n_loads, unload_minutes)
