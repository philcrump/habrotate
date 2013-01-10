import time # For delays
import earthmaths # Az/El calculations
import socket # UDP PstRotator interface
import json
import urllib2

UDP_ADDRESS = "127.0.0.1"
UDP_PORT = 12000 # Port for pstrotator interface

config_file = open('config.json', 'r')
config = json.load(config_file)
config_file.close()

listener = (float(config["station_latitude"]), float(config["station_longitude"]), float(config["station_altitude"]))

print("Receiver Station Location loaded as: " + str(listener))

i=0
ids=[25]

print "Querying flights.."

flights_data = json.load(urllib2.urlopen('http://py.thecraag.com/flights'))

for flight in flights_data:
   i=i+1
   ids.append(flight["id"])
   print "{0}: {1}".format(i, flight["name"])

wanted_id = int(raw_input('Select Flight number: '))
flight_id = ids[wanted_id]

udp_socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ) # Open UDP socket

while True:
   print "Querying position.."
   try:
      position_data = json.load(urllib2.urlopen('http://py.thecraag.com/position?flight_id=' + str(flight_id)))
   except:
      print "Invalid JSON received from server, does a position exist?"

   try:
      balloon = (position_data["latitude"], position_data["longitude"], position_data["altitude"])
      print "Balloon is at " + repr(balloon) + " Sentence id: " + str(position_data["sentence_id"]) + " at " + position_data["time"] + " UTC."
   except:
		print "Position not received from server."
		print position_data
		break

   #print ("Balloon is at " + repr(balloon) + "Sentence id: " + str(d["sentence_id"]) + " at " + d["time"] + " UTC.")

   p = earthmaths.position_info(listener, balloon)
   #p["bearing"] = wrap_bearing(p["bearing"])
   #p["elevation"] = wrap_bearing(p["elevation"])
   #self.check_range(p)
   #print p
   bearing = round(p["bearing"])
   elevation = round(p["elevation"])
   distance = round(p["straight_distance"]/1000,1)
   print("Azimuth: " + str(bearing) + " Elevation: " + str(elevation) + " at " + str(distance) + " km.")
   udp_string = "<PST><TRACK>0</TRACK><AZIMUTH>" + str(bearing) + "</AZIMUTH><ELEVATION>" + str(elevation) + "</ELEVATION></PST>"
   udp_socket.sendto(udp_string, (UDP_ADDRESS, UDP_PORT))
   time.sleep(10)
