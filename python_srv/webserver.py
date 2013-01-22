# Copyright 2013 (C) Philip Crump
# Original HTTP Server Code Copyright Jon Berg , turtlemeat.com
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

import string,cgi,time
from dateutil import parser # required for RFC3339 time
from operator import itemgetter # required to sort flights by time
from os import curdir, sep
from urlparse import urlparse, parse_qs
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
#import pri
import couchdbkit # habitat interface
import json

def grab_flights():
    i=0
    flights_string=''
    flights_op = []
    db = couchdbkit.Server("http://habitat.habhub.org")["habitat"]
    flights = db.view("flight/launch_time_including_payloads", include_docs=True, descending=True, limit=10)
    for flight in flights:
        if(flight["doc"]["type"]=="flight"):
            flights_op.append(dict())
	    flights_op[i]["name"] = flight["doc"]["name"]
	    flights_op[i]["id"] = flight["doc"]["_id"]
	    flights_op[i]["time"] = time.mktime(parser.parse(flight["doc"]["launch"]["time"]).timetuple())
            i=i+1
            #flights_string += "{0},{2},{1};".format(flight["doc"]["_id"], flight["doc"]["launch"]["time"], flight["doc"]["name"])
    #return flights_string
    return json.dumps(sorted(flights_op, key=itemgetter('time'), reverse=True))

def grab_position(flight_id):
    db = couchdbkit.Server("http://habitat.habhub.org")["habitat"]
    ## Get a list of the payloads in the flight
    flights = db.view("flight/launch_time_including_payloads", include_docs=True, descending=True, limit=10)
    #print list(flights)
    for flight in flights:
        if(flight["doc"]["type"]=="flight" and flight["doc"]["_id"]==flight_id):
            payloads = flight["doc"]["payloads"]
    #print payloads
    ## Grab telemetry data for each payload
    flight_telemetry = []
    i=0
    for payload_id in payloads:
        flight_telemetry.append(dict())
        telemetry = db.view("payload_telemetry/flight_payload_time", startkey=[flight_id, payload_id], endkey=[flight_id, payload_id,[]], include_docs=True)
        telemetry_list = list(telemetry)
        last_string = sorted(telemetry_list, key=lambda x: x["doc"]["data"]["sentence_id"])[-1]
	flight_telemetry[i]["latitude"] = last_string["doc"]["data"]["latitude"];
	flight_telemetry[i]["longitude"] = last_string["doc"]["data"]["longitude"];
	flight_telemetry[i]["altitude"] = last_string["doc"]["data"]["altitude"];
	flight_telemetry[i]["time"] = last_string["doc"]["data"]["time"];
	flight_telemetry[i]["sentence_id"] = last_string["doc"]["data"]["sentence_id"];
	i=i+1
    #print sorted(flight_telemetry, key=lambda x: x["time"])
    ## Get latest timed position
    latest_telemetry = sorted(flight_telemetry, key=lambda x: x["time"])[-1]
    if latest_telemetry["latitude"] == latest_telemetry["longitude"]:
       return json.dumps({"Error":"1","Message":"Position appears to be invalid: Looks like 0,0,0"})
    try:
	return json.dumps({"latitude": latest_telemetry["latitude"], "longitude": latest_telemetry["longitude"], "altitude": latest_telemetry["altitude"], "sentence_id": latest_telemetry["sentence_id"], "payload": "*Not Implemented*", "time": latest_telemetry["time"]})
        #return str(d["latitude"]) + "," + str(d["longitude"]) + "," + str(d["altitude"])
    except KeyError:
       return json.dumps({"Error":"1","Message":"Position does not have required fields????"})


class HTTPHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
	    input = urlparse(self.path)
            if input.path.endswith("/flights"):
                self.send_response(200)
                self.send_header('Content-type',	'text/html')
                self.send_header('Access-Control-Allow-Origin',	'http://api.thecraag.com')
                self.end_headers()
                self.wfile.write(grab_flights())
                return
            if input.path.endswith("/position"):
                self.send_response(200)
                self.send_header('Content-type',	'text/html')
                self.send_header('Access-Control-Allow-Origin',	'http://api.thecraag.com')
                self.end_headers()
		try:
		    payload_doc_id = parse_qs(input.query)["flight_id"][0]
                except:
                    self.wfile.write(json.dumps({"Error":"1","Message":"Error Extracting Flight ID from query string."}))
                    return
                self.wfile.write(grab_position(payload_doc_id))
                return
            return
                
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)
     
    def do_POST(self):
        global rootnode
        try:
            ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
            if ctype == 'multipart/form-data':
                query=cgi.parse_multipart(self.rfile, pdict)
            self.send_response(301)
            
            self.end_headers()
            upfilecontent = query.get('upfile')
            print "filecontent", upfilecontent[0]
            self.wfile.write("<HTML>POST OK.<BR><BR>");
            self.wfile.write(upfilecontent[0]);
            
        except :
            pass

def main():
    try:
        server = HTTPServer(('127.0.0.1', 8888), HTTPHandler)
        print 'starting httpserver...'
        server.serve_forever()
    except KeyboardInterrupt:
        print '^C received, shutting down server'
        server.socket.close()

if __name__ == '__main__':
    main()

