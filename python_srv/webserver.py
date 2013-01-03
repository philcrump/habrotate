#Copyright Jon Berg , turtlemeat.com

import string,cgi,time
from dateutil import parser # required for RFC3339 time
from operator import itemgetter # required to sort flights by time
from os import curdir, sep
from urlparse import urlparse, parse_qsl
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

def grab_position(payload_id):
    db = couchdbkit.Server("http://habitat.habhub.org")["habitat"]
    position = db.view("payload_telemetry/flight_payload_time", startkey=[payload_id, "end"], descending=True, limit=1, include_docs=True)
    r = list(position)
    if len(r) != 1 or r[0]["key"][0] != payload_id:
       return "Could not get balloon position"
    try:
        r = r[0]
        t = r["key"][1]
        #if max_age is not None:
        #   if abs(time.time() - t) > self.max_age:
        #      raise ValueError("Position is too old (max_age)")
        d = r["doc"]["data"]
    except:
        return "Processing Error"
    if d.get("_fix_invalid", False):
        return "Fix info is invalid" + d["_fix_invalid"]
    try:
	return json.dumps({"latitude": d["latitude"], "longitude": d["longitude"], "altitude": d["altitude"], "sentence_id": d["sentence_id"], "time": d["time"]})
        #return str(d["latitude"]) + "," + str(d["longitude"]) + "," + str(d["altitude"])
    except KeyError:
        return "Balloon does not have lat/lon/alt"


class HTTPHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
	    input = urlparse(self.path)
            if input.path.endswith("flights"):
                self.send_response(200)
                self.send_header('Content-type',	'text/html')
                self.send_header('Access-Control-Allow-Origin',	'http://api.thecraag.com')
                self.end_headers()
                self.wfile.write(grab_flights())
                return
            if input.path.endswith(""):
                self.send_response(200)
                self.send_header('Content-type',	'text/html')
                self.send_header('Access-Control-Allow-Origin',	'http://api.thecraag.com')
                self.end_headers()
		try:
		    payload_doc_id = dict(parse_qsl(input.query))['flight_id']
                    self.wfile.write(grab_position(payload_doc_id))
                except:
                    self.wfile.write("Error: flight id not valid")
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

