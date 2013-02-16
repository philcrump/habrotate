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

print "##### HABrotate ####"

from time import sleep, gmtime, strftime # For delays
import earthmaths # Az/El calculations
from socket import socket, AF_INET, SOCK_DGRAM # UDP PstRotator interface
from json import load
from urllib2 import urlopen
from sys import exit, exc_info

def load_listener_config(config):
		return (float(config["station_latitude"]), float(config["station_longitude"]), float(config["station_altitude"]))

def load_udp_config(config):
		return (str(config["udp_ip"]), int(config["udp_port"]))

def load_control_config(config):
		return (int(config["hysteresis"]), int(config["overshoot"]))

try:		
	config_file = open('config.json', 'r')
except IOError:
	print "ERROR: Config File 'config.json' does not exist in application directory."
	exit(1)
try:
	config_json = load(config_file)
except:
	print "ERROR: Syntax Error in config.json file."
	exit(1)

config_file.close()

listener = load_listener_config(config_json)
print("Loaded Receiver Station Location: " + str(listener))

udp_config = load_udp_config(config_json)
print("Loaded UDP Configuration: " + str(udp_config))

control_config = load_control_config(config_json)
hysteresis = control_config[0]
overshoot = control_config[1]
if overshoot >= hysteresis: #If overshoot is larger than hysteresis we will oscillate
	print ("ERROR: Overshoot must be less than the Hysteresis, else oscillation may occur.")
	exit(1)
print ("Loaded Control Configuration: Hysteresis = " + str(control_config[0]) + " degrees, Overshoot = " + str(control_config[1]) + " degrees.")

i=0
ids=[25]

print "Querying flights.."

try:
	flights_json = urlopen('http://py.thecraag.com/flights')
except:
	print "ERROR: thecraag.com HTTP Connection Error: ", exc_info()[0]
	exit(1)

try:
	flights_data = load(flights_json)
except:
	print "ERROR: Invalid JSON returned from Server: ", exc_info()[0]
	exit(1)

for flight in flights_data:
	i=i+1
	ids.append(flight["id"])
	if strftime("%d:%m", gmtime(int(flight["time"]))) == strftime("%d:%m", gmtime()):
		print "{0}: {1} - TODAY".format(i, flight["name"])
	else:
		print "{0}: {1}".format(i, flight["name"])

valid_input = False
while not valid_input:
	try:
		wanted_id = int(raw_input('Select Flight number: '))
		if wanted_id==0:
			raise IndexError
		flight_id = ids[wanted_id]
		valid_input = True
	except ValueError:
		print "Input not an integer, please try again:"
	except IndexError:
		print "Input out of range, please try again:"


udp_socket = socket( AF_INET, SOCK_DGRAM ) # Open UDP socket

loopcount = 0
update_rotator = 0
try:
	while True:
		print "Querying position.."
		try:
			position_json = urlopen('http://py.thecraag.com/position?flight_id=' + str(flight_id))
		except:
			print "ERROR: thecraag.com HTTP Connection Error: ", exc_info()[0]
			exit(1)
		try:
			position_data = load(position_json)
		except:
			print "ERROR: Invalid JSON received from server. Contact Developer. ", exc_info()[0]
			print urllib2.urlopen('http://py.thecraag.com/position?flight_id=' + str(flight_id)).read()
			exit(1)

		if "Error" in position_data:
			print("ERROR: Server Error: " + str(position_data["Message"]))
			exit(1)
		try:
			balloon = (position_data["latitude"], position_data["longitude"], position_data["altitude"])
			print "Found payload at " + repr(balloon) + " Sentence: " + str(position_data["sentence_id"]) + " at " + position_data["time"] + " UTC."
		except:
			print "ERROR: Document Parsing Error:", exc_info()[0]
			print "DEBUG info:"
			print position_data
			exit(1)

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
			else:
				print ("Current Rotator error: Azimuth: " + str(rotator_bearing-bearing) + " Elevation: " + str(rotator_elevation-elevation))
			udp_string = "<PST><TRACK>0</TRACK><AZIMUTH>" + str(rotator_bearing) + "</AZIMUTH><ELEVATION>" + str(rotator_elevation) + "</ELEVATION></PST>"
			udp_socket.sendto(udp_string, udp_config)
		print("Pausing for 10s...")
		sleep(10)
		loopcount+=1
except KeyboardInterrupt:
        print '^C received, Shutting down.'