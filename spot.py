from flask import Blueprint, request, jsonify, Response
from google.cloud import datastore
from jwt_ops import verify

client = datastore.Client()
bp = Blueprint('space', __name__, url_prefix='/spaces')

@bp.route('', methods=['POST','GET'])
def cars_get_post():
	if request.content_type != 'application/json':
		error = {"Error": "This MIME type is not supported by the endpoint"}
		return jsonify(error), 406

	# create new parking spot
	if request.method == "POST":
		content = request.get_json()

		if 'space_id' not in content or 'floor' not in content or 'car' not in content or len(content) != 3:
			error = {"Error": "The request object is missing at least one of the required attributes"}
			return jsonify(error), 400

		new_space = {
			'space_id': content['space_id'],
			'floor': content['floor'],
			'car': content['car']
			}

		new_space = datastore.Entity(key=client.key("spaces"))
		new_space.update({
			'space_id': content['space_id'],
			'floor': content['floor'],
			'car': content['car']
			})
		client.put(new_space)

		# formats/sends response object
		new_space['id'] = new_space.key.id
		new_space['self'] = f'{request.url}/{new_space.key.id}'
		return jsonify(new_space), 201

	# get list of all parking spaces
	elif request.method == 'GET':
		query = client.query(kind="spaces")
		results = list(query.fetch())

		for space in results:
			space['id'] = space.key.id
			space['self'] = f'{request.url}/{space.key.id}'

		return jsonify(results), 200

	else:
		return 'Method not recognized'

@bp.route('/<id>', methods=['GET'])
def cars_read_update_delete(id):
	content = request.get_json()
	space_attributes = ['space_id', 'floor', 'car']

	space_key = client.key('spaces', int(id))
	space = client.get(key=space_key)

	if request.content_type != 'application/json':
		error = {"Error": "This MIME type is not supported by the endpoint"}
		return jsonify(error), 406
	elif not space:
		error = {"Error": "No car with this car_id exists"}
		return jsonify(error), 404

	if request.method == 'GET':
		space['id'] = space.key.id
		space['self'] = f'{request.url}/{space.key.id}'
		return jsonify(space), 200

	# edit one or more attributes of a car
	elif request.method == 'PATCH':

		for key in content:
			if key not in space_attributes:
				error = {"Error": "You can only edit attributes make and plate"}
				return jsonify(error), 400

		space.update({'make': content['make'], 'plate': content['plate']})
		client.put(space)

		space['id'] = space.key.id
		space['self'] = f'{request.url}/{space.key.id}'
		return jsonify(space), 201

	# edit all attributes of a car
	elif request.method == 'PUT':
		
		if len(content) != 2 or not content['make'] or not content['plate']:  
			error = {"Error": "The request object is missing at least one of the required attributes"}
			return jsonify(error), 400

		for key in content:
			if key not in space_attributes:
				error = {"Error": "You can only edit attributes make and plate"}
				return jsonify(error), 400

		space.update({'make': content['make'], 'plate': content['plate']})
		client.put(space)

		space['id'] = space.key.id
		space['self'] = f'{request.url}/{space.key.id}'
		return jsonify(space), 201

	elif request.method == 'DELETE':
		client.delete(space_key)
		return Response(status=204)

	else:
		return 'Method not recognized'