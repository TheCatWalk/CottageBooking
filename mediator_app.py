from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import uvicorn
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
import io
from datetime import datetime, timedelta
import uuid
from Levenshtein import ratio
import json
import os


# Create a new FastAPI instance for the Mediator
mediator_app = FastAPI()

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Namespace definitions
COT = Namespace("http://users.jyu.fi/~kumapmxw/cottage-ontology.owl#")
SSWAP = Namespace("http://sswapmeet.sswap.info/sswap/")
RESOURCE = Namespace("http://127.0.0.1:8000/")

@mediator_app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})

# Preprocess RDG by replacing empty literals with default values
def preprocess_rdg(rdg_graph):
    for s, p, o in rdg_graph:
        if isinstance(o, Literal) and o.value == "":
            if o.datatype == XSD.int:
                rdg_graph.set((s, p, Literal(0, datatype=XSD.int)))
            elif o.datatype == XSD.dateTime:
                rdg_graph.set((s, p, Literal("1970-01-01T00:00:00", datatype=XSD.dateTime)))

# Postprocess RIG by restoring empty literals
def postprocess_rig(rig_graph):
    for s, p, o in list(rig_graph):
        if isinstance(o, Literal):
            if o.datatype == XSD.int and (o.value == "0" or o.value is None):
                rig_graph.remove((s, p, o))
                rig_graph.add((s, p, Literal("")))
            elif o.datatype == XSD.dateTime and (o.value is None or o.value.startswith("1970-01-01T")):
                rig_graph.remove((s, p, o))
                rig_graph.add((s, p, Literal("")))

# Update graph with form data
def update_graph_with_form_data(rig_graph, form_data):
    for booking_request in rig_graph.subjects(RDF.type, COT.BookingRequest):
        for prop, value in form_data.items():
            if value:
                rig_graph.set((booking_request, COT[prop], Literal(value)))

def extract_data_from_rrg(rrg_response_text):
    # Parse the RRG response
    rrg_graph = Graph()
    rrg_graph.parse(data=rrg_response_text, format="turtle")

    extracted_data = {}
    maps_to_node = None
    for s, p, o in rrg_graph.triples((None, SSWAP.mapsTo, None)):
        maps_to_node = o
        break

    if maps_to_node:
        print("Parsing mapsTo section...")
        for p, o in rrg_graph.predicate_objects(subject=maps_to_node):
            extracted_key = str(p).split('#')[-1]
            extracted_data[extracted_key] = str(o)
            print(f"Extracted {extracted_key}: {o}")
    else:
        print("No mapsTo section found.")
    return extracted_data

def generate_shifted_booking_results(extracted_data, maxShiftDays, startDate, duration, booker_name):
    html_content = "<h2>Booking Results</h2>"
    start_date_obj = datetime.strptime(startDate, '%Y-%m-%d')
    user_start_date = start_date_obj - timedelta(days=maxShiftDays)
    user_end_date = start_date_obj + timedelta(days=maxShiftDays)
    index = 1  # Initialize an index counter

    current_date = user_start_date
    while current_date <= user_end_date:
        booking_number = uuid.uuid4()
        html_content += "<div class='result-item'>"
        html_content += f"<div><p><strong>----------------Index: {index}</strong></p><hr></div>"
        html_content += f"<p>Booker Name: {booker_name}</p>"
        html_content += f"<p><strong>Shifted Booking Start Date:</strong> {current_date.strftime('%Y-%m-%d')}</p>"
        html_content += f"<p>Booking Number: {booking_number}</p>"
        html_content += f"<p><strong>Address:</strong> {extracted_data.get('hasAddress', 'Not available')}</p>"
        html_content += f"<p><strong>Image:</strong> <img src='{extracted_data.get('hasImageURL', '')}' alt='Cottage Image' style='width:100px;height:100px;'></p>"
        html_content += f"<p><strong>City Name:</strong> {extracted_data.get('cityName', 'Not available')}</p>"
        html_content += f"<p><strong>Distance from City:</strong> {extracted_data.get('distanceFromCity', 'Not available')} meters</p>"
        html_content += f"<p><strong>Distance from Lake:</strong> {extracted_data.get('distanceFromLake', 'Not available')} meters</p>"
        html_content += f"<p><strong>Number of Bedrooms:</strong> {extracted_data.get('numberOfBedrooms', 'Not available')}</p>"
        html_content += f"<p><strong>Number of Places:</strong> {extracted_data.get('numberOfPlaces', 'Not available')}</p>"
        booking_end_date = current_date + timedelta(days=duration - 1)
        html_content += f"<p><strong>Booking Period:</strong> {duration} days ({current_date.strftime('%Y-%m-%d')} to {booking_end_date.strftime('%Y-%m-%d')})</p>"
        html_content += "</div>"
        current_date += timedelta(days=1)
        index += 1  # Increment the index for each row
    return html_content

