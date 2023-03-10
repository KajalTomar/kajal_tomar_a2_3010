import socket
import threading
import sys
import os
import uuid
import json
import tempfile
import sqlite3 
import traceback

from requests import head

try:
	dbConn = sqlite3.connect('3010eeter.db')
	cur = dbConn.cursor()
except Exception as e:
	print('> Could not connect to the db')
	print(e)
	traceback.print_exc()

HOST = ''
PORT = 8888

status200 = 'HTTP/1.1 200 OK\n'
status400 = 'HTTP/1.1 400 Bad Request\n'
status403 = 'HTTP/1.1 403 Forbidden: Access Denied\n'
status404 = 'HTTP/1.1 404 Not Found\n'
status500 = 'HTTP/1.1 500 Internal Error\n'


def parseRequest(req):
	req = req.decode('utf-8', 'ignore')
	reqLine = req.split(' ') 
	method = reqLine[0] # 
	reqFile = reqLine[1]
	print('> Parsing the requested file. Method = '+method+', File = '+reqFile)

	return reqFile

def getRequestedFile(thePath):
	global status200
	global status404
	print('> Getting the requested file: '+thePath)
	fileName = ''
	contentType=''
	if(thePath == '/index.html' or thePath == '/'):
		fileName  = './webFiles/index.html' # return  the index file by default
		contentType = 'Content-Type: text/html\n'		
	elif(thePath == '/main.js'):
		fileName = './webFiles/main.js'
		contentType = 'Content-Type: text/javascript\n' 
	else:
		imageExtensions = ['.jpg', '.jpeg', '.png', '.tiff', '.gif']
		textExtensions = ['.css', '.csv', '.html', '.javascript', '.plain', '.xml']
		
		fileName, fileExtension = os.path.splitext(thePath)
		fileName = './webFiles'+thePath	
		if(fileExtension in imageExtensions):
			fileExtension = (fileExtension.split('.'))[1]
			contentType = 'Content-Type: image/'+fileExtension+'\n'
		elif(fileExtension in textExtensions):
			fileExtension = (fileExtension.split('.'))[1]
			contentType = 'Content-Type: text/'+fileExtension+'\n'

	try:
		print(fileName)
		if(fileName != ''):
			try:
				with open(fileName, 'rb') as myFile:
					print('opening file')
					response = myFile.read()
					fileLength = 'Content-Length:'+str(len(response))
			
					header = status200+contentType+fileLength+'\n\n'
					header = header.encode('utf-8','ignore')

					response = header + response
			except Exception as e:
				reponse =  (status404).encode('utf-8','ignore')
		else:
			print('> file foes not exist')
			response = (status404).encode('utf-8','ignore')
	#	print(response.decode('utf-8','ignore'))
	except Exception as e:
		# could not open the file
		#response = 'File not found'
		#response = response.encode('utf-8','ignore')
		response = (status404).encode('utf-8','ignore')

	return response

def resolveGetMethod(message, command):
	global status200
	global status400
	global status403
	global status404
	global status500
	
	response = status200
	if(command.lower() == 'tweet'):
		try:
			sessionID = (message.split('sessionID='))[1]
			sessionID = (sessionID.split(';'))[0]
			sessionID = sessionID.strip()
			statement = "SELECT username FROM users WHERE signed_in=1 AND cookie='"+sessionID+"'"
			cur.execute(statement)
			dbConn.commit()
			result = cur.fetchall()
				
			if(len(result) == 1):
				statement = "SELECT * FROM tweets" 
				cur.execute(statement)
				results = cur.fetchall()
			
				if(results):
#keys = ['tweet','byUser']
					resultJson = json.dumps([{"tweet": result[0], "byUser": result[1], "id": str(result[2])} for result in results])
					header = status200+'Content-Type: application/json\nContent-Length:'+str(len(resultJson))+'\n\n'
					response = header.encode('utf-8','ignore') + resultJson.encode('utf-8','ignore')
			else:
				response = status404
		except Exception as e:
			print(e)
			traceback.print_exc()
			response = status500.encode('utf-8','ignore')

	return response

