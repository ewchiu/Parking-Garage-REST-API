from flask import Blueprint, request, jsonify
from google.cloud import datastore
from jwt_ops import verify

client = datastore.Client()
bp = Blueprint('user', __name__, url_prefix='/users')

# get all users
@bp.route('', methods=['GET'])
def get_users():
	if request.method == 'GET':
		query = client.query(kind='users')
		results = list(query.fetch())

		for user in results:
			user['id'] = user.key.id
			user['self'] = f'{request.url}/{user.key.id}'

		return jsonify(results), 200

	else:
		return 'Method not recognized'

# get user by id
@bp.route('/<user_id>', methods=['GET'])
def get_user_by_id(user_id):

	if request.method == 'GET':
		sub = verify()
		user_key = client.key('users', int(user_id))
		user = client.get(key=user_key)

		if sub is False:
			return jsonify({'Error': 'JWT could not be verified'}), 401
		elif sub is None:
			return jsonify({'Error': 'No JWT was provided'}), 401
		elif sub != user['sub']:
			return jsonify({'Error': 'You do not have access to this user info.'}), 401

		if not user:
			error = {"Error": "No user with this user_id exists"}
			return jsonify(error), 404

		user['id'] = user.key.id
		user['self'] = f'{request.url}/{user.key.id}'
		return jsonify(user), 200

