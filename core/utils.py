from dataclasses import dataclass
import hashlib
import math
import csv


@dataclass
class City:
    city: str
    lat: float
    lng: float
    country: str
    iso2: str
    capital: str
    population: int
    population_proper: int


cities: list[City] = []


def get_cities():
    if len(cities) > 0:
        return cities

    with open("core/data/et.csv", "r") as file:
        reader = csv.DictReader(file)
        for row in reader:
            cities.append(
                City(
                    city=row["city"],
                    lat=float(row["lat"]),
                    lng=float(row["lng"]),
                    country=row["country"],
                    iso2=row["iso2"],
                    capital=row["capital"],
                    population=int(row["population"]),
                    population_proper=int(row["population_proper"]),
                )
            )
    return cities


def get_city(city: str):
    cities = get_cities()
    for c in cities:
        if c.city == city:
            return c

    return None


def haversine(lat1: float, lon1: float, lat2: float, lon2: float):
    # Convert latitude and longitude from degrees to radians
    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in kilometers. Use 3956 for miles. Determines return value units.
    r = 6371

    # Calculate the result
    distance = c * r

    return distance


def base36encode(number):
    """Convert an integer to a base36 string."""
    chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    result = ""
    while number > 0:
        number, remainder = divmod(number, 36)
        result = chars[remainder] + result
    return result or "0"


def generate_tracking_number(shipment_id):
    # Convert shipment ID to base36
    base36_id = base36encode(shipment_id)

    # Generate a short hash of the shipment ID
    hash_object = hashlib.md5(str(shipment_id).encode())
    hash_str = hash_object.hexdigest()[
        :4
    ].upper()  # Take the first 4 characters of the hash

    # Combine base36 ID and hash to form the tracking number
    tracking_number = f"{base36_id}-{hash_str}"

    return tracking_number
