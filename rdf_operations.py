from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF
from datetime import datetime, timedelta
import re


def load_rdf_data(file_path):
    graph = Graph()
    graph.parse(file_path, format="turtle")
    return graph

def calculate_date_range(start_date_str, shift_days_str):
    """Calculate the range of dates around a start date based on shift days."""
    shift_days = int(shift_days_str)  # Convert shift_days from string to integer
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    start_date_earliest = start_date - timedelta(days=shift_days)
    start_date_latest = start_date + timedelta(days=shift_days)
    return start_date_earliest.strftime('%Y-%m-%d'), start_date_latest.strftime('%Y-%m-%d')

def execute_sparql_query(graph, bookerName, numberOfPlaces, numberOfBedrooms, cityName, distanceFromCity, distanceFromLake, startDate, duration, shift):
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
    filtered_results = []

    # Adjusting the logic to use startDate and shift from the RIG
    start_date_obj = datetime.strptime(startDate, '%Y-%m-%dT%H:%M:%S')
    user_start_date = start_date_obj - timedelta(days=shift)
    user_end_date = start_date_obj + timedelta(days=shift)

    for row in results:
        cottage_start_date = datetime.strptime(row['startDate'], '%Y-%m-%d')
        cottage_end_date = datetime.strptime(row['endDate'], '%Y-%m-%d')

        if cottage_start_date <= user_end_date and cottage_end_date >= user_start_date:
            filtered_results.append(row)

    return filtered_results


def parse_rig(rig_graph):
    # Define the namespaces based on RDG.ttl and new.rdf
    COT = Namespace("http://users.jyu.fi/~kumapmxw/cottage-ontology.owl#")
    SSWAP = Namespace("http://sswapmeet.sswap.info/sswap/")
    REQUEST = Namespace("http://example.org/request/")

    # Find the request node in the RIG
    request_node = rig_graph.value(predicate=RDF.type, object=REQUEST.BookingRequest, any=False)

    # Extract parameters from the RIG
    params = {
        'bookerName': str(rig_graph.value(subject=request_node, predicate=REQUEST.bookerName)),
        'numberOfPlaces': int(rig_graph.value(subject=request_node, predicate=REQUEST.numberOfPlaces)),
        'numberOfBedrooms': int(rig_graph.value(subject=request_node, predicate=REQUEST.numberOfBedrooms)),
        'cityName': str(rig_graph.value(subject=request_node, predicate=REQUEST.cityName)),
        'distanceFromCity': int(rig_graph.value(subject=request_node, predicate=REQUEST.distanceFromCity)),
        'distanceFromLake': int(rig_graph.value(subject=request_node, predicate=REQUEST.distanceFromLake)),
        'startDate': str(rig_graph.value(subject=request_node, predicate=REQUEST.startDate)),
        'duration': int(rig_graph.value(subject=request_node, predicate=REQUEST.duration)),
        'shift': int(rig_graph.value(subject=request_node, predicate=REQUEST.shift))
    }
    return params
