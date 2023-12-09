from rdflib import Graph

from rdf_operations import parse_rig

def main():
    # Load the test RIG
    rig_graph = Graph().parse("test_rig.ttl", format="turtle")
    parsed_params = parse_rig(rig_graph)
    print(parsed_params)

if __name__ == "__main__":
    main()
