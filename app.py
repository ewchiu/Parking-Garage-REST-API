from google.cloud import datastore
from flask import Flask, jsonify, request, redirect, session, url_for
from uuid import uuid4
from google.oauth2 import id_token
from google.auth.transport import requests
import google_auth_oauthlib.flow
import os

# REST API by Eric Chiu
# Simulates a parking garage with cars that park in spots

# This variable specifies the name of a file that contains the OAuth 2.0
# information for this application, including its client_id and client_secret.
CLIENT_SECRETS_FILE = "client_secret.json"

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app = Flask(__name__)
app.secret_key = str(uuid4)
# app.register_blueprint(boat.bp)
# app.register_blueprint(load.bp)

client = datastore.Client()

SCOPES = [
	'https://www.googleapis.com/auth/userinfo.profile', 
	'openid'
]
API_SERVICE_NAME = 'userinfo'
API_VERSION = 'v2'

@app.route('/')
def index():
    return f'<h1>Welcome</h1> <p>Get your JWT <a href="/authorize">here</a></p>'

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

	return f"<h1>User info</h1> <p>your JWT is: {token['id_token']}</p> <p>decoded JWT: {id}</p>"

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
