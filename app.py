from datetime import timedelta, datetime
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from mediator_app import SSWAP
from rdf_operations import load_rdf_data, execute_sparql_query
import uvicorn
import uuid
from rdflib import Graph, Namespace, Literal, BNode, URIRef
from rdflib.namespace import RDF, XSD, NamespaceManager


app = FastAPI()
ontology = load_rdf_data("new.rdf")  # Updated to load new.rdf

app.mount("/static", StaticFiles(directory="."), name="static")

COT = Namespace("http://users.jyu.fi/~kumapmxw/cottage-ontology.owl#")

@app.get("/rdg")
async def get_rdg():
    return FileResponse('RDG.ttl', media_type='text/turtle')

@app.get("/", response_class=HTMLResponse)
async def get_search_form():
    html_content = """
        <html>
        <head>
            <title>Cottage Booking</title>
            <!-- Styles and other head elements -->
        </head>
        <body>
            <h2>Search for Cottage Bookings</h2>
            <form action="/search_cottages" method="post">
                Name of Booker: <input type="text" name="booker_name" value="Test Booker"><br>
                Number of Places (People) [1-10]: <input type="number" name="numberOfPlaces" value="4" min="1" max="10"><br>
                Number of Bedrooms [1-5]: <input type="number" name="numberOfBedrooms" value="3" min="1" max="5"><br>
                City [e.g., Jyvaskyla, Rovaniemi, Oulu]: <input type="text" name="cityName" value="Jyvaskyla"><br>
                Max Distance to City (kilometers) [100-500]: <input type="number" name="distanceFromCity" value="300" min="100" max="500"><br>
                Max Distance to Lake (meters) [10-100]: <input type="number" name="distanceFromLake" value="30" min="10" max="100"><br>
                Booking Start Date (yyyy-mm-dd): <input type="text" name="startDate" value="2023-07-01"><br>
                Booking Duration (in days): <input type="number" name="duration" value="5" min="1" max="30"><br>
                Max Shift Days (+/- days): <input type="number" name="maxShiftDays" value="2" min="0" max="1000"><br>
                <input type="submit" value="Search">
            </form>
        </body>
        </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/search_cottages", response_class=HTMLResponse)
async def search_cottages(
        booker_name: str = Form(...),
        numberOfPlaces: int = Form(...),
        numberOfBedrooms: int = Form(...),
        distanceFromLake: float = Form(...),
        cityName: str = Form(...),
        distanceFromCity: float = Form(...),
        startDate: str = Form(...),
        duration: int = Form(...),
        maxShiftDays: int = Form(...)):

    results = execute_sparql_query(
        ontology, booker_name, numberOfPlaces, numberOfBedrooms, distanceFromLake,
        cityName, distanceFromCity, startDate, duration, maxShiftDays
    )
    response_html = "<h2>Search Results</h2>"
    index = 1  # Initialize an index counter
    for row in results:
        start_date_obj = datetime.strptime(startDate, '%Y-%m-%d')
        user_start_date = start_date_obj - timedelta(days=maxShiftDays)
        user_end_date = start_date_obj + timedelta(days=maxShiftDays)

        current_date = user_start_date
        while current_date <= user_end_date:
            cottage_start_date = datetime.strptime(row['startDate'], '%Y-%m-%d')
            cottage_end_date = datetime.strptime(row['endDate'], '%Y-%m-%d')

            if cottage_start_date <= current_date <= cottage_end_date:
                booking_number = uuid.uuid4()
                response_html += f"<div><p><strong>Index: {index}</strong></p><hr>"
                response_html += f"<p>Booker Name: {booker_name}</p>"
                response_html += f"<p>Booking Number: {booking_number}</p>"
                # Display the image using the image URL
                if 'hasImageURL' in row and row['hasImageURL']:
                    response_html += f'<p>Image: <img src="{row["hasImageURL"]}" alt="Cottage Image" style="width:100px;height:100px;"></p>'
                response_html += f"<p>Address: {row['hasAddress']}</p>"
                response_html += f"<p>Number of Places: {row['numberOfPlaces']}</p>"
                response_html += f"<p>Number of Bedrooms: {row['numberOfBedrooms']}</p>"
                response_html += f"<p>City: {row['cityName']}</p>"
                response_html += f"<p>Distance to City: {row['distanceFromCity']}</p>"
                response_html += f"<p>Distance to Lake: {row['distanceFromLake']}</p>"
                # Calculate and display the booking period
                booking_start_date = current_date
                booking_end_date = booking_start_date + timedelta(days=duration - 1)
                date_label = "Booking Start Date" if current_date == start_date_obj else "Shifted Booking Start Date"
                response_html += f"<p>{date_label}: {booking_start_date.strftime('%Y-%m-%d')}</p>"
                response_html += f"<p>Booking Period: {duration} days ({booking_start_date.strftime('%Y-%m-%d')} to {booking_end_date.strftime('%Y-%m-%d')})</p>"
                response_html += "</div><hr>"
                index += 1  # Increment the index for each row

            current_date += timedelta(days=1)

    return HTMLResponse(content=response_html)

@app.post("/process_rig")
async def process_rig(request: Request):
    # Receive RIG data from the request
    rig_data = await request.body()

    # Parse the RIG data
    rig_graph = Graph()
    rig_graph.parse(data=rig_data, format="turtle")
    print("Received RIG Data:", rig_data)


    # Initialize variables to store the extracted data
    booker_name, numberOfPlaces, numberOfBedrooms, distanceFromLake, cityName, distanceFromCity, startDate, duration, maxShiftDays = '', 0, 0, 0.0, '', 0.0, '', 0, 0

    # Extract data from the RIG graph
    for s, p, o in rig_graph.triples((None, None, None)):
        if p == COT.booker_name and o:
            booker_name = str(o)
        elif p == COT.numberOfPlaces and o:
            numberOfPlaces = int(o) if o else 0
        elif p == COT.numberOfBedrooms and o:
            numberOfBedrooms = int(o) if o else 0
        elif p == COT.distanceFromLake and o:
            distanceFromLake = float(o) if o else 0.0
        elif p == COT.cityName and o:
            cityName = str(o)
        elif p == COT.distanceFromCity and o:
            distanceFromCity = float(o) if o else 0.0
        elif p == COT.startDate and o:
            startDate = str(o)
        elif p == COT.duration and o:
            duration = int(o) if o else 0
        elif p == COT.maxShiftDays and o:
            maxShiftDays = int(o) if o else 0

    # Print extracted data for verification
    print(f"Booker Name: {booker_name}")
    print(f"Number of Places: {numberOfPlaces}")
    print(f"Number of Bedrooms: {numberOfBedrooms}")
    print(f"Distance from Lake: {distanceFromLake}")
    print(f"City Name: {cityName}")
    print(f"Distance from City: {distanceFromCity}")
    print(f"Start Date: {startDate}")
    print(f"Duration: {duration}")
    print(f"Max Shift Days: {maxShiftDays}")

    # Execute SPARQL query with extracted data
    query_results = execute_sparql_query(
        ontology, booker_name, numberOfPlaces, numberOfBedrooms, distanceFromLake,
        cityName, distanceFromCity, startDate, duration, maxShiftDays
    )

    # Construct the final RRG graph
    final_rrg_graph = Graph()

    # Copy relevant triples from RIG to RRG
    for s, p, o in rig_graph.triples((None, None, None)):
        if p != SSWAP.mapsTo and not (isinstance(s, BNode) or isinstance(o, BNode)):
            final_rrg_graph.add((s, p, o))

    # Find the 'hasMapping' node from RIG
    has_mapping_node = None
    for s, p, o in rig_graph.triples((None, SSWAP.hasMapping, None)):
        has_mapping_node = o  # Save the hasMapping node

    # Add 'operatesOn' section from RIG to RRG
    for s, p, o in rig_graph.triples((None, SSWAP.operatesOn, None)):
        final_rrg_graph.add((s, p, o))
        for s1, p1, o1 in rig_graph.triples((o, None, None)):
            if p1 != SSWAP.mapsTo:
                final_rrg_graph.add((s1, p1, o1))

    # Add 'hasMapping' and 'mapsTo' sections with query results
    if query_results:
        maps_to_node = BNode()  # Create a new blank node for mapsTo object
        final_rrg_graph.add((has_mapping_node, SSWAP.mapsTo, maps_to_node))
        for result in query_results:
            for key, value in result.items():
                if key != 'cottage' and value:
                    # Prepare literal with correct datatype
                    if key in ["numberOfPlaces", "numberOfBedrooms", "distanceFromCity", "distanceFromLake", "duration", "maxShiftDays"]:
                        value = Literal(value, datatype=XSD.integer)
                    elif key in ["startDate", "endDate"]:
                        value = Literal(value, datatype=XSD.dateTime)
                    else:
                        value = Literal(value)
                    final_rrg_graph.add((maps_to_node, COT[key], value))
    else:
        # If no results, add an empty mapsTo section
        final_rrg_graph.add((has_mapping_node, SSWAP.mapsTo, BNode()))

    # Re-add the 'hasMapping' section from RIG to RRG
    for s, p, o in rig_graph.triples((None, SSWAP.hasMapping, None)):
        for s1, p1, o1 in rig_graph.triples((o, None, None)):
            if p1 != SSWAP.mapsTo:  # Skip the original mapsTo section
                final_rrg_graph.add((s1, p1, o1))

    # Set namespace manager for consistent prefix usage
    nm = NamespaceManager(final_rrg_graph)
    nm.bind("cot", COT)
    nm.bind("sswap", SSWAP)
    nm.bind("xsd", XSD)
    final_rrg_graph.namespace_manager = nm

    # Serialize final RRG to Turtle format
    final_rrg_data = final_rrg_graph.serialize(format="turtle")
    print("Final RRG:", final_rrg_data)

    # Return final RRG in response
    return HTMLResponse(content=final_rrg_data, media_type="text/turtle")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
