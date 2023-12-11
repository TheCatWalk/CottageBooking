Current Data Flow:

Mediator Service Initialization:

User accesses the Mediator service's frontend via a web browser.
The Mediator service presents a form to collect booking information and the URL of the Cottage Booking service.
User Interaction:

The user fills out the booking information on the Mediator's frontend and provides the URL of the Cottage Booking service.
Request to Cottage Booking Service:

Mediator backend constructs the RIG (Request Invocation Graph) based on user input.
Mediator backend sends the RIG as a POST request to the provided Cottage Booking service URL.
Processing by Cottage Booking Service:

The Cottage Booking service (app.py) receives the RIG.
It extracts booking details from the RIG and performs a SPARQL query on its RDF database (new.rdf).
Constructs the RRG (Response Return Graph) based on query results.
Response to Mediator:

The Cottage Booking service sends the RRG back to the Mediator.
Mediator Processing and Display:

Mediator backend receives the RRG.
Parses the RRG and generates an HTML response showing the booking details.
Mediator frontend displays this information to the user.

TODO:
"Ideal" Location for RDG.ttl Usage:
In the Mediator service, when constructing the RIG (mediator.py). The RDG.ttl file should guide the structure of the RIG to ensure it aligns with the expected format of the Cottage Booking service.
Optionally, in the Cottage Booking service (app.py) to validate the incoming RIG against the expected structure defined in RDG.ttl.
Practical Steps:
Load and parse the RDG.ttl file in the Mediator service.
Use the definitions (predicates, classes, etc.) from RDG.ttl to construct the RIG accurately.
(Optional) Validate incoming RIGs in the Cottage Booking service against the structure defined in RDG.ttl.

In short: Do this backward. We already have the RIG, parse the RDG (that exists in such a way that the current RIG is the outout)
