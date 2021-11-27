from flask import Blueprint, request, jsonify, Response, make_response
from google.cloud import datastore
from jwt_ops import verify

client = datastore.Client()
bp = Blueprint('space', __name__, url_prefix='/spaces')

@bp.route('', methods=['POST','GET'])
def spaces_get_post():
	if 'application/json' not in request.accept_mimetypes:
		error = {"Error": "Not Acceptable"}
		return jsonify(error), 406

	# create new parking spot
	if request.method == "POST":
		content = request.get_json()

		if 'space_id' not in content or 'floor' not in content or 'handicap' not in content or len(content) != 3:
			error = {"Error": "The request object is missing at least one of the required attributes"}
			return jsonify(error), 400

		new_space = datastore.Entity(key=client.key("spaces"))
		new_space.update({
			'space_id': content['space_id'],
			'floor': content['floor'],
			'handicap': content['handicap'],
			'car': None
			})
		client.put(new_space)

		# formats/sends response object
		new_space['id'] = new_space.key.id
		new_space['self'] = f'{request.url}/{new_space.key.id}'
		return jsonify(new_space), 201

	# get list of all parking spaces
	elif request.method == 'GET':
		query = client.query(kind="spaces")
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

		for space in results:
			space['id'] = space.key.id
			space['self'] = f'{request.url}/{space.key.id}'

		output = {'spaces': results}

		if next_url:
			output['next'] = next_url

		return jsonify(output), 200

	else:
		res = make_response({"Error": "Method not recognized"})
		res.headers.set('Allow', ['GET', 'POST'])
		res.status_code = 405
		return res

@bp.route('/<id>', methods=['GET', 'PATCH', 'PUT', 'DELETE'])
def spaces_read_update_delete(id):
	content = request.get_json()
	space_attributes = ['space_id', 'floor', 'handicap', 'car']

	space_key = client.key('spaces', int(id))
	space = client.get(key=space_key)

	if 'application/json' not in request.accept_mimetypes:
		if request.method != 'DELETE':
			error = {"Error": "Not Acceptable"}
			return jsonify(error), 406
	elif not space:
		error = {"Error": "No space with this space_id exists"}
		return jsonify(error), 404

	if request.method == 'GET':
		space['id'] = space.key.id
		space['self'] = f'{request.url}/{space.key.id}'
		return jsonify(space), 200

	# edit one or more attributes of a car
	elif request.method == 'PATCH':

		for key in content:
			if key not in space_attributes:
				error = {"Error": "You can only edit valid attributes of the target entity"}
				return jsonify(error), 400

			space[key] = content[key]

		client.put(space)
		space['id'] = space.key.id
		space['self'] = f'{request.url}/{space.key.id}'
		return jsonify(space), 201

	# edit all attributes of a car
	elif request.method == 'PUT':
		
		if 'space_id' not in content or 'floor' not in content or 'handicap' not in content or 'car' not in content or len(content) != 4:
			error = {"Error": "The request object is missing at least one of the required attributes"}
			return jsonify(error), 400

		for key in content:
			if key not in space_attributes:
				error = {"Error": "You can only edit valid attributes of the target entity"}
				return jsonify(error), 400

			space[key] = content[key]
		
		client.put(space)

		space['id'] = space.key.id
		space['self'] = f'{request.url}/{space.key.id}'
		return jsonify(space), 201

	elif request.method == 'DELETE':
		client.delete(space_key)
		return Response(status=204)

	else:
		res = make_response({"Error": "Method not recognized"})
		res.headers.set('Allow', ['GET', 'PATCH', 'PUT', 'DELETE'])
		res.status_code = 405
		return res

@bp.route('/<space_id>/cars/<car_id>', methods=['PUT'])
def park_and_empty_space(space_id, car_id):

	sub = verify()
	space_key = client.key('spaces', int(space_id))
	space = client.get(key=space_key)

	car_key = client.key('cars', int(car_id))
	car = client.get(key=car_key)

	if 'application/json' not in request.accept_mimetypes:
		if request.method != 'DELETE':
			error = {"Error": "Not Acceptable"}
			return jsonify(error), 406
	elif not space:
		error = {"Error": "No space with this space_id exists"}
		return jsonify(error), 404
	elif not car:
		error = {"Error": "No car with this car_id exists"}
		return jsonify(error), 404
	elif sub is False or sub is None:
		return jsonify({'Error': 'Either no JWT was provided, or the JWT could not be verified'}), 401
	elif sub != car['owner']:
		return jsonify({'Error': 'You do not have access to this car.'}), 403
	
	if request.method == 'PUT':
		if space['car']:
			return jsonify({'Error': 'There is already a car parked here.'}), 403

		space['car'] = car
		client.put(space)
		space['self'] = f'{request.url}/{space.key.id}'
		return jsonify(space), 201
		