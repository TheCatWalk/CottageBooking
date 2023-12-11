import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from rdflib import Graph, Namespace, Literal, URIRef, RDF
import requests

mediator_app = FastAPI()


# # Function to load and parse the RDG file
# def load_rdg_data(file_path):
#     rdg_graph = Graph()
#     rdg_graph.parse(file_path, format="turtle")
#     return rdg_graph
#
#  RDG.ttl
#  rdg_graph = load_rdg_data("RDG.ttl")


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

        # Debug: Print the RIG for inspection
        print("Constructed RIG in Mediate:")
        print(rig_graph.serialize(format="turtle"))

        rig_data = rig_graph.serialize(format="turtle")
        response = requests.post(booking_service_url, data=rig_data, headers={"Content-Type": "text/turtle"})

        rdf_data = response.json().get('rrg', '')
        if not rdf_data:
            return HTMLResponse(content="No RDF data received from the Cottage Booking service.")

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
                date_label = "Booking Start Date" if current_date == start_date else "Shifted Booking Start Date"

                address = str(response_graph.value(response_node, COT.hasAddress) or "No Address")
                num_places = str(response_graph.value(response_node, COT.numberOfPlaces) or "Not Specified")
                num_bedrooms = str(response_graph.value(response_node, COT.numberOfBedrooms) or "Not Specified")
                image_url = str(response_graph.value(response_node, COT.hasImageURL) or "")
                city_name = str(response_graph.value(response_node, COT.cityName) or "Not Specified")
                distance_city = str(response_graph.value(response_node, COT.distanceFromCity) or "Not Specified")
                distance_lake = str(response_graph.value(response_node, COT.distanceFromLake) or "Not Specified")

                response_html += "<div>"
                response_html += f"<p>Booker Name: {booker_name}</p>"
                response_html += f"<p>Booking Number: {booking_number}</p>"
                response_html += f"<p>{date_label}: {current_date.strftime('%Y-%m-%d')}</p>"
                response_html += f"<p>Booking Period: {duration} days</p>"
                response_html += f"<p>Address: {address}</p>"
                response_html += f"<p>Number of Places: {num_places}</p>"
                response_html += f"<p>Number of Bedrooms: {num_bedrooms}</p>"
                response_html += f"<p>City: {city_name}</p>"
                response_html += f"<p>Distance to City: {distance_city}</p>"
                response_html += f"<p>Distance to Lake: {distance_lake}</p>"
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
