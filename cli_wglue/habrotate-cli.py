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
import socket # UDP PstRotator interface
import json
import urllib2
import sys

def load_listener_config():
		config_file = open('config.json', 'r')
		config = json.load(config_file)
		config_file.close()

		return (float(config["station_latitude"]), float(config["station_longitude"]), float(config["station_altitude"]))

def load_udp_config():
		config_file = open('config.json', 'r')
		config = json.load(config_file)
		config_file.close()

		return (str(config["udp_ip"]), int(config["udp_port"]))

def load_control_config():
		config_file = open('config.json', 'r')
		config = json.load(config_file)
		config_file.close()

		return (int(config["hysteresis"]), int(config["overshoot"]))
		
listener = load_listener_config()
print("Loaded Receiver Station Location: " + str(listener))

udp_config = load_udp_config()
print("Loaded UDP Configuration: " + str(udp_config))

control_config = load_control_config()
hysteresis = control_config[0]
overshoot = control_config[1]
if overshoot >= hysteresis: #If overshoot is larger than hysteresis we will oscillate
	print ("Overshoot must be less than the Hysteresis, else oscillation may occur.")
	sys.exit(0)
print ("Loaded Control Configuration: Hysteresis = " + str(control_config[0]) + " degrees, Overshoot = " + str(control_config[1]) + " degrees.")

i=0
ids=[25]

print "Querying flights.."

flights_data = json.load(urllib2.urlopen('http://py.thecraag.com/flights'))

for flight in flights_data:
	i=i+1
	ids.append(flight["id"])
	if time.strftime("%d:%m", time.gmtime(int(flight["time"]))) == time.strftime("%d:%m", time.gmtime()):
		print "{0}: {1} - TODAY".format(i, flight["name"])
	else:
		print "{0}: {1}".format(i, flight["name"])

wanted_id = int(raw_input('Select Flight number: '))
flight_id = ids[wanted_id]

udp_socket = socket.socket( socket.AF_INET, socket.SOCK_DGRAM ) # Open UDP socket

loopcount = 0
update_rotator = 0
try:
	while True:
		print "Querying position.."
		try:
			position_data = json.load(urllib2.urlopen('http://py.thecraag.com/position?flight_id=' + str(flight_id)))
		except:
			print "Invalid JSON received from server. Contact Developer."
			print urllib2.urlopen('http://py.thecraag.com/position?flight_id=' + str(flight_id)).read()
			break
		if "Error" in position_data:
			print("Server Error: " + str(position_data["Message"]))
			break
		try:
			balloon = (position_data["latitude"], position_data["longitude"], position_data["altitude"])
			print "Found payload at " + repr(balloon) + " Sentence: " + str(position_data["sentence_id"]) + " at " + position_data["time"] + " UTC."
		except:
			print "Document Error. Position not received from server."
			print "DEBUG:"
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
		print("Balloon Azimuth: " + str(bearing) + " Elevation: " + str(elevation) + " at " + str(distance) + " km.")
		if loopcount == 0: #Set rotator on first loop
			print ("Pointing Rotator.")
			rotator_bearing = bearing
			rotator_elevation = elevation
			udp_string = "<PST><TRACK>0</TRACK><AZIMUTH>" + str(rotator_bearing) + "</AZIMUTH><ELEVATION>" + str(rotator_elevation) + "</ELEVATION></PST>"
			udp_socket.sendto(udp_string, udp_config)
		else:
			if bearing > (rotator_bearing + hysteresis):
				rotator_bearing = (bearing + overshoot)%360
				update_rotator = 1
			elif bearing < (rotator_bearing - hysteresis):
				rotator_bearing = (bearing - overshoot)%360
				update_rotator = 1
			if elevation > (rotator_elevation + hysteresis):
				rotator_elevation = elevation + overshoot
				update_rotator = 1
			elif elevation < (rotator_elevation - hysteresis):
				rotator_elevation = elevation - overshoot
				update_rotator = 1
			if update_rotator == 1:
				update_rotator = 0
				print("Moving rotator to Azimuth: " + str(rotator_bearing) + " Elevation: " + str(rotator_elevation))
				udp_string = "<PST><TRACK>0</TRACK><AZIMUTH>" + str(rotator_bearing) + "</AZIMUTH><ELEVATION>" + str(rotator_elevation) + "</ELEVATION></PST>"
				udp_socket.sendto(udp_string, udp_config)
			else:
				print ("Current Rotator error: Azimuth: " + str(rotator_bearing-bearing) + " Elevation: " + str(rotator_elevation-elevation))
		time.sleep(10)
		loopcount+=1
except KeyboardInterrupt:
        print '^C received, Shutting down.'