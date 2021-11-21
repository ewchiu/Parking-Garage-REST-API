from google.cloud import datastore
from flask import Flask, jsonify, request, redirect, session, url_for
from uuid import uuid4
from google.oauth2 import id_token
from google.auth.transport import requests
import google_auth_oauthlib.flow
import os

import user
import car
import spot

# REST API by Eric Chiu
# Simulates a parking garage with cars that park in spots

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = str(uuid4)
app.register_blueprint(user.bp)
app.register_blueprint(car.bp)
app.register_blueprint(spot.bp)

client = datastore.Client()

SCOPES = [
	'https://www.googleapis.com/auth/userinfo.profile', 
	'https://www.googleapis.com/auth/userinfo.email',
	'openid'
]
API_SERVICE_NAME = 'userinfo'
API_VERSION = 'v2'

@app.route('/')
def index():
	return f'<h1>Welcome to the Parking Spot</h1> <p>Get your JWT <a href="/authorize">here</a> so we can find a spot for your car!</p>'

@app.route('/authorize')
def authorize():
	# Create flow instance to manage the OAuth 2.0 Authorization Grant Flow steps.
	flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
		CLIENT_SECRETS_FILE, scopes=SCOPES)

	flow.redirect_uri = url_for('oauth2callback', _external=True)

	authorization_url, state = flow.authorization_url(
		# Enable offline access so that you can refresh an access token without
		# re-prompting the user for permission. Recommended for web server apps.
		access_type='offline'
		)

	# Store the state so the callback can verify the auth server response.
	session['state'] = state

	return redirect(authorization_url)

@app.route('/oauth2callback')
def oauth2callback():
	# Specify the state when creating the flow in the callback so that it can
	# verified in the authorization server response.
	state = session['state']

	flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
		CLIENT_SECRETS_FILE, scopes=SCOPES, state=state)
	flow.redirect_uri = url_for('oauth2callback', _external=True)

	# Use the authorization server's response to fetch the OAuth 2.0 tokens
	token = flow.fetch_token(authorization_response=request.url)

	# Store credentials in the session.
	credentials = flow.credentials
	session['credentials'] = credentials_to_dict(credentials)
	
	req = requests.Request()
	id = id_token.verify_oauth2_token(token['id_token'], req, session['credentials']['client_id'])

	# Create the new user in datastore
	# if the user didn't already exist
	query = client.query(kind="users")
	query.add_filter("sub", "=", id['sub'])
	result = list(query.fetch())

	if len(result) == 0:
		new_user = datastore.Entity(key=client.key('users'))
		new_user.update({'name': id['name'], 'email': id['email'], 'sub': id['sub']})
		client.put(new_user)

		return f""" <h1>Thanks for logging in!</h1> 
					<p>A new user account has been created and your user info is shown below.</p>
					<p>Name: {id['name']}</p>
					<p>Email: {id['email']}</p>
					<p>Your JWT is: {token['id_token']}</p> 
					<p>Please include the JWT in the Authorization header for your requests.</p>
					""", 201

	else:
		return f""" <h1>Welcome back!</h1> 
					<p>Your user account already exists and your user info is shown below.</p>
					<p>Name: {id['name']}</p>
					<p>Email: {id['email']}</p>
					<p>Your JWT is: {token['id_token']}</p> 
					<p>Please include the JWT in the Authorization header for your requests.</p>
					""", 200

def credentials_to_dict(credentials):
	return {'token': credentials.token,
			'refresh_token': credentials.refresh_token,
			'token_uri': credentials.token_uri,
			'client_id': credentials.client_id,
			'client_secret': credentials.client_secret,
			'scopes': credentials.scopes
			}
			
			
if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080, debug=True)
