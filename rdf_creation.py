import random
import string
from datetime import datetime, timedelta
from rdflib import Graph, URIRef, Literal, Namespace, RDF

# Constants
CITIES = ["Helsinki", "Jyvaskyla", "Tampere"]
ADDRESS_SUFFIXES = ["Street", "Lane", "Road", "Avenue", "Boulevard", "Circle", "Park"]
MONTHS = {"01.2024": (1, 31), "02.2024": (1, 29)}

# Namespace
EX = Namespace("http://example.org#")

def generate_random_address(city):
    """ Generate a random address for a given city. """
    suffix = random.choice(ADDRESS_SUFFIXES)
    number_or_letter = random.choice(string.ascii_letters + string.digits)
    return f"{city} {number_or_letter} {suffix}"

def generate_random_date(month_year):
    """ Generate a random date within the specified month and year, formatted as YYYY-MM-DD. """
    month, year = month_year.split('.')
    start_day, end_day = MONTHS[month_year]
    random_day = random.randint(start_day, end_day)
    date = datetime(int(year), int(month), random_day)
    return date.strftime('%Y-%m-%d')

def create_cottage_instance(g, instance_number):
    """ Create a new Cottage instance with random data. """
    city = random.choice(CITIES)
    cottage_uri = URIRef(f"http://example.org#Cottage{instance_number}")
    g.add((cottage_uri, RDF.type, EX.Cottage))
    g.add((cottage_uri, EX.address, Literal(generate_random_address(city))))
    g.add((cottage_uri, EX.places, Literal(random.randint(1, 5))))
    g.add((cottage_uri, EX.bedrooms, Literal(random.randint(1, 4))))
    g.add((cottage_uri, EX.distanceToLake, Literal(random.randint(10, 1000))))
    g.add((cottage_uri, EX.nearestCity, Literal(city)))
    g.add((cottage_uri, EX.distanceToCity, Literal(random.randint(6, 20))))
    g.add((cottage_uri, EX.availableDays, Literal(random.randint(1, 14))))
    month_year = random.choice(list(MONTHS.keys()))
    g.add((cottage_uri, EX.startDate, Literal(generate_random_date(month_year))))
    g.add((cottage_uri, EX.imageURL, Literal(f"http://example.org/images/cottage{instance_number}.jpg")))

def update_ontology(number_of_instances, file_path="ontology.rdf"):
    """ Update the ontology with a specified number of new cottage instances. """
    g = Graph()
    g.bind("ex", EX)
    g.parse(file_path, format="turtle")

    for i in range(number_of_instances):
        create_cottage_instance(g, i + 1)

    g.serialize(destination=file_path, format="turtle")

if __name__ == "__main__":
    num_instances = int(input("Enter the number of instances to create: "))
    update_ontology(num_instances)