def resolvePostMethod(message, command):
	global status200
	global status400
	global status403
	global status404
	global status500
	
	response = ''

	if(command.lower() == 'login'):
		try:
			print('> trying to log in\n')
			message = (message.split('\r\n\r\n'))
			if(len(message) >= 2):
				message = message[1]
				messageBody = json.loads(message)
				username = messageBody['username'].strip()
				password = messageBody['password'].strip()
				if(username and password):
					statement = "SELECT * FROM users where username ='"+username+"' AND password='"+password+"'" 
					cur.execute(statement)
					result = cur.fetchall()
					
					if(len(result) > 0):
						if(result[0][2] == 0 and not result[0][3]):
							# give a cookie and set status to logged in
							cookie = str(uuid.uuid4())
							statement = "UPDATE users SET cookie='"+cookie+"expires=2147483647', signed_in=1 WHERE username ='"+username+"' AND password='"+password+"'"
							cur.execute(statement)
							dbConn.commit()
							result = cur.rowcount 
						
							if(result >= 1):
								print('> '+username+' is logged in.')
								response = status200+'Set-Cookie: sessionID='+cookie+'expires=2147483647;\n\n'
								#response = status200+"{'Set-Cookie': 'sessionID="+cookie+"'}\n\n"
							else:
								response = status500
						else:
							 # user is already logged in 
							print('> the user is already logged in.')
							response = status200 # not sure that this is the right response
					else:
						print('> no results for that username, password combo')
						response = status404
				else:
					# if the result is an empty array, then send not found response
					print('> did not get username or password.')
					response = status400
			else:
				# the body did not have a username and password field
				print('> did not get all the login details.')
				response = status400
		except Exception as e:
			response = status500
			print(e)
			traceback.print_exc()
	elif(command.lower() == 'tweet'):
		print('> trying to post a tweet')
		try:
			body = message.split('\r\n\r\n')[1]
			sessionID = (message.split('sessionID='))[1]
			#sessionID = ((sessionID.split('\r\n'))[0]).strip()
			sessionID = (sessionID.split(';'))[0]
			sessionID = sessionID.strip()
			if(len(body) > 1 and sessionID):
				messageBody = json.loads(body)
				tweet = messageBody['tweet'].strip()

				statement = "SELECT username FROM users WHERE signed_in=1 AND cookie='"+sessionID+"'"
				cur.execute(statement)
				dbConn.commit()
				result = cur.fetchall()
				
				if(len(result) == 1):
					user = result[0][0]
					
					try:
						statement = "INSERT INTO tweets VALUES('"+tweet+"', '"+user+"', NULL);"
						cur.execute(statement)
						dbConn.commit()
						response = status200
					except Exception as e:
						response = status500
						print(e)
						traceback.print_exc()
				else:
					print('cookie does not exist.')
					response = status404	
			else:
				print('> did not get the right info '+message)
				response = status400	
		except Exception as e:
			response = status500
			print(e)
			traceback.print_exc()

	return(response.encode('utf-8','ignore'))

def resolveDeleteMethod(message, command, tweetID):
	global status200
	global status400
	global status403
	global status404
	global status500
	
	print('> IN DELETE METHOD')

	response = status200
	if(command.lower() == 'logout'):
		try:
			sessionID = message.split('sessionID=')[1]
			sessionID = (sessionID.split(';'))[0]
			sessionID = sessionID.strip()
			statement = "UPDATE users SET cookie='', signed_in=0 WHERE cookie='"+sessionID+"'"
			cur.execute(statement)
			dbConn.commit()
			response = status200
		except Exception as e:
			response = status400
			print(e)
			traceback.print_exc()
	elif(command.lower() == 'tweet'):
		try:
			sessionID = message.split('sessionID=')[1]
			sessionID = (sessionID.split(';'))[0]
			sessionID = sessionID.strip()
			
			statement = "SELECT username FROM users WHERE signed_in=1 AND cookie='"+sessionID+"'"
			cur.execute(statement)
			dbConn.commit()
			result = cur.fetchall()
				
			if(len(result) == 1):
				user = result[0][0]
				
				try:
					statement = "DELETE FROM tweets WHERE username='"+user+"' AND tweet_id="+tweetID+";"
					cur.execute(statement)
					dbConn.commit()
					response = status200
				except Exception as e:
					response = status500
					print(e)
					traceback.print_exc()
			else:
				print('cookie does not exist.')
				response = status404	
		except Exception as e:
			response = status500
			print(e)
			traceback.print_exc()


	return(response.encode('utf-8','ignore'))

# --------------------------------------------------------
# bindToRandomPort(socket)
#
# Purpose: binds the socket to an available port
# Parameter: socket to bind
# Returns: the port number that the socket is bound to
# --------------------------------------------------------
def bindToRandomPort(s):
	result = -1
	while result != 0:
		try:
			result = s.bind((HOST,0))
			return s.getsockname()[1]
		except socket.error as e:
			pass

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
	try:
		s.bind((HOST, PORT))
		print('> listening on port: '+str(PORT))
	except socket.error as e:
		PORT = bindToRandomPort(s)
		print('The requested port was in already use. Using port '+str(PORT))
	
	s.listen()
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	try:
		while True:
			conn, addr = s.accept()
		
			with conn:
				messageRecvd = conn.recv(1024)				
				if(messageRecvd):
					print('\n>>> MESSAGE RECIEVED \n---------\n'+messageRecvd.decode('utf-8','ignore')+'\n---------\n', flush=True)
					messageRecvd = messageRecvd.decode('utf-8', 'ignore')
					message = messageRecvd.split(' ') 
					
					if(len(message) > 1):
						method = message[0]
						path = message[1].split('/')
						if(method == 'GET'):
							if(path[1].lower() == 'api'):
								conn.send(resolveGetMethod(messageRecvd, path[2]))
							else:
								theResponse = getRequestedFile(message[1])
								if(theResponse):
									conn.send(theResponse)
						elif(method == 'POST' and path[1].lower() == 'api'):
							conn.send(resolvePostMethod(messageRecvd, path[2]))
							# theResponse = resolvePostMethod(message[1], path[2])
						elif(method == 'DELETE'):
							print(path)
							if(path[2].lower() == 'tweet'):
								conn.send(resolveDeleteMethod(messageRecvd, path[2], path[3]))
							elif(path[2].lower() == 'logout'):
								conn.send(resolveDeleteMethod(messageRecvd, path[2], ''))
#if(theResponse):
#							conn.send(theResponse)
					else:
						con.send(('HTTP/1.1 400 Bad Request\n\n').encode('utf-8','ignore'))
					conn.close()

	except KeyboardInterrupt: 
		print("End of Process.\n")
		s.close();
		sys.exit(0)


