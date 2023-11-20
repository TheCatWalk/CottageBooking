from rdflib import Graph, Literal
from datetime import datetime, timedelta
import re

def load_rdf_data(file_path):
    graph = Graph()
    graph.parse(file_path, format="turtle")
    return graph

def execute_sparql_query(graph, booker_name, num_places, num_bedrooms, max_lake_dist, city, max_city_dist, required_days, start_date, max_shift_days):
    sparql_query = f"""
        PREFIX ex: <http://example.org#>

        SELECT ?cottage ?address ?places ?bedrooms ?distanceToLake ?nearestCity ?imageURL ?startDate ?availableDays ?maxShiftDays
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
                     ex:availableDays ?availableDays ;
                     ex:maxShiftDays ?maxShiftDays .

            FILTER (?places >= {num_places}) .
            FILTER (?bedrooms >= {num_bedrooms}) .
            FILTER (?distanceToLake <= {max_lake_dist}) .
            FILTER (?distanceToCity <= {max_city_dist}) .
            FILTER (?nearestCity = "{city}") .
            FILTER (?availableDays >= {required_days}) .
            FILTER (str(?startDate) <= "{start_date}") .
            FILTER (?maxShiftDays >= {max_shift_days}).
        }}
    """
    return graph.query(sparql_query)
