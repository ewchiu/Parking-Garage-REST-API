from flask import Blueprint, request, jsonify, Response, session, make_response
from google.cloud import datastore
from jwt_ops import verify

client = datastore.Client()
bp = Blueprint('car', __name__, url_prefix='/cars')

@bp.route('', methods=['POST','GET'])
def cars_get_post():
	if 'application/json' not in request.accept_mimetypes:
		error = {"Error": "Not Acceptable"}
		return jsonify(error), 406

	# create new car
	if request.method == "POST":
		content = request.get_json()
		sub = verify()

		if sub is False or sub is None:
			return jsonify({'Error': 'Either no JWT was provided, or the JWT could not be verified'}), 401

		if 'make' not in content or 'plate' not in content or 'make' not in content or len(content) != 3:
			error = {"Error": "The request object is missing at least one of the required attributes"}
			return jsonify(error), 400

		new_car = datastore.Entity(key=client.key("cars"))
		new_car.update({
			'make': content['make'], 
			'model': content['model'], 
			'plate': content['plate'], 
			'owner': sub,
			'space': None
			})
		client.put(new_car)

		# formats/sends response object
		new_car['id'] = new_car.key.id
		new_car['self'] = f'{request.url}/{new_car.key.id}'
		return jsonify(new_car), 201

	# get list of all cars
	elif request.method == 'GET':
		query = client.query(kind="cars")
		sub = None

		if request.headers.get('Authorization'):
			sub = verify()

			if sub is False:
				return jsonify({'Error': 'Either no JWT was provided, or the JWT could not be verified'}), 401

		if sub:
			query.add_filter('owner', '=', sub)

		limit = int(request.args.get('limit', '5'))
		offset = int(request.args.get('offset', '0'))
		iterator = query.fetch(limit = limit, offset=offset)
		pages = iterator.pages
		results = list(next(pages))

		if iterator.next_page_token:
			next_offset = limit + offset
			next_url = f"{request.base_url}?limit={limit}&offset={next_offset}"
		else:
			next_url = None

		for car in results:
			car['id'] = car.key.id
			car['self'] = f'{request.url}/{car.key.id}'

		output = {'cars': results}

		if next_url:
			output['next'] = next_url

		return jsonify(output), 200

	else:
		res = make_response({"Error": "Method not recognized"})
		res.headers.set('Allow', ['GET', 'POST'])
		res.status_code = 405
		return res

@bp.route('/<car_id>', methods=['GET', 'PATCH', 'PUT', 'DELETE'])
def cars_read_update_delete(car_id):
	content = request.get_json()
	car_attributes = ['make', 'model', 'plate', 'space']

	sub = verify()
	car_key = client.key('cars', int(car_id))
	car = client.get(key=car_key)

	if 'application/json' not in request.accept_mimetypes:
		if request.method != 'DELETE':
			error = error = {"Error": "Not Acceptable"}
			return jsonify(error), 406
	elif not car:
		error = {"Error": "No car with this car_id exists"}
		return jsonify(error), 404
	elif sub is False or sub is None:
		return jsonify({'Error': 'Either no JWT was provided, or the JWT could not be verified'}), 401
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
				error = {"Error": "You can only edit valid attributes of the target entity"}
				return jsonify(error), 400

			car[key] = content[key]

		client.put(car)

		car['id'] = car.key.id
		car['self'] = f'{request.url}/{car.key.id}'
		return jsonify(car), 201

	# edit all attributes of a car
	elif request.method == 'PUT':
		
		if len(content) != 4 or not content['make'] or not content['model'] or not content['plate'] or not content['space']:  
			error = {"Error": "The request object is missing at least one of the required attributes"}
			return jsonify(error), 400

		for key in content:
			if key not in car_attributes:
				error = {"Error": "You can only edit valid attributes of the target entity"}
				return jsonify(error), 400

		car.update({
			'make': content['make'], 
			'model': content['model'], 
			'plate': content['plate'], 
			'space': content['space']
			})
		client.put(car)

		car['id'] = car.key.id
		car['self'] = f'{request.url}/{car.key.id}'
		return jsonify(car), 201

	elif request.method == 'DELETE':

		# checks if the car is currently parked in a space
		query = client.query(kind="spaces")
		query.add_filter('car', '=', car.key.id)
		parked_spaces = list(query.fetch())

		for space in parked_spaces:
			space['car'] = None
			client.put(space)

		client.delete(car_key)
		return Response(status=204)

	else:
		res = make_response({"Error": "Method not recognized"})
		res.headers.set('Allow', ['GET', 'PATCH', 'PUT', 'DELETE'])
		res.status_code = 405
		return res