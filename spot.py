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