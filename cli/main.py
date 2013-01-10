# Copyright 2013 (C) Philip Crump
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


import time # For delays
import earthmaths # Az/El calculations
import couchdbkit # habitat interface
import socket # UDP PstRotator interface

import pprint # DEBUG

UDP_ADDRESS = "127.0.0.1"
UDP_PORT = 12000

i=0
ids=[25]

print "Connecting to habitat.."

db = couchdbkit.Server("http://habitat.habhub.org")["habitat"]

print "Retrieving Flights.."

##HTTP: http://habitat.habhub.org/habitat/_design/flight/_view/launch_time_including_payloads?limit=5&descending=true&include_docs=true
flights = db.view("flight/launch_time_including_payloads", include_docs=True, descending=True, limit=30)

for flight in flights:
   if(flight["doc"]["type"]=="flight"):
      #pprint.pprint(flight)
      i=i+1
      ids.append(flight["doc"]["_id"])
      print "{0}: '{2}'  -  {1}".format(i, flight["doc"]["launch"]["time"], flight["doc"]["name"])

wanted_id = int(raw_input('Select Flight number: '))

payload_id = ids[wanted_id]

#pprint.pprint(ids)

udp_socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM )

while True:
   print "Receiving position.."
   try:
      ##HTTP: http://habitat.habhub.org/habitat/_design/payload_telemetry/_view/flight_payload_time?limit=2&descending=true&include_docs=true&startkey=["(payload_id)","end"]
      position = db.view("payload_telemetry/flight_payload_time", startkey=[payload_id, "end"], descending=True, limit=1, include_docs=True)
   except:
      db = couchdbkit.Server("http://habitat.habhub.org")["habitat"]
      position = db.view("payload_telemetry/flight_payload_time", startkey=[payload_id, "end"], descending=True, limit=1, include_docs=True)

   #pprint.pprint(position)

   r = list(position)
   if len(r) != 1 or r[0]["key"][0] != payload_id:
      raise ValueError("Could not get balloon position")
   r = r[0]

   t = r["key"][1]
   #if max_age is not None:
   #   if abs(time.time() - t) > self.max_age:
   #      raise ValueError("Position is too old (max_age)")

   d = r["doc"]["data"]
   if d.get("_fix_invalid", False):
      raise ValueError("Fix info is invalid")
   try:
      balloon = (d["latitude"], d["longitude"], d["altitude"])
   except KeyError:
      raise ValueError("Balloon does not have lat/lon/alt")

   print ("Balloon is at " + repr(balloon) + "Sentence id: " + str(d["sentence_id"]) + " at " + d["time"] + " UTC.")

   listener = (50.945277, -1.356812, 80)

   p = earthmaths.position_info(listener, balloon)
   #p["bearing"] = wrap_bearing(p["bearing"])
   #p["elevation"] = wrap_bearing(p["elevation"])
   #self.check_range(p)
   print p
   bearing = round(p["bearing"])
   elevation = round(p["elevation"])
   distance = round(p["straight_distance"]/1000,1)
   print("Azimuth: " + str(bearing) + " Elevation: " + str(elevation) + " at " + str(distance) + " km.")
   udp_string = "<PST><TRACK>0</TRACK><AZIMUTH>" + str(bearing) + "</AZIMUTH><ELEVATION>" + str(elevation) + "</ELEVATION></PST>"
   udp_socket.sendto(udp_string, (UDP_ADDRESS, UDP_PORT))
   time.sleep(10)
