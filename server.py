# --------------------------------------------------------------------
# NAME		        : Kajal Tomar
# STUDENT NUMBER	: 7793306
# COURSE		    : COMP 3010
# INSTRUCTOR	    : Robert Guderian
# ASSIGNMENT	    : Assignment 2
#
# REMARKS: 	This file implements the webserver for 3010-eeter 
# --------------------------------------------------------------------
import socket
import threading
import sys
import os
import uuid
import json
import tempfile
import sqlite3 
import traceback

HOST = ''
PORT = 8888

status200 = 'HTTP/1.1 200 OK\n'
status400 = 'HTTP/1.1 400 Bad Request\n'
status403 = 'HTTP/1.1 403 Forbidden: Access Denied\n'
status404 = 'HTTP/1.1 404 Not Found\n'
status500 = 'HTTP/1.1 500 Internal Error\n'

# Connect to the database
try:
	dbConn = sqlite3.connect('3010eeter.db')
	cur = dbConn.cursor()
except Exception as e:
	print('> Could not connect to the db')
	print(e)
	traceback.print_exc()

# --------------------------------------------------------
# getRequestedFile(path)
#
# Purpose: Sharing files from filesystem, including images, works. Appropriate HTTP codes used (404 or 200).
# Parameter: the path of the file
# Returns: the response
# --------------------------------------------------------
def getRequestedFile(thePath):
	global status200
	global status404
	fileName = ''
	contentType=''
	response = ''
	print('> Getting the requested file: '+thePath)
	
	if(thePath == '/index.html' or thePath == '/'):
		fileName  = './webFiles/index.html' # return  the index file by default
		contentType = 'Content-Type: text/html\n'		
	elif(thePath == '/main.js'):
		fileName = './webFiles/main.js' # return the js file
		contentType = 'Content-Type: text/javascript\n' 
	else: 
	 	# for all other file requests, including images
		imageExtensions = ['.jpg', '.jpeg', '.png', '.tiff', '.gif']
		textExtensions = ['.css', '.csv', '.html', '.javascript', '.plain', '.xml']
		
		fileName, fileExtension = os.path.splitext(thePath)
		fileName = './webFiles'+thePath	
		
		# set file extention and content type accordingly			
		if(fileExtension in imageExtensions):
			fileExtension = (fileExtension.split('.'))[1]
			contentType = 'Content-Type: image/'+fileExtension+'\n'
		elif(fileExtension in textExtensions):
			fileExtension = (fileExtension.split('.'))[1]
			contentType = 'Content-Type: text/'+fileExtension+'\n'

	try:
		if(fileName != ''):
			try: 
				# read the contents of the file and set content length
				with open(fileName, 'rb') as myFile:
					print('opening file')
					response = myFile.read()
					fileLength = 'Content-Length:'+str(len(response))
			
					header = status200+contentType+fileLength+'\n\n'
					header = header.encode('utf-8','ignore')
					
					# create the response
					response = header + response
			except Exception as e:
				# if there is an error while opening the file, return 404
				reponse =  (status404).encode('utf-8','ignore')
		else:
			print('> file foes not exist')
			response = (status404).encode('utf-8','ignore')
	except Exception as e:
		response = (status404).encode('utf-8','ignore')

	return response

# --------------------------------------------------------
# resolveGetMethod(message, command)
#
# Purpose: if the user is logged in, get a list of all memos
# Parameter: message contains the cookie, command is the API path
# Returns: the response
# --------------------------------------------------------
def resolveGetMethod(message, command):
	global status200
	global status404
	global status500
	
	response = ''

	if(command.lower() == 'tweet'):
		try:
			# get the cookie
			sessionID = (message.split('sessionID='))[1]
			sessionID = (sessionID.split(';'))[0]
			sessionID = sessionID.strip()

			# get the username associated with the cookie
			# this will confirm the logged in status
			statement = "SELECT username FROM users WHERE signed_in=1 AND cookie='"+sessionID+"'"
			cur.execute(statement)
			dbConn.commit()
			result = cur.fetchall()
				
			if(len(result) == 1):
				# the cookie does exist, so login status is confirmed
				# get all the tweets
				statement = "SELECT * FROM tweets" 
				cur.execute(statement)
				results = cur.fetchall()
			
				if(results):
					# convert to json
					resultJson = json.dumps([{"tweet": result[0], "byUser": result[1], "id": str(result[2])} for result in results])
					header = status200+'Content-Type: application/json\nContent-Length:'+str(len(resultJson))+'\n\n'
					response = header.encode('utf-8','ignore') + resultJson.encode('utf-8','ignore')
			else:
				response = status404.encode('utf-8','ignore')
		except Exception as e:
			response = status500.encode('utf-8','ignore')

	return response

