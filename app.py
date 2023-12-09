from datetime import timedelta, datetime
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from rdf_operations import load_rdf_data, parse_rig, execute_sparql_query
from rdflib import Graph
import uvicorn
import uuid



app = FastAPI()
ontology = load_rdf_data("new.rdf")  # Ensure this loads your RDF database

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


@app.post("/invoke")
async def invoke_service(request: Request):
    # Read the incoming RIG data
    rig_data = await request.body()
    rig_data = rig_data.decode('utf-8')  # Convert bytes to string

    # Parse the RIG
    rig_graph = Graph().parse(data=rig_data, format="turtle")
    parsed_params = parse_rig(rig_graph)

    # Use parsed parameters to query the RDF database
    results = execute_sparql_query(ontology, **parsed_params)

    # TODO: Generate RRG based on results
    # This will be implemented in the next step

    return {"status": "success", "results": results}



if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)

