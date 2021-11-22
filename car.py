from flask import Blueprint, request, jsonify, Response, session
from google.cloud import datastore
from google.auth.transport import requests
from google.oauth2 import id_token
from jwt_ops import verify

client = datastore.Client()
bp = Blueprint('car', __name__, url_prefix='/cars')

@bp.route('', methods=['POST','GET'])
def cars_get_post():

    # create new car
	if request.method == "POST":
		content = request.get_json()
		sub = verify()

		if sub is False:
			return jsonify({'Error': 'JWT could not be verified'}), 401
		elif sub is None:
			return jsonify({'Error': 'No JWT was provided'}), 401

		if 'make' not in content or 'plate' not in content or len(content) != 2:
			error = {"Error": "The request object is missing at least one of the required attributes"}
			return jsonify(error), 400

		new_car = {
			'make': content['make'], 
			'plate': content['plate'], 
			'owner': sub
			}

		new_car = datastore.Entity(key=client.key("cars"))
		new_car.update({'make': content['make'], 'plate': content['plate'], 'owner': sub})
		client.put(new_car)

        # formats/sends response object
		new_car['id'] = new_car.key.id
		new_car['self'] = f'{request.url}/{new_car.key.id}'
		return jsonify(new_car), 201

    # get list of all cars
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