@mediator_app.get("/booking_form", response_class=HTMLResponse)
async def get_booking_form(request: Request):
    return templates.TemplateResponse("mediator_form.html", {"request": request})

@mediator_app.post("/submit_request", response_class=HTMLResponse)
async def submit_request(request: Request,
                         booking_service_url: str = Form(...),
                         booker_name: str = Form(...),
                         numberOfPlaces: int = Form(...),
                         numberOfBedrooms: int = Form(...),
                         cityName: str = Form(...),
                         distanceFromCity: int = Form(...),
                         distanceFromLake: int = Form(...),
                         startDate: str = Form(...),
                         duration: int = Form(...),
                         maxShiftDays: int = Form(...)
                         ):
    rdg_endpoint = booking_service_url.rstrip('/') + '/rdg'
    rdg_response = requests.get(rdg_endpoint)

    if rdg_response.status_code == 200:
        rdg_data = io.StringIO(rdg_response.text)
        rdg_graph = Graph()
        rdg_graph.parse(rdg_data, format="turtle")
        preprocess_rdg(rdg_graph)

        # Prepare form data
        form_data = {
            "booker_name": booker_name,
            "numberOfPlaces": str(numberOfPlaces),
            "numberOfBedrooms": str(numberOfBedrooms),
            "cityName": cityName,
            "distanceFromCity": str(distanceFromCity),
            "distanceFromLake": str(distanceFromLake),
            "startDate": startDate,
            "duration": str(duration),
            "maxShiftDays": str(maxShiftDays)
        }

        # Create a copy of the RDG graph for the RIG
        rig_graph = Graph()
        rig_graph += rdg_graph

        # Bind namespaces explicitly
        rig_graph.namespace_manager.bind("cot", COT)
        rig_graph.namespace_manager.bind("sswap", SSWAP)
        rig_graph.namespace_manager.bind("resource", RESOURCE)
        rig_graph.namespace_manager.bind("xsd", XSD)

        # Update RIG with form data and postprocess
        update_graph_with_form_data(rig_graph, form_data)
        postprocess_rig(rig_graph)

        # Serialize the RIG
        rig_data = rig_graph.serialize(format="turtle")
        print(rig_data)
        rrg_response = requests.post(booking_service_url + "/process_rig", data=rig_data, headers={"Content-Type": "text/turtle"})

        if rrg_response.status_code == 200:
            extracted_data = extract_data_from_rrg(rrg_response.text)
            html_content = generate_shifted_booking_results(extracted_data, maxShiftDays, startDate, duration, booker_name)
            return HTMLResponse(content=html_content)
        else:
            return HTMLResponse(content="Failed to process booking request.", status_code=500)

    else:
        return HTMLResponse(content="Failed to fetch RDG.", status_code=500)


@mediator_app.get("/align_ontology", response_class=HTMLResponse)
async def get_alignment_form(request: Request):
    return templates.TemplateResponse("alignment_form.html", {"request": request})

