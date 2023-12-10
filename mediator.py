
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from rdflib import Graph, Namespace, Literal, URIRef
import requests

mediator_app = FastAPI()

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
                Max Shift Days: <input type="number" name="shift" value="2"><br>
                <input type="submit" value="Submit">
            </form>
        </body>
        </html>
    """
    return HTMLResponse(content=html_content)

@mediator_app.post("/mediate", response_class=HTMLResponse)
async def mediate_request(request: Request, booking_service_url: str = Form(...)):
    try:
        form_data = await request.form()
        # Construct the RIG (Request Invocation Graph) based on RDG.ttl structure
        rig_graph = Graph()
        REQUEST = Namespace("http://example.org/request/")
        COT = Namespace("http://users.jyu.fi/~kumapmxw/cottage-ontology.owl#")
        SSWAP = Namespace("http://sswapmeet.sswap.info/sswap/")
        RESPONSE = Namespace("http://example.org/response/")
        request_node = URIRef("http://example.org/request/BookingRequest")

        # Iterate over form data and add triples to the graph
        for key, value in form_data.items():
            if key != "booking_service_url":
                predicate = URIRef(f"http://example.org/request/{key}")
                rig_graph.add((request_node, predicate, Literal(value)))

        # Serialize the RIG to Turtle format
        rig_data = rig_graph.serialize(format="turtle")

        # Send RIG to the Cottage Booking service's invoke endpoint
        response = requests.post(booking_service_url, data=rig_data, headers={"Content-Type": "text/turtle"})

        return HTMLResponse(content=f"Response from Cottage Booking Service: {response.text}")
    except Exception as e:
        # Debugging: Capture any exception and return it as response for easier troubleshooting
        return HTMLResponse(content=f"An error occurred: {str(e)}", status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(mediator_app, host="127.0.0.1", port=5001)
