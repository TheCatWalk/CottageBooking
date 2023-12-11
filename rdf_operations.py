from rdflib import Graph, Literal, Namespace, URIRef, RDF
from rdflib.namespace import RDF
from datetime import datetime, timedelta
import re


def load_rdf_data(file_path):
    graph = Graph()
    graph.parse(file_path, format="turtle")
    return graph


# def calculate_date_range(start_date_str, shift_days_str):
#     """Calculate the range of dates around a start date based on shift days."""
#     shift_days = int(shift_days_str)  # Convert shift_days from string to integer
#     start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
#     start_date_earliest = start_date - timedelta(days=shift_days)
#     start_date_latest = start_date + timedelta(days=shift_days)
#     return start_date_earliest.strftime('%Y-%m-%d'), start_date_latest.strftime('%Y-%m-%d')


def execute_sparql_query(graph, booker_name, numberOfPlaces, numberOfBedrooms, distanceFromLake, cityName,
                         distanceFromCity, startDate, duration, maxShiftDays):
    sparql_query = f"""
        PREFIX cot: <http://users.jyu.fi/~kumapmxw/cottage-ontology.owl#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT ?cottage ?hasAddress ?numberOfPlaces ?numberOfBedrooms ?distanceFromLake ?cityName ?hasImageURL ?startDate ?endDate ?distanceFromCity
        WHERE {{
            ?cottage rdf:type cot:cottage ;
                     cot:hasAddress ?hasAddress ;
                     cot:numberOfPlaces ?numberOfPlaces ;
                     cot:numberOfBedrooms ?numberOfBedrooms ;
                     cot:distanceFromLake ?distanceFromLake ;
                     cot:cityName ?cityName ;
                     cot:hasImageURL ?hasImageURL ;
                     cot:distanceFromCity ?distanceFromCity ;
                     cot:startDate ?startDate ;
                     cot:endDate ?endDate .

            FILTER (?numberOfPlaces >= {numberOfPlaces}) .
            FILTER (?numberOfBedrooms >= {numberOfBedrooms}) .
            FILTER (?distanceFromLake <= {distanceFromLake}) .
            FILTER (?distanceFromCity <= {distanceFromCity}) .
            FILTER (STR(?cityName) = "{cityName}") .
        }}
    """
    results = graph.query(sparql_query)
    print("Raw SPARQL results:", list(results))
    filtered_results = []

    # Debugging: Print received parameters
    print("Received parameters for SPARQL query:")
    print(f"Booker Name: {booker_name}, Number of Places: {numberOfPlaces}, Number of Bedrooms: {numberOfBedrooms}, "
          f"Distance From Lake: {distanceFromLake}, City Name: {cityName}, Distance From City: {distanceFromCity}, "
          f"Start Date: {startDate}, Duration: {duration}, Max Shift Days: {maxShiftDays}")

    # Adjusting the logic to use startDate and shift from the RIG
    try:
        start_date_obj = datetime.strptime(startDate, '%Y-%m-%d')
    except TypeError as e:
        print(f"Error parsing startDate: {e}")
        start_date_obj = datetime.now()  # Fallback to current date if parsing fails
    except ValueError as e:
        print(f"Invalid startDate format: {e}")
        start_date_obj = datetime.now()  # Fallback to current date if parsing fails

    user_start_date = start_date_obj - timedelta(days=maxShiftDays)
    user_end_date = start_date_obj + timedelta(days=maxShiftDays)

    for row in results:
        cottage_start_date = datetime.strptime(row['startDate'], '%Y-%m-%d')
        cottage_end_date = datetime.strptime(row['endDate'], '%Y-%m-%d')

        if cottage_start_date <= user_end_date and cottage_end_date >= user_start_date:
            filtered_results.append(row)

    return filtered_results


def parse_rig(rig_graph):
    # Define the namespaces based on RDG.ttl and new.rdf
    REQUEST = Namespace("http://example.org/request/")

    # Find the request node in the RIG
    request_node = rig_graph.value(predicate=RDF.type, object=REQUEST.BookingRequest, any=False)

    # Debugging: Print the entire graph for inspection
    print("RIG Graph:", rig_graph.serialize(format="turtle"))

    # Extract parameters from the RIG
    try:
        # Initialize parameters dictionary
        params = {
            'booker_name': '',
            'numberOfPlaces': 0,
            'numberOfBedrooms': 0,
            'cityName': '',
            'distanceFromCity': 0.0,
            'distanceFromLake': 0.0,
            'startDate': '',
            'duration': 0,
            'maxShiftDays': 0
        }

        # Iterate over the triples in the graph
        for s, p, o in rig_graph:
            if p == REQUEST.booker_name:
                params['booker_name'] = str(o)
            elif p == REQUEST.numberOfPlaces:
                params['numberOfPlaces'] = int(o)
            elif p == REQUEST.numberOfBedrooms:
                params['numberOfBedrooms'] = int(o)
            elif p == REQUEST.cityName:
                params['cityName'] = str(o)
            elif p == REQUEST.distanceFromCity:
                params['distanceFromCity'] = float(o)
            elif p == REQUEST.distanceFromLake:
                params['distanceFromLake'] = float(o)
            elif p == REQUEST.startDate:
                params['startDate'] = str(o)
            elif p == REQUEST.duration:
                params['duration'] = int(o)
            elif p == REQUEST.maxShiftDays:
                params['maxShiftDays'] = int(o)

        # Debug: Print extracted parameters
        print("Extracted Parameters:")
        print(params)

        return params
    except Exception as e:
        print(f"Error parsing RIG: {e}")
        raise e