def align_terms(graph1, graph2):
    """
    Align each term from the hasMapping section of the base RDF graph (graph1)
    with the term from the external RDF graph (graph2) that has the highest Levenshtein ratio.
    Returns a list of tuples with base terms, their best matches, and the similarity score.
    """
    predicates_graph1 = set(p for s, p, o in graph1.triples((None, SSWAP.hasMapping, None)) for _, p, _ in graph1.triples((o, None, None)))
    predicates_graph2 = set(p for s, p, o in graph2.triples((None, SSWAP.hasMapping, None)) for _, p, _ in graph2.triples((o, None, None)))

    aligned_terms = {}
    for p1 in predicates_graph1:
        matches = [(str(p2), ratio(str(p1), str(p2))) for p2 in predicates_graph2]
        aligned_terms[str(p1)] = matches
    return aligned_terms

@mediator_app.post("/perform_alignment", response_class=HTMLResponse)
async def perform_alignment(request: Request, rdg_url: str = Form(...)):
    print("Received RDG URL for alignment:", rdg_url)

    # Fetch and parse the external RDG
    external_response = requests.get(rdg_url)
    if external_response.status_code != 200:
        return HTMLResponse(content="Failed to fetch external RDG.", status_code=500)

    external_rdg_graph = Graph()
    try:
        external_rdg_graph.parse(data=external_response.text, format="turtle")
    except Exception as e:
        return HTMLResponse(content=f"Error parsing external RDG: {e}", status_code=500)

    # Parse the mediator's RDG from a local file
    mediator_rdg_graph = Graph()
    try:
        mediator_rdg_graph.parse("RDG.ttl", format="turtle")
    except Exception as e:
        return HTMLResponse(content=f"Error parsing mediator's RDG: {e}", status_code=500)

    # Perform alignment
    alignment_results = align_terms(mediator_rdg_graph, external_rdg_graph)

    # Construct the response with dropdowns and pre-selected matches
    response_html = "<form action='/save_alignment' method='post'><h2>Alignment Results</h2>"
    response_html += "<table><tr><th>Base RDG Predicate</th><th>Possible Matches</th></tr>"

    for term1, matches in alignment_results.items():
        # Sort matches by score and get the highest scoring match
        matches_sorted = sorted(matches, key=lambda x: x[1], reverse=True)
        highest_scoring_match = matches_sorted[0][0] if matches_sorted else ""

        response_html += f"<tr><td>{term1}</td><td><select name='{term1}'>"
        for term2, score in matches_sorted:
            selected = " selected" if term2 == highest_scoring_match else ""
            response_html += f"<option value='{term2}'{selected}>{term2} (Score: {score:.2f})</option>"
        response_html += "</select></td></tr>"
    response_html += "</table><input type='submit' value='Save Alignment'></form>"
    return HTMLResponse(content=response_html)

@mediator_app.post("/save_alignment", response_class=HTMLResponse)
async def save_alignment(request: Request):
    form_data = await request.form()
    alignment_data = {key: value for key, value in form_data.items()}

    # Create the directory if it doesn't exist
    os.makedirs('Saved_Alignments', exist_ok=True)

    # Format current date and time for the filename
    current_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = f'Saved_Alignments/alignment-{current_time}.ttl'

    # Convert alignment data to TTL format
    ttl_content = ""
    for base_term, aligned_term in alignment_data.items():
        ttl_content += f'<{base_term}> <http://www.w3.org/2002/07/owl#sameAs> <{aligned_term}> .\n'

    # Save the alignments to a TTL file
    with open(filename, 'w') as file:
        file.write(ttl_content)

    return HTMLResponse(content=f"<p>Alignment saved successfully in {filename}.</p>")

if __name__ == "__main__":
    uvicorn.run(mediator_app, host="127.0.0.1", port=8002)
