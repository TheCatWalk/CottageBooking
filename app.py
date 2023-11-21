from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from rdf_operations import load_rdf_data, execute_sparql_query
import uvicorn
import uuid


app = FastAPI()
ontology = load_rdf_data("ontology.rdf")

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
            Number of Places (People) [1-5]: <input type="number" name="num_places" value="1" min="1" max="5"><br>
            Number of Bedrooms [1-4]: <input type="number" name="num_bedrooms" value="1" min="1" max="4"><br>
            Max Distance to Lake (meters) [10-1000]: <input type="number" name="max_lake_dist" value="1000" min="10" max="1000"><br>
            City [Helsinki, Jyvaskyla, or Tampere]: <input type="text" name="city" value="Jyvaskyla"><br>
            Max Distance to City (kilometers) [6-20]: <input type="number" name="max_city_dist" value="20"><br>
            Required Number of Days: <input type="number" name="required_days" value="1"><br>
            Starting Day of Booking (yyyy-mm-dd): <input type="text" name="start_date" value="2024-02-06"><br>
            Max Possible Shift of Start Day (+/- n days): <input type="number" name="max_shift_days" value="7"><br>
            <input type="submit" value="Search">
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/search_cottages", response_class=HTMLResponse)
async def search_cottages(
        booker_name: str = Form(...), num_places: int = Form(...),
        num_bedrooms: int = Form(...), max_lake_dist: float = Form(...),
        city: str = Form(...), max_city_dist: float = Form(...),
        required_days: int = Form(...), start_date: str = Form(...), max_shift_days: str = Form(...)):
    results = execute_sparql_query(ontology, booker_name, num_places, num_bedrooms,
                                   max_lake_dist, city, max_city_dist, required_days,
                                   start_date, max_shift_days)
    sorted_results = sorted(results, key=lambda x: x[7])
    # Inside the search_cottages function
    results_html = "<table><tr><th>Index</th><th>Booking Number</th><th>Booker Name</th><th>Address</th><th>Nearest City (Distance in km)</th><th>Places</th><th>Bedrooms</th><th>Distance to Lake (Metres)</th><th>Start Date</th><th>Available Days</th><th>Image Url</th></tr>"
    for index, result in enumerate(sorted_results, start=1):
        booking_number = str(uuid.uuid4())
        # Unpack the result tuple based on the SPARQL query order
        _, address, places, bedrooms, distance_to_lake, nearest_city, image_url, start_date, available_days, distance_to_city = result
        nearest_city_with_distance = f"{nearest_city} ({distance_to_city} km)"
        image_tag = f'<img src="{image_url}" alt="Cottage Image" style="width:100px; height:auto;">'
        formatted_result = [str(index), booking_number, booker_name, str(address), nearest_city_with_distance, str(places), str(bedrooms),
                            str(distance_to_lake), str(start_date), str(available_days), image_tag]
        row = "<tr>" + "".join(f"<td>{field}</td>" for field in formatted_result) + "</tr>"
        results_html += row
    results_html += "</table>"


    results_html += "</table>"

    final_html_content = f"""
    <html>
    <head>
        <title>Cottage Booking</title>
        <style>
            table, th, td {{
                border: 1px solid black;
                border-collapse: collapse;
            }}
            th, td {{
                padding: 5px;
                text-align: left;
            }}
        </style>
    </head>
    <body>
        <h2>Search for Cottage Bookings</h2>
        <form action="/search_cottages" method="post">
            <!-- Form fields here -->
        </form>
        {results_html}
    </body>
    </html>
    """
    return HTMLResponse(content=final_html_content)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
