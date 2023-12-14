import uuid
import requests
import re
from datetime import datetime, timedelta
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from rdflib import Graph, Namespace, Literal, URIRef, RDF
from Levenshtein import ratio

mediator_app = FastAPI()

# Function to fetch RDG data
def fetch_rdg_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        print("Fetched RDG Data (first 500 chars):", response.text[:500])  # Print first 500 characters for debugging
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching RDG data: {e}")
        return None

def extract_properties_rdg0():
    with open('rdg0.ttl', 'r') as file:
        content = file.read()
        # Extract properties and flatten the tuple structure
        properties = re.findall(r'\brequest:(\w+)|\bcot:(\w+)', content)
        return [prop for sublist in properties for prop in sublist if prop]

# Alignment related functions
def extract_properties(data, regex):
    properties = re.findall(regex, data)
    # Filter out empty matches
    filtered_properties = [prop for prop in properties if prop]
    print(f"Regex pattern: {regex}")
    print(f"Extracted properties using '{regex}': {filtered_properties}")  # Debugging statement
    return filtered_properties

def calculate_similarity(property1, property2):
    return ratio(property1, property2)

def compare_with_other_ontologies(ontology0_properties, other_ontology):
    comparison_results = {}
    for prop0 in ontology0_properties:
        highest_similarity = 0
        most_similar_property = None
        for prop in other_ontology:
            similarity = calculate_similarity(prop0, prop)
            if similarity > highest_similarity:
                highest_similarity = similarity
                most_similar_property = prop
        comparison_results[prop0] = (most_similar_property, highest_similarity)
    return comparison_results

# Endpoint for alignment
@mediator_app.post("/perform_alignment")
async def perform_alignment(rdg_url: str = Form(...)):
    rdg_data = fetch_rdg_data(rdg_url)
    if not rdg_data:
        return HTMLResponse(content="<p>Failed to fetch RDG data from the URL.</p>")

    ontology0_properties = extract_properties_rdg0()
    if not ontology0_properties:
        return HTMLResponse(content="<p>Failed to extract properties from RDG0.</p>")

    # Determine the correct regex pattern for the fetched RDG data based on the URL
    regex_pattern = r'\bcottageOnt:(\w+)' if "rdg1" in rdg_url else r'\bcottage:(\w+)'
    other_ontology_properties = extract_properties(rdg_data, regex_pattern)

    if not other_ontology_properties:
        return HTMLResponse(content="<p>Failed to extract properties from fetched RDG data.</p>")

    alignment_results = compare_with_other_ontologies(ontology0_properties, other_ontology_properties)
    if not alignment_results:
        return HTMLResponse(content="<p>No alignment results found.</p>")

    response_html = "<h2>Alignment Results</h2>"
    for prop0, (prop, similarity) in alignment_results.items():
        response_html += f"<p>Alignment: '{prop0}' (RDG0) <-> '{prop}' (Other RDG), Highest Similarity: {similarity:.2f}</p>"

    return HTMLResponse(content=response_html)




@mediator_app.get("/", response_class=HTMLResponse)
async def get_mediator_form():
    html_content = """
        <html>
        <head>
            <title>Mediator Service</title>
            <!-- Styles and other head elements -->
        </head>
        <body>
            <h2>Mediator for Cottage Booking</h2>
            <!-- Alignment Section -->
            <h3>Ontology Alignment</h3>
            <form action="/perform_alignment" method="post">
                RDG URL: <input type="text" name="rdg_url" placeholder="Enter RDG URL"><br>
                <input type="submit" value="Align">
            </form>
            <hr>
            
            <!-- Existing Booking Section -->
            <h3>Search for Cottage Bookings</h3>
            <form action="/mediate" method="post">
                Cottage Booking Service URL: <input type="text" name="booking_service_url" value="http://127.0.0.1:8000/invoke"><br>
                Name of Booker: <input type="text" name="booker_name" value="Test Booker"><br>
                Number of Places (People): <input type="number" name="numberOfPlaces" value="4"><br>
                Number of Bedrooms: <input type="number" name="numberOfBedrooms" value="3"><br>
                City: <input type="text" name="cityName" value="Jyvaskyla"><br>
                Distance to City (km): <input type="number" name="distanceFromCity" value="300"><br>
                Distance to Lake (m): <input type="number" name="distanceFromLake" value="30"><br>
                Booking Start Date (yyyy-mm-dd): <input type="text" name="startDate" value="2023-07-01"><br>
                Booking Duration (days): <input type="number" name="duration" value="5"><br>
                Max Shift Days: <input type="number" name="maxShiftDays" value="2"><br>
                <input type="submit" value="Submit">
            </form>
        </body>
        </html>
    """
    return HTMLResponse(content=html_content)


