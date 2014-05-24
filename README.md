habrotate
=========

An interface to track High Altitude Balloon payloads automatically with PstRotator, uses positioning telemetry data from habitat.

This program requires an internet connection to get the latest telemetry from habitat. Retrieving the position telemetry from a local copy of dl-fldigi may be implemented in the future.

### Interface to Habitat

habrotate queries habitat through the CouchDB API on habitat.habhub.org. 

First a query is made to return Active Flights and their respective payload_ids.

When a flight is selected, it's payload_id is then used to query for the last uploaded position telemetry.

### Interface to PstRotator

habrotate sends AZ/EL updates to PstRotator's local UDP port. You will need to enable 'UDP Control' in Setup.

For more information, see: https://www.philcrump.co.uk/habrotate
