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
		query = client.query(kind="cars")
		results = list(query.fetch())

		for car in results:
			car['id'] = car.key.id
			car['self'] = f'{request.url}/{car.key.id}'

		return jsonify(results), 200

	else:
		return 'Method not recognized'

@bp.route('/<car_id>', methods=['GET'])
def cars_read_update_delete(car_id):

	if request.method == 'GET':
		sub = verify()
		car_key = client.key('cars', int(car_id))
		car = client.get(key=car_key)

		if not car:
			error = {"Error": "No car with this car_id exists"}
			return jsonify(error), 404
		elif sub is False:
			return jsonify({'Error': 'JWT could not be verified'}), 401
		elif sub is None:
			return jsonify({'Error': 'No JWT was provided'}), 401
		elif sub != car['owner']:
			return jsonify({'Error': 'You do not have access to this car.'}), 403

		car['id'] = car.key.id
		car['self'] = f'{request.url}/{car.key.id}'
		return jsonify(car), 200