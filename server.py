import socket
import threading
import sys
import os
import uuid
import json
import tempfile
import sqlite3 

from requests import head

HOST = ''
PORT = 8080

#header = '''HTTP/1.1 200 OK
#'''

def parseRequest(req):
	req = req.decode('utf-8', 'ignore')
	reqLine = req.split(' ') 
	method = reqLine[0] # 
	reqFile = reqLine[1]
	print('METHOD = '+method)
	print('FILE = '+reqFile)

	return reqFile

def getRequestedFile(thePath):

	if(thePath == '/'):
		fileName  = 'index.html' # return  the index file by default
		contentType = 'Content-Type: text/html'		
	elif(thePath == '/main.js'):
		fileName = 'main.js'
		contentType = 'Content-Type: text/javascript' 
	elif(thePath == '/data.js'):
		fileName = 'data.js'
		contentType = 'Content-Type: text/javascript' 
	
	header = 'HTTP/1.1 200 OK\n'
	
	try:
		print(contentType)
		print('opening ' +fileName)
		file = open(fileName, 'rb')
		response = file.read()
		file.close()
						
		header = 'HTTP/1.1 200 OK\n'+contentType+'\n\n'
		print(header)
		header = header.encode('utf-8','ignore')

		response = header + response
	#	print(response.decode('utf-8','ignore'))
	except Exception as e:
		# could not open the file
		#response = 'File not found'
		#response = response.encode('utf-8','ignore')
		print(e)
		response = ('HTTP/1.1 404 Not Found\n\n').encode('utf-8','ignore')

	return response

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
	s.bind((HOST, PORT))
	s.listen()
	#print('listening on '+socket.gethostname())
	try:
		while True:
			conn, addr = s.accept()
		
			with conn:
				request = conn.recv(1024)				
				if(request):
					requestedFile = parseRequest(request)
					print('>>> REQUESET RECIEVED \n---------\n'+request.decode('utf-8','ignore')+'\n---------\n')
#file = open('index.html','rb')
#				body = file.read()
#				file.close()
				theResponse = getRequestedFile(requestedFile)
				
				if(theResponse):
					conn.send(theResponse)
					conn.close()

	except KeyboardInterrupt: 
		print("End of Process.\n")
		s.close();
		sys.exit(0)


