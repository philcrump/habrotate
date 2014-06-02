HABrotate Changelog
=================

## 0.5.3 (June 2, 2014)

* Fixed a bug that caused a crash if Unicode was used in a flight name (Reported by Geoff G8DHE)
* Remove debug print when querying position
* Removed obselete code directories from git

## 0.5.2 (March 5, 2013)

* Sort habitat flight docs by start time for initial menu
* Increased number of flight docs retrieved from habitat for initial menu
* Don't assert the rotator on every event loop - could cause unneccessary wear-and-tear with buggy controllers

## 0.5.1 (Feb 17, 2013)

* Retrieve Launch Location Altitude for a flight from Google Maps API if it isn't set in the flight doc

## 0.5 (Feb 16, 2013)

* Client script now polls habitat directly via HTTP, no custom server element involved

...

Older versions queried a server side couchdb script via HTTP to retrieve the data from habitat, due to couchdb libs not working on Windows
