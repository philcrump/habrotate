Python Web Glue Script
================================

This python script runs as a webserver on a linux machine and provides a HTTP JSON interface in front of the CouchDB server on habitat.

This script was written as I could not get a CouchDB interface to work with py2exe on Windows. Using this allows me to deploy a lightweight .exe for the habrotate software on the Windows pstrotator machine.

Tested working on Win XP with pstrotator AZ by Noel, G8GTZ.

Some flights are bugged and will not return positions (perhaps due to a space in the flight name?)

URLs
===

/flights
* Calls grab_flights and returns a JSON object containing the current Flight Names and their Documents IDs.

/position?flight_id=[Flight Document ID]
* Calls grab_position and returns a JSON object containing the latest Latitude, Longitude, Altitude as well as the Sentence ID and Decode-Time of that position for debugging.

Any errors are returned as plain text strings.
