from flask import Blueprint, request, jsonify, make_response
from google.cloud import datastore
from jwt_ops import verify

client = datastore.Client()
bp = Blueprint('user', __name__, url_prefix='/users')

# get all users
@bp.route('', methods=['GET'])
def get_users():
	if request.method == 'GET':

		if 'application/json' not in request.accept_mimetypes:
			error = {"Error": "Not Acceptable"}
			return jsonify(error), 406
			
		query = client.query(kind='users')
		results = list(query.fetch())

		for user in results:
			user['id'] = user.key.id
			user['self'] = f'{request.url}/{user.key.id}'

		return jsonify(results), 200

	else:
		res = make_response({"Error": "Method not recognized"})
		res.headers.set('Allow', ['GET'])
		res.status_code = 405
		return res

# get user by id
@bp.route('/<user_id>', methods=['GET'])
def get_user_by_id(user_id):

	if request.method == 'GET':
		sub = verify()
		user_key = client.key('users', int(user_id))
		user = client.get(key=user_key)

		if 'application/json' not in request.accept_mimetypes:
			error = {"Error": "Not Acceptable"}
			return jsonify(error), 406
		elif sub is False:
			return jsonify({'Error': 'JWT could not be verified'}), 401
		elif sub is None:
			return jsonify({'Error': 'No JWT was provided'}), 401
		elif sub != user['sub']:
			return jsonify({'Error': 'You do not have access to this user info.'}), 403

		if not user:
			error = {"Error": "No user with this user_id exists"}
			return jsonify(error), 404

		user['id'] = user.key.id
		user['self'] = f'{request.url}/{user.key.id}'
		return jsonify(user), 200

	else:
		res = make_response({"Error": "Method not recognized"})
		res.headers.set('Allow', ['GET'])
		res.status_code = 405
		return res

