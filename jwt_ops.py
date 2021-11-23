from google.auth.transport import requests
from flask import session, request
from google.oauth2 import id_token
from json import load

file = open('client_secret.json')
client_secret = load(file)

def verify():
	req = requests.Request()
	jwt = request.headers.get('Authorization')

	if jwt:
		req = requests.Request()
		jwt = jwt.split(" ")[1]

		try:
			sub = id_token.verify_oauth2_token(jwt, req, client_secret['web']['client_id'])
			sub = sub['sub']
			
		except Exception as e: 
			return False

		return sub

	else:
		return None
	
	