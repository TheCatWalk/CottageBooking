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

def execute_sparql_query(graph, booker_name, num_places, num_bedrooms, max_lake_dist, city, max_city_dist, required_days, start_date, shift_days):
    start_date_earliest, start_date_latest = calculate_date_range(start_date, shift_days)

    sparql_query = f"""
        PREFIX ex: <http://example.org#>

        SELECT ?cottage ?address ?places ?bedrooms ?distanceToLake ?nearestCity ?imageURL ?startDate ?availableDays ?distanceToCity
        WHERE {{
            ?cottage rdf:type ex:Cottage ;
                     ex:address ?address ;
                     ex:places ?places ;
                     ex:bedrooms ?bedrooms ;
                     ex:distanceToLake ?distanceToLake ;
                     ex:nearestCity ?nearestCity ;
                     ex:imageURL ?imageURL ;
                     ex:distanceToCity ?distanceToCity ;
                     ex:startDate ?startDate ;
                     ex:availableDays ?availableDays .

            FILTER (?places >= {num_places}) .
            FILTER (?bedrooms >= {num_bedrooms}) .
            FILTER (?distanceToLake <= {max_lake_dist}) .
            FILTER (?distanceToCity <= {max_city_dist}) .
            FILTER (?nearestCity = "{city}") .
            FILTER (?availableDays >= {required_days}) .
            FILTER (str(?startDate) >= "{start_date_earliest}" && str(?startDate) <= "{start_date_latest}")
        }}
    """
    return graph.query(sparql_query)