# --------------------------------------------------------
# resolvePostMethod(message, command)
#
# Purpose: log the user into the system or create a new memo
# Parameter: message contains information (username, password, 
# cookie or tweet), command is the API path
# Returns: the response
# --------------------------------------------------------
def resolvePostMethod(message, command):
	global status200
	global status400
	global status404
	global status500
	
	response = ''

	if(command.lower() == 'login'):
		try:
			print('> trying to log in\n')

			# get the body of the message
			message = (message.split('\r\n\r\n'))
			
			if(len(message) >= 2):
				message = message[1]
				messageBody = json.loads(message)
				username = messageBody['username'].strip()
				password = messageBody['password'].strip()
				
				if(username and password):
					# select the user's row to check if they are already logged in (already have a cookie)
					statement = "SELECT * FROM users where username ='"+username+"' AND password='"+password+"'" 
					cur.execute(statement)
					result = cur.fetchall()
					
					if(len(result) > 0):
						if(result[0][2] == 0 and not result[0][3]):
							# the user was not logged in 

							# give a cookie and set status to logged in
							cookie = str(uuid.uuid4())
							statement = "UPDATE users SET cookie='"+cookie+"expires=2147483647', signed_in=1 WHERE username ='"+username+"' AND password='"+password+"'"
							cur.execute(statement)
							dbConn.commit()
							result = cur.rowcount 
						
							if(result >= 1):
								# confirmed that the row was updated with the cookie
								print('> '+username+' is logged in.')
								# set the cookie, return 200
								response = status200+'Set-Cookie: sessionID='+cookie+'expires=2147483647;\n\n'
							else:
								# row did not get updated
								response = status500
						else:
							 # user is already logged in 
							print('> the user is already logged in.')
							response = status200 # not sure that this is the right response
					else:
						# no results for that username, password combo
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
	elif(command.lower() == 'tweet'):
		print('> trying to post a tweet')
		try:
			body = message.split('\r\n\r\n')[1]
			
			# get the cookie 
			sessionID = (message.split('sessionID='))[1]
			sessionID = (sessionID.split(';'))[0]
			sessionID = sessionID.strip()

			if(len(body) > 1 and sessionID):
				# a cookie was given, so get the tweet from the body
				messageBody = json.loads(body)
				tweet = messageBody['tweet'].strip()

				# confirm that this user is exists and is logged in
				statement = "SELECT username FROM users WHERE signed_in=1 AND cookie='"+sessionID+"'"
				cur.execute(statement)
				dbConn.commit()
				result = cur.fetchall()
				
				if(len(result) == 1):
					user = result[0][0]
					
					try:
						# insert the tweet
						statement = "INSERT INTO tweets VALUES('"+tweet+"', '"+user+"', NULL);"
						cur.execute(statement)
						dbConn.commit()
						response = status200
					except Exception as e:
						response = status500
				else:
					#cookie does not exist
					response = status404	
			else:
				#did not get the right info
				response = status400	
		except Exception as e:
			response = status500

	return(response.encode('utf-8','ignore'))

# --------------------------------------------------------
# resolveDeleteMethod(message, command, tweetID)
#
# Purpose: log out the user (delete cookie) or delete tweet
# Parameter: cookie, the api command, tweet id (if applicable)
# Returns: the response
# --------------------------------------------------------
def resolveDeleteMethod(message, command, tweetID):
	global status200
	global status400
	global status404
	global status500
	
	response = ''
	
	if(command.lower() == 'logout'):
		try:
			# get the cookie
			sessionID = message.split('sessionID=')[1]
			sessionID = (sessionID.split(';'))[0]
			sessionID = sessionID.strip()

			# remove the cookie
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
			# get the cookie
			sessionID = message.split('sessionID=')[1]
			sessionID = (sessionID.split(';'))[0]
			sessionID = sessionID.strip()
			
			# confirm that user exists and is logged in
			statement = "SELECT username FROM users WHERE signed_in=1 AND cookie='"+sessionID+"'"
			cur.execute(statement)
			dbConn.commit()
			result = cur.fetchall()
				
			if(len(result) == 1):
				user = result[0][0]
				# user is logged in
				try:
					# delete the tweet
					statement = "DELETE FROM tweets WHERE username='"+user+"' AND tweet_id="+tweetID+";"
					cur.execute(statement)
					dbConn.commit()
					response = status200
				except Exception as e:
					response = status500
			else:
				#cookie does not exist.
				response = status404	
		except Exception as e:
			response = status500

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

# --------------------------------------------------------
# Purpose: open + bind to socket, listen for connections and 
#			messages. Parse the message header to see what type
#			of request it is and call the appropriate methods.
# --------------------------------------------------------
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
	try:
		# try to bind to port 8888
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
			theResponse = ''	
			with conn:
				messageRecvd = conn.recv(1024)				
				
				if(messageRecvd):
					print('\n>>> MESSAGE RECIEVED \n---------\n'+messageRecvd.decode('utf-8','ignore')+'\n---------\n', flush=True)
					messageRecvd = messageRecvd.decode('utf-8', 'ignore')
					message = messageRecvd.split(' ') 
					
					if(len(message) > 1):
						method = message[0] # get type of request
						path = message[1].split('/') # get api method
						
						# call the right method based on request and api
						if(method == 'GET'):
							if(path[1].lower() == 'api'):
								theResponse = resolveGetMethod(messageRecvd, path[2])
							else:
								theResponse = getRequestedFile(message[1])
						elif(method == 'POST' and path[1].lower() == 'api'):
							theResponse = resolvePostMethod(messageRecvd, path[2])
						elif(method == 'DELETE'):
							print(path)
							if(path[2].lower() == 'tweet'):
								theResponse = resolveDeleteMethod(messageRecvd, path[2], path[3])
							elif(path[2].lower() == 'logout'):
								theResponse = resolveDeleteMethod(messageRecvd, path[2], '')
						if(theResponse):
							conn.send(theResponse)
						else:
							conn.send(('HTTP/1.1 500 Internal Server Error\n\n').encode('utf-8','ignore'))
					else:
						conn.send(('HTTP/1.1 400 Bad Request\n\n').encode('utf-8','ignore'))
					conn.close()
	except KeyboardInterrupt: 
		print("End of Process.\n")
		s.close();
		sys.exit(0)


