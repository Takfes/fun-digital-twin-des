from src.datagen import generate_data

data = generate_data()

data.keys()

data["orders"]
data["tickets"]
data["depots"]

round(data["tickets"].shape[0] / 2)
data["trucks"]