#fOR crEAting RIG With RDG (and validate)
# @mediator_app.post("/mediate", response_class=HTMLResponse)
# async def mediate_request(request: Request, booking_service_url: str = Form(...)):
#     try:
#         form_data = await request.form()
#
#         # Construct the RIG based on RDG.ttl structure
#         rig_graph = Graph()
#         REQUEST = Namespace("http://example.org/request/")
#         request_node = rdg_graph.value(predicate=RDF.type, object=REQUEST.BookingRequest, any=False)
#
#         for key, value in form_data.items():
#             if key != "booking_service_url":
#                 predicate = URIRef(f"http://example.org/request/{key}")
#                 rig_graph.add((request_node, predicate, Literal(value)))


@mediator_app.post("/mediate", response_class=HTMLResponse)
async def mediate_request(request: Request, booking_service_url: str = Form(...)):
    try:
        form_data = await request.form()

        # Construct the RIG (Request Invocation Graph) based on RDG.ttl structure
        rig_graph = Graph()
        REQUEST = Namespace("http://example.org/request/")
        request_node = URIRef("http://example.org/request/BookingRequest")

        for key, value in form_data.items():
            if key != "booking_service_url":
                predicate = URIRef(f"http://example.org/request/{key}")
                rig_graph.add((request_node, predicate, Literal(value)))

        # Serialize the RIG to Turtle format
        rig_data = rig_graph.serialize(format="turtle")

        # Send RIG to the Cottage Booking service's invoke endpoint
        response = requests.post(booking_service_url, data=rig_data, headers={"Content-Type": "text/turtle"})
        rdf_data = response.json().get('rrg', '')

        if not rdf_data:
            return HTMLResponse(content="No RDF data received from the Cottage Booking service.")

        # Parse the RDF response
        response_graph = Graph().parse(data=rdf_data, format="turtle")
        response_html = "<h2>Mediator Service Output</h2>"
        RESPONSE = Namespace("http://example.org/response/")
        COT = Namespace("http://users.jyu.fi/~kumapmxw/cottage-ontology.owl#")

        booker_name = form_data.get("booker_name", "No Booker Name")
        start_date_str = form_data.get("startDate", "")
        duration = int(form_data.get("duration", 0))
        max_shift_days = int(form_data.get("maxShiftDays", 0))

        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            user_start_date = start_date - timedelta(days=max_shift_days)
            user_end_date = start_date + timedelta(days=max_shift_days)
        except ValueError:
            response_html += "<p>Invalid Start Date</p>"
            return HTMLResponse(content=response_html)

        for response_node in response_graph.subjects(RDF.type, RESPONSE.CottageResponse):
            current_date = user_start_date
            while current_date <= user_end_date:
                booking_number = uuid.uuid4()

                # Extract start and end dates from the response
                cottage_start_date_str = str(response_graph.value(response_node, COT.startDate) or "")
                cottage_end_date_str = str(response_graph.value(response_node, COT.endDate) or "")
                cottage_start_date = datetime.strptime(cottage_start_date_str, '%Y-%m-%d')
                cottage_end_date = datetime.strptime(cottage_end_date_str, '%Y-%m-%d')

                if cottage_start_date <= current_date <= cottage_end_date:
                    date_label = "Booking Start Date" if current_date == start_date else "Shifted Booking Start Date"

                    # Extract other details from the RDF graph
                    address = str(response_graph.value(response_node, COT.hasAddress) or "No Address")
                    num_places = str(response_graph.value(response_node, COT.numberOfPlaces) or "Not Specified")
                    num_bedrooms = str(response_graph.value(response_node, COT.numberOfBedrooms) or "Not Specified")
                    image_url = str(response_graph.value(response_node, COT.hasImageURL) or "")
                    city_name = str(response_graph.value(response_node, COT.cityName) or "Not Specified")
                    distance_city = str(response_graph.value(response_node, COT.distanceFromCity) or "Not Specified")
                    distance_lake = str(response_graph.value(response_node, COT.distanceFromLake) or "Not Specified")

                    # Append the details to the HTML content
                    response_html += "<div>"
                    response_html += f"<p>Booker Name: {booker_name}</p>"
                    response_html += f"<p>Booking Number: {booking_number}</p>"
                    response_html += f"<p>{date_label}: {current_date.strftime('%Y-%m-%d')}</p>"
                    response_html += f"<p>Booking Period: {duration} days</p>"
                    response_html += f"<p>Address: {address}</p>"
                    response_html += f"<p>Number of Places: {num_places}</p>"
                    response_html += f"<p>Number of Bedrooms: {num_bedrooms}</p>"
                    response_html += f"<p>City: {city_name}</p>"
                    response_html += f"<p>Distance to City: {distance_city} km</p>"
                    response_html += f"<p>Distance to Lake: {distance_lake} m</p>"
                    if image_url:
                        response_html += f'<p>Image: <img src="{image_url}" alt="Cottage Image" style="width:100px;height:100px;"></p>'
                    response_html += "</div><hr>"

                current_date += timedelta(days=1)

        return HTMLResponse(content=response_html)
    except Exception as e:
        return HTMLResponse(content=f"An error occurred: {str(e)}", status_code=500)




if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mediator_app, host="127.0.0.1", port=5001)
