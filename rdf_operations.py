from rdflib import Graph, Literal
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

def execute_sparql_query(graph, booker_name, numberOfPlaces, numberOfBedrooms, distanceFromLake, cityName, distanceFromCity, startDate, duration, maxShiftDays):
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

    start_date_obj = datetime.strptime(startDate, '%Y-%m-%d')
    for row in results:
        cottage_start_date = datetime.strptime(row['startDate'], '%Y-%m-%d')
        cottage_end_date = datetime.strptime(row['endDate'], '%Y-%m-%d')
        available_duration = (cottage_end_date - cottage_start_date).days

        # Calculate the user's flexible booking period
        user_start_date = start_date_obj - timedelta(days=maxShiftDays)
        user_end_date = start_date_obj + timedelta(days=maxShiftDays)

        # Check for overlap
        if ((cottage_start_date <= user_end_date) and (cottage_end_date >= user_start_date)) and available_duration >= duration:
            row_data = {
                'cottage': row['cottage'],
                'hasAddress': row['hasAddress'],
                'numberOfPlaces': row['numberOfPlaces'],
                'numberOfBedrooms': row['numberOfBedrooms'],
                'distanceFromLake': row['distanceFromLake'],
                'cityName': row['cityName'],
                'hasImageURL': row['hasImageURL'],
                'startDate': row['startDate'],
                'endDate': row['endDate'],
                'distanceFromCity': row['distanceFromCity'],
                'available_duration': available_duration  # Add calculated duration
            }
            filtered_results.append(row_data)

    return filtered_results

