from flask import Blueprint, request, jsonify, Response, session
from google.cloud import datastore
from jwt_ops import verify

client = datastore.Client()
bp = Blueprint('car', __name__, url_prefix='/cars')

@bp.route('', methods=['POST','GET'])
def cars_get_post():
	if request.content_type != 'application/json':
		error = {"Error": "This MIME type is not supported by the endpoint"}
		return jsonify(error), 406

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

		if request.content_type != 'application/json':
			error = {"Error": "This MIME type is not supported by the endpoint"}
			return jsonify(error), 406

		for car in results:
			car['id'] = car.key.id
			car['self'] = f'{request.url}/{car.key.id}'

		return jsonify(results), 200

	else:
		return 'Method not recognized'

@bp.route('/<car_id>', methods=['GET'])
def cars_read_update_delete(car_id):
	content = request.get_json()
	car_attributes = ['make', 'plate']

	sub = verify()
	car_key = client.key('cars', int(car_id))
	car = client.get(key=car_key)

	if request.content_type != 'application/json':
		error = {"Error": "This MIME type is not supported by the endpoint"}
		return jsonify(error), 406
	elif not car:
		error = {"Error": "No car with this car_id exists"}
		return jsonify(error), 404
	elif sub is False:
		return jsonify({'Error': 'JWT could not be verified'}), 401
	elif sub is None:
		return jsonify({'Error': 'No JWT was provided'}), 401
	elif sub != car['owner']:
		return jsonify({'Error': 'You do not have access to this car.'}), 403

	if request.method == 'GET':
		car['id'] = car.key.id
		car['self'] = f'{request.url}/{car.key.id}'
		return jsonify(car), 200

	# edit one or more attributes of a car
	elif request.method == 'PATCH':

		for key in content:
			if key not in car_attributes:
				error = {"Error": "You can only edit attributes make and plate"}
				return jsonify(error), 400

		car.update({'make': content['make'], 'plate': content['plate']})
		client.put(car)

		car['id'] = car.key.id
		car['self'] = f'{request.url}/{car.key.id}'
		return jsonify(car), 201

	# edit all attributes of a car
	elif request.method == 'PUT':
		
		if len(content) != 2 or not content['make'] or not content['plate']:  
			error = {"Error": "The request object is missing at least one of the required attributes"}
			return jsonify(error), 400

		for key in content:
			if key not in car_attributes:
				error = {"Error": "You can only edit attributes make and plate"}
				return jsonify(error), 400

		car.update({'make': content['make'], 'plate': content['plate']})
		client.put(car)

		car['id'] = car.key.id
		car['self'] = f'{request.url}/{car.key.id}'
		return jsonify(car), 201

	elif request.method == 'DELETE':

		# checks if the car is currently parked in a space
		query = client.query(kind="spaces")
		results = list(query.fetch())
		parked_spot = None

		for space in results:
			if space['car'] == car['id']:
				parked_spot = space

		if parked_spot:
			parked_spot['car'] = None
			client.put(parked_spot)

		client.delete(car_key)
		return Response(status=204)

	else:
		return 'Method not recognized'