from flask import Blueprint, request, jsonify, Response, session
from google.cloud import datastore
from google.auth.transport import requests
from google.oauth2 import id_token

client = datastore.Client()
bp = Blueprint('car', __name__, url_prefix='/cars')

@bp.route("", methods=['POST','GET'])
def cars_get_post():

    # create new car
	if request.method == "POST":
		content = request.get_json()
		jwt = request.headers.get('Authorization')

		if jwt:
			req = requests.Request()
			jwt = jwt.split(" ")[1]

			try:
				sub = id_token.verify_oauth2_token(jwt, req, session['credentials']['client_id'])
				sub = sub['sub']
			except:
				return 'The provided JWT could not be verified', 401

		else:
			return 'Please specify the JWT', 401

		if 'name' not in content or 'type' not in content or 'length' not in content or 'public' not in content or len(content) != 4:
			error = {"Error": "The request object is missing at least one of the required attributes"}
			return jsonify(error), 400

        # create new boat in Datastore
		new_boats = datastore.entity.Entity(key=client.key("boats"))
		new_boats.update({"name": content["name"], "type": content["type"], 
			"length": content["length"], "public": content["public"], "owner": sub})
		client.put(new_boats)

        # formats response object
		added_boat = {"id": new_boats.key.id, "name": content["name"], "type": content["type"],
			"length": content["length"], "public": content["public"], "owner": sub}

		return jsonify(added_boat), 201

    # get list of boats
	elif request.method == 'GET':
		display_public = False
		jwt = request.headers.get('Authorization')

		if jwt:
			req = reqs.Request()
			jwt = jwt.split(" ")[1]

			try:
				sub = id_token.verify_oauth2_token(jwt, req, session['credentials']['client_id'])
				sub = sub['sub']
			except Exception as e:
				display_public = True
				print(f'Error in auth {e}')
		
		else:
			display_public = True

		query = client.query(kind="boats")
		
		if display_public:
			query.add_filter("public", "=", True)
		else:
			query.add_filter("owner", "=", sub)

		results = list(query.fetch())

		for e in results:
			e["id"] = e.key.id

		return jsonify(results), 200

	else:
		return 'Method not recognized